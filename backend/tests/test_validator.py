from types import SimpleNamespace

from backend.models.user import Gender
from backend.services.recommendations.chat.handlers import build_fact_sheet
from backend.services.recommendations.chat.intents import IntentResult
from backend.services.recommendations.chat.validator import validate_answer
from backend.services.recommendations.frame import build_frame


# chat.validator, warstwa 4 ochrony (kalkulator snu Piotra, pobudka o 7:00):
# - przechodzą liczby z faktów, także zapisane inaczej („7:00” zamiast „07:00”, liczby z przecinkiem);
# - odpadają zmyślona godzina, zmyślona liczba z przecinkiem i wynik równania spoza tematu.
def test_validator_accepts_fact_numbers_and_rejects_invented(coffee_user):
    today = coffee_user["today"]
    frame = build_frame(coffee_user["rows"], coffee_user["typical_latency"], today)
    user = SimpleNamespace(age=37, typical_sleep_latency=coffee_user["typical_latency"], gender=Gender.male)
    sheet = build_fact_sheet(frame, user, IntentResult(intent="sleep_window", mode="bedtime", time="7:00"), today)

    good = ("Jeśli wstajesz o 7:00, połóż się o 22:54: zaśniesz ok. 23:30 i prześpisz 7 h 30 min. "
            "Po 6 h snu masz rano średnio 5,2 pkt energii.")
    assert validate_answer(good, sheet).ok

    invented = validate_answer("Połóż się o 22:30, a energii będziesz mieć 5,7 pkt. A 2x+5=11, więc x = 3.", sheet)
    assert invented.problems == ["Liczby spoza faktów: 11, 22:30, 3, 5, 5,7."]
