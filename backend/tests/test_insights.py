from backend.services.recommendations.compare import compare
from backend.services.recommendations.frame import build_frame
from backend.services.recommendations.insights import build_insights, effect_fact, habits_table


# insights, effect_fact: kierunek zdania ze znaku różnicy i liczby po polsku (przecinek),
# na danych z generatora: u Piotra kawa wydłuża zasypianie, u Anny alkohol obniża jakość snu.
def test_effect_sentence_direction_and_format(healthy_user, coffee_user):
    piotr = build_frame(coffee_user["rows"], coffee_user["typical_latency"], coffee_user["today"])
    anna = build_frame(healthy_user["rows"], healthy_user["typical_latency"], healthy_user["today"])

    coffee = compare(piotr, "coffee", "latency_extra", coffee_user["today"])
    alcohol = compare(anna, "alcohol", "quality", healthy_user["today"])

    assert effect_fact(coffee).text == "Po wieczorach z kawą zasypiasz średnio o 21 min dłużej."
    assert effect_fact(alcohol).text == "Po wieczorach z alkoholem oceniasz jakość snu średnio o 1,1 pkt niżej."


# insights, build_insights na danych Piotra z generatora:
# - pierwsze 5 dni = tryb "start": zalecenia z samych częstości nawyków (kawa w 2 z 4 wieczorów);
# - cała historia: karta drzemki włącza zalecenie o drzemce (drzemek w ostatnich 30 dniach nie było),
#   a „także” na karcie nie powtarza głównego wniosku i zawiera tylko wnioski tego samego nawyku.
def test_build_insights_start_and_personal(coffee_user):
    rows = sorted(coffee_user["rows"], key=lambda row: row["date"])
    first_days = rows[:5]
    start_today = first_days[-1]["date"]
    start = build_insights(build_frame(first_days, coffee_user["typical_latency"], start_today), start_today, 37)
    full = build_insights(build_frame(rows, coffee_user["typical_latency"], coffee_user["today"]), coffee_user["today"], 37)

    assert start.level == "start"
    assert "caffeine_timing" in [g["id"] for g in start.guidelines]

    assert len(full.cards) == 3
    assert "nap_length" in [g["id"] for g in full.guidelines]
    for card in full.cards:
        assert card.fact not in card.also
        assert all(fact.id.startswith(f"effect.{card.factor}.") for fact in card.also)


# insights, habits_table na danych Piotra z generatora:
# - pierwsze 5 dni: wszystkie komórki bez różnicy (za mało nocy), a tabela się nie wywraca;
# - cała historia: znak różnicy zgodny z kierunkiem (kawa wydłuża zasypianie, alkohol obniża jakość).
def test_habits_table_signs_and_too_few_nights(coffee_user):
    rows = sorted(coffee_user["rows"], key=lambda row: row["date"])
    start_today = rows[4]["date"]
    start = habits_table(build_frame(rows[:5], coffee_user["typical_latency"], start_today), start_today)
    full = habits_table(build_frame(rows, coffee_user["typical_latency"], coffee_user["today"]), coffee_user["today"])

    assert all(cell.diff is None for row in start for cell in row.cells)

    cells = {(row.factor, cell.outcome): cell for row in full for cell in row.cells}
    assert cells[("coffee", "latency_extra")].diff == "+21 min"
    assert cells[("alcohol", "quality")].diff == "-1,4 pkt"
