import logging
import time
from dataclasses import dataclass
from datetime import date

import pandas as pd

from ....models import User
from ....schemas.recommendations import ChatTurn
from .handlers import build_fact_sheet
from .intents import FactSheet
from .templates import DISCLAIMER, OFF_TOPIC_ANSWER, UNAVAILABLE_ANSWER, template_answer
from .validator import validate_answer

logger = logging.getLogger(__name__)
COMPOSE_ATTEMPTS = 2        # pierwsza odpowiedź + jedna poprawka po uwagach walidatora


@dataclass
class ChatAnswer:
    # Wynik jednej wiadomości (pola jak w ChatResponse).
    answer: str
    intent: str | None
    level: str | None
    evidence: list[str]
    disclaimer: str
    source: str                 # "llm", "template", "fixed" albo "unavailable"


def _compose_checked(llm, question: str, sheet: FactSheet) -> tuple[str, str]:
    # llm: klient z metodami classify i compose (prawdziwy w aplikacji, FakeLLMClient w testach).
    # Redaktor + walidator: odpowiedź LLM tylko po pozytywnej walidacji, inaczej szablon z faktów.
    feedback = None
    for _ in range(COMPOSE_ATTEMPTS):
        try:
            answer = llm.compose(question, sheet, feedback)
        except Exception:       # LLM przestał działać w trakcie: od razu szablon
            break
        result = validate_answer(answer, sheet)
        if result.ok:
            return answer, "llm"
        feedback = " ".join(result.problems)
    return template_answer(sheet), "template"


def _reply(message: str, history: list[ChatTurn], frame: pd.DataFrame, user: User, today: date, llm) -> ChatAnswer:
    # Klasyfikacja -> stała odmowa albo fakty -> redakcja z walidacją.
    try:
        intent = llm.classify(message, history)
    except Exception:           # timeout, brak klucza, zły JSON: bez klasyfikacji nie zgadujemy
        return ChatAnswer(UNAVAILABLE_ANSWER, None, None, [], DISCLAIMER, "unavailable")
    if intent.intent == "off_topic":
        return ChatAnswer(OFF_TOPIC_ANSWER, "off_topic", None, [], DISCLAIMER, "fixed")
    sheet = build_fact_sheet(frame, user, intent, today)
    answer, source = _compose_checked(llm, message, sheet)
    evidence = [fact.text for fact in sheet.facts]
    return ChatAnswer(answer, sheet.intent, sheet.level, evidence, DISCLAIMER, source)


def answer_chat(message: str, history: list[ChatTurn], frame: pd.DataFrame, user: User, today: date, llm) -> ChatAnswer:
    # Jedyne wejście czatu. Logujemy intencję, źródło i czas, bez treści wiadomości.
    started = time.perf_counter()
    reply = _reply(message, history, frame, user, today, llm)
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("czat: intencja=%s, źródło=%s, czas=%d ms", reply.intent, reply.source, elapsed_ms)
    return reply
