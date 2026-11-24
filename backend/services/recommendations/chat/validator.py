import re
from dataclasses import dataclass

from .intents import FactSheet

MAX_ANSWER_CHARS = 1200
TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")      # godzina: "7:00", "23:30"
NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")          # liczba: "21", "1,4", "1.4"


def _numbers(text: str) -> set:
    # Godziny i liczby z tekstu w jednej, porównywalnej postaci:
    # "7:00" -> "07:00", a "1,4" i "1.4" -> 1.4 (najpierw godziny, żeby "23:30" nie dało 23 i 30).
    found = {f"{int(hours):02d}:{minutes}" for hours, minutes in TIME_RE.findall(text)}
    rest = TIME_RE.sub(" ", text)
    found |= {float(number.replace(",", ".")) for number in NUMBER_RE.findall(rest)}
    return found


def _show(value) -> str:
    # Do komunikatu dla LLM: 3.0 -> "3", 5.7 -> "5,7", "22:30" bez zmian.
    return value if isinstance(value, str) else f"{value:g}".replace(".", ",")


def allowed_numbers(sheet: FactSheet) -> set:
    # Liczby, których wolno użyć: ze zdań i napisów faktów, z uwag, z zaleceń (z tytułami i źródłami)
    # oraz liczba nocy. Zdania faktów, bo nazwy czynników zawierają liczby („kawa w ciągu 6 h”).
    texts = [fact.text for fact in sheet.facts] + sheet.notes
    texts += [value for fact in sheet.facts for value in fact.values.values()]
    for guideline in sheet.guidelines:
        texts += [guideline["title"], guideline["text"], *guideline["sources"]]
    allowed = {float(sheet.nights)}
    for text in texts:
        allowed |= _numbers(text)
    return allowed


@dataclass
class ValidationResult:
    ok: bool
    problems: list[str]         # opisy błędów; trafiają do LLM przy ponownej próbie


def validate_answer(answer: str, sheet: FactSheet) -> ValidationResult:
    # Warstwa 4 ochrony: odpowiedź LLM może zawierać tylko liczby z FactSheet, bez kodu, w limicie długości.
    problems = []
    if not answer.strip():
        problems.append("Odpowiedź jest pusta.")
    if len(answer) > MAX_ANSWER_CHARS:
        problems.append(f"Odpowiedź ma {len(answer)} znaków, a limit to {MAX_ANSWER_CHARS}.")
    if "```" in answer:
        problems.append("Odpowiedź zawiera blok kodu.")
    unknown = _numbers(answer) - allowed_numbers(sheet)
    if unknown:
        problems.append("Liczby spoza faktów: " + ", ".join(sorted(_show(v) for v in unknown)) + ".")
    return ValidationResult(not problems, problems)
