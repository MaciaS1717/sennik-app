from types import SimpleNamespace

from backend.models.user import Gender
from backend.services.recommendations.chat.intents import IntentResult
from backend.services.recommendations.chat.pipeline import answer_chat
from backend.services.recommendations.chat.templates import OFF_TOPIC_ANSWER, UNAVAILABLE_ANSWER
from backend.services.recommendations.frame import build_frame


class FakeLLMClient:
    # Udawany LLM: zwraca z góry ustaloną intencję (albo rzuca wyjątek) i kolejne odpowiedzi z listy.
    def __init__(self, intent, answers=()):
        self.intent = intent
        self.answers = list(answers)
        self.feedbacks = []         # co pipeline przekazał przy kolejnych próbach

    def classify(self, message, history):
        if isinstance(self.intent, Exception):
            raise self.intent
        return self.intent

    def compose(self, question, sheet, feedback=None):
        self.feedbacks.append(feedback)
        return self.answers.pop(0)


# chat.pipeline.answer_chat, ścieżki awaryjne, których prawdziwy LLM nie wywoła na żądanie (dane Piotra):
# - klasyfikator pada -> „asystent niedostępny”; off_topic -> stała odmowa bez redaktora;
# - redaktor zmyśla godzinę, po uwadze walidatora poprawia -> odpowiedź LLM;
# - redaktor zmyśla dwa razy -> odpowiedź z szablonu. Godzina "7:00" bez zera działa w całym przebiegu.
def test_chat_pipeline_fallbacks(coffee_user):
    today = coffee_user["today"]
    frame = build_frame(coffee_user["rows"], coffee_user["typical_latency"], today)
    user = SimpleNamespace(age=37, typical_sleep_latency=coffee_user["typical_latency"], gender=Gender.male)
    ask = lambda llm: answer_chat("O której iść spać, jeśli wstaję o 7?", [], frame, user, today, llm)
    window = IntentResult(intent="sleep_window", mode="bedtime", time="7:00")
    good = "Połóż się o 22:54, a zaśniesz ok. 23:30 i wstaniesz o 7:00 po 7 h 30 min snu."
    bad = "Połóż się o 22:00, to prześpisz 9 h."

    assert ask(FakeLLMClient(TimeoutError())).answer == UNAVAILABLE_ANSWER
    assert ask(FakeLLMClient(IntentResult(intent="off_topic"))).answer == OFF_TOPIC_ANSWER

    corrected = FakeLLMClient(window, [bad, good])
    reply = ask(corrected)
    assert (reply.source, reply.answer) == ("llm", good)
    assert "22:00" in corrected.feedbacks[1]

    assert ask(FakeLLMClient(window, [bad, bad])).source == "template"
