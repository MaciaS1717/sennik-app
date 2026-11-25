from .intents import FactSheet

TEMPLATE_FACTS = 5          # najwyżej tyle zdań faktów w odpowiedzi z szablonu
TEMPLATE_GUIDELINES = 1     # i jedno zalecenie
NO_DATA = (
    "Na razie nie mam danych, żeby odpowiedzieć na to pytanie. "
    "Wypełniaj raporty poranne i wieczorne, a wnioski pojawią się z czasem."
)
OFF_TOPIC_ANSWER = (
    "Pomagam tylko w sprawach snu, samopoczucia i Twoich raportów w Senniku. "
    "Możesz zapytać np. „Jak poprawić sen?”, „Jak kawa wpływa na mój sen?” "
    "albo „O której się położyć, jeśli wstaję o 7:00?”."
)
UNAVAILABLE_ANSWER = "Asystent jest chwilowo niedostępny. Skorzystaj z sekcji Wnioski albo z Kalkulatora snu."
DISCLAIMER = (
    "Sennik nie jest narzędziem medycznym. Odpowiedzi opierają się na Twoich raportach "
    "i ogólnych zaleceniach. Nie są diagnozą."
)


def template_answer(sheet: FactSheet) -> str:
    # Odpowiedź bez LLM, z gotowych zdań: gdy walidator dwa razy odrzuci odpowiedź albo LLM przestanie działać.
    if sheet.intent == "general_knowledge":
        # Bez LLM nie wiemy, którego zalecenia dotyczy pytanie, więc wymieniamy tematy.
        titles = ", ".join(g["title"].lower() for g in sheet.guidelines)
        return f"Nie udało się przygotować odpowiedzi. Sprawdzone zalecenia w aplikacji dotyczą tematów: {titles}."
    parts = sheet.notes + [fact.text for fact in sheet.facts[:TEMPLATE_FACTS]]
    parts += [f"{g['title']}: {g['text']}" for g in sheet.guidelines[:TEMPLATE_GUIDELINES]]
    return "\n\n".join(parts) if parts else NO_DATA
