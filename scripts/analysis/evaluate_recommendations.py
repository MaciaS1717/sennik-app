# Ewaluacja modułu rekomendacji na danych z generatora (tabele do rozdziału 8 pracy).
# Uruchomienie z głównego katalogu repozytorium:
#     python -m scripts.analysis.evaluate_recommendations
import json
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from backend.crud.daily_logs import _compute_sleep_duration
from backend.services.recommendations.compare import compare_all, top_findings
from backend.services.recommendations.frame import build_frame
from scripts.synthetic_data.generator import generate_history

PROFILES_DIR = Path(__file__).resolve().parents[1] / "synthetic_data" / "profiles"

# Efekty wpisane w generator (scripts/synthetic_data/generator.py, generate_morning)
# z oczekiwanym kierunkiem: +1 = wynik rośnie, -1 = wynik maleje.
# Uwaga: generator liczy wysoki stres od 8, a aplikacja od 7, więc efekt stresu jest tu rozmyty.
BUILT_IN = {
    # wprost w kodzie generatora
    ("coffee", "latency_extra"): +1,
    ("screens_high", "latency_extra"): +1,
    ("nap_long", "latency_extra"): +1,
    ("stress_high", "latency_extra"): +1,
    ("stress_high", "awakenings"): +1,
    ("stress_high", "quality"): -1,
    ("alcohol", "awakenings"): +1,
    ("alcohol", "quality"): -1,
    ("is_weekend", "duration"): +1,
    ("short_sleep_6h", "energy"): -1,
    ("short_sleep_7h", "energy"): -1,
    # pośrednio: dłuższe zasypianie skraca sen (czas snu = czas w łóżku - zasypianie)
    ("coffee", "duration"): -1,
    ("screens_high", "duration"): -1,
    ("nap_long", "duration"): -1,
    ("stress_high", "duration"): -1,
}


def load_profile(path: Path) -> tuple[list[dict], int, date]:
    # Historia osoby z generatora (bez bazy), z czasem snu liczonym jak w API.
    profile = json.loads(path.read_text(encoding="utf-8"))
    latency = profile["account"]["typical_sleep_latency"]
    user = SimpleNamespace(typical_sleep_latency=latency)
    rows = generate_history(profile)
    for row in rows:
        row["sleep_duration"] = _compute_sleep_duration(user, SimpleNamespace(**row))
    today = date.fromisoformat(profile["generation"]["date_to"])
    return rows, latency, today


def is_true_finding(comparison) -> bool:
    # Wniosek zgodny z generatorem: para jest w BUILT_IN i różnica ma oczekiwany znak.
    direction = BUILT_IN.get((comparison.factor, comparison.outcome))
    return comparison.result == "wniosek" and direction is not None and comparison.diff * direction > 0


def _cell(comparison) -> str:
    # Komórka tabeli 1: różnica przy wniosku (z „!” przy złym kierunku), w przeciwnym razie powód.
    if comparison.result == "wniosek":
        mark = "" if is_true_finding(comparison) else " !"
        return f"{comparison.diff:+.1f}{mark}"
    return "za mało" if comparison.result == "za_malo_danych" else "–"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")   # polskie znaki i strzałki także w konsoli Windows

    results = {}   # osoba -> {(czynnik, wynik): Comparison}
    cards = {}     # osoba -> lista kart (top_findings)
    for path in sorted(PROFILES_DIR.glob("*.json")):
        rows, latency, today = load_profile(path)
        frame = build_frame(rows, latency, today)
        comparisons = compare_all(frame, today)
        results[path.stem] = {(c.factor, c.outcome): c for c in comparisons}
        cards[path.stem] = top_findings(comparisons)
    people = list(results)

    print("## Tabela 1. Czy system odnajduje efekty wpisane w generator\n")
    print("Różnica przy wyniku `wniosek` („!” = zły kierunek); „–” = brak wniosku; „za mało” = < 5 nocy w grupie.\n")
    print("| Czynnik → wynik | " + " | ".join(people) + " |")
    print("|---" * (len(people) + 1) + "|")
    found = 0
    for pair in BUILT_IN:
        print(f"| {pair[0]} → {pair[1]} | " + " | ".join(_cell(results[p][pair]) for p in people) + " |")
        found += sum(is_true_finding(results[p][pair]) for p in people)
    print(f"\nOdnalezione: {found} z {len(BUILT_IN) * len(people)} par (osoba × efekt).\n")

    print("## Tabela 2. Pozostałe wnioski (fałszywe alarmy, efekty łańcuchowe, nawyki występujące razem)\n")
    print("| Osoba | Czynnik → wynik | Okno | Różnica | 95% przedział | Na karcie |")
    print("|---|---|---|---|---|---|")
    other = total = 0
    for person in people:
        for pair, c in results[person].items():
            if c.result != "wniosek":
                continue
            total += 1
            if is_true_finding(c):
                continue
            other += 1
            on_card = "tak" if c in cards[person] else ""
            print(f"| {person} | {pair[0]} → {pair[1]} | {c.window} | {c.diff:+.2f} "
                  f"| [{c.ci_low:.2f}; {c.ci_high:.2f}] | {on_card} |")
    print(f"\nPozostałe wnioski: {other} z {total} wszystkich wniosków.\n")

    all_cards = [c for person in people for c in cards[person]]
    true_cards = sum(is_true_finding(c) for c in all_cards)
    print(f"Karty (to, co widzi użytkownik): {true_cards} z {len(all_cards)} zgodnych z generatorem.")


if __name__ == "__main__":
    main()
