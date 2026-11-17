from dataclasses import dataclass

import pandas as pd

from .compare import MID, MIN_NIGHTS, bootstrap_ci

BIN_MIN = 30                # szerokość przedziału długości snu (min)
MIN_NIGHTS_FOR_DATA = 14    # od tylu pełnych nocy zakres liczymy z danych
MIN_SLEEP = 6 * 60          # nie proponujemy mniej niż 6 h (NSF: 6 h „może być odpowiednie” dla dorosłych)
RECOMMENDED_MIN = 7 * 60    # główne zalecenie dla dorosłych (NSF, AASM): co najmniej 7 h
CYCLE_MIN = 90              # przybliżona długość cyklu snu (źródła: 70-120 min)
CYCLES = range(4, 8)        # 4-7 cykli, czyli 6 h, 7,5 h, 9 h, 10,5 h
LATENCY_NIGHTS = 30         # czas zasypiania z tylu ostatnich nocy
OPTION_WINDOW = 15          # do opcji liczymy noce o długości ±15 min od niej
RATING_ORDER = {"dobra": 0, "za_malo_danych": 1, "slabsza": 2, "brak_oceny": 0}
USUAL_RADIUS = 60           # pora zaśnięcia jest „zwykła”, gdy w promieniu 60 min są co najmniej
USUAL_NIGHTS = 3            # 3 noce z historii


@dataclass
class DurationRange:
    low: int                # minuty snu
    high: int
    source: str             # "dane" albo "zalecenia"
    nights: int             # pełne noce (długość i energia)
    note: str | None = None


@dataclass
class RatedOption:
    duration: int                   # minuty snu
    mean_energy: float | None       # średnia energia rano po podobnie długim śnie
    nights: int                     # z ilu nocy jest ta średnia
    rating: str                     # "dobra", "slabsza", "za_malo_danych" albo "brak_oceny"

@dataclass
class SleepPlan:
    bedtime: str                    # położenie się (HH:MM)
    onset: str                      # zaśnięcie
    wake: str                       # pobudka
    option: RatedOption             # długość snu i jej ocena


@dataclass
class SleepWindow:
    mode: str                       # "wake_time" albo "bedtime"
    duration_range: DurationRange
    latency: int                    # czas zasypiania (min)
    latency_source: str             # "dane" albo "profil"
    plans: list[SleepPlan]
    notes: list[str]                # uwagi dla użytkownika


def recommended_range(age: int) -> tuple[int, int]:
    # Zalecana długość snu według wieku (NSF; do potwierdzenia w weryfikacji źródeł).
    if age < 18:
        return 8 * 60, 10 * 60
    if age >= 65:
        return 7 * 60, 8 * 60
    return 7 * 60, 9 * 60


def duration_bins(frame: pd.DataFrame) -> pd.DataFrame:
    # Średnia energia rano w przedziałach długości snu co 30 min (indeks = początek przedziału).
    nights = frame[frame["duration"].notna() & frame["energy"].notna()]
    bin_start = (nights["duration"] // BIN_MIN * BIN_MIN).astype(int)
    return nights.groupby(bin_start)["energy"].agg(mean_energy="mean", nights="count")


def duration_range(frame: pd.DataFrame, age: int) -> DurationRange:
    # Zakres długości snu, po której użytkownik ma najwięcej energii rano.
    bins = duration_bins(frame)
    nights = int(bins["nights"].sum())
    low, high = recommended_range(age)

    if nights < MIN_NIGHTS_FOR_DATA:
        return DurationRange(low, high, "zalecenia", nights)

    # Tylko przedziały z co najmniej 5 nocami; najlepszy i te gorsze od niego najwyżej o MID.
    bins = bins[bins["nights"] >= MIN_NIGHTS]
    best = bins["mean_energy"].max()
    good = bins[bins["mean_energy"] >= best - MID["energy"]]
    data_low = max(int(good.index.min()), MIN_SLEEP)
    data_high = int(good.index.max()) + BIN_MIN

    if data_high <= data_low:
        note = "Twoje dane pokazują dobrą energię po krótszym śnie, ale nie proponujemy mniej niż 6 h."
        return DurationRange(low, high, "zalecenia", nights, note)

    # Zakres poniżej 7 h jest dopuszczalny, ale użytkownik ma o tym wiedzieć.
    note = None
    if data_low < RECOMMENDED_MIN:
        note = "Zakres schodzi poniżej zalecanych 7 h, bo Twoje dane pokazują dobrą energię po krótszym śnie."
    return DurationRange(data_low, data_high, "dane", nights, note)

def sleep_options(low: int, high: int) -> list[int]:
    # Długości snu (min) z pełnych cykli, które mieszczą się w zakresie [low, high].
    options = [k * CYCLE_MIN for k in CYCLES if low <= k * CYCLE_MIN <= high]
    if not options:
        # Żaden pełny cykl nie pasuje: środek zakresu zaokrąglony do 15 min.
        options = [round((low + high) / 2 / 15) * 15]
    return options


def typical_latency(frame: pd.DataFrame, profile_latency: int) -> tuple[int, str]:
    # Czas zasypiania: mediana z ostatnich nocy; bez nocy wartość z profilu.
    latencies = frame["latency_total"].dropna().tail(LATENCY_NIGHTS)
    if latencies.empty:
        return profile_latency, "profil"
    return int(round(latencies.median())), "dane"


def _energy_near(frame: pd.DataFrame, duration: int) -> pd.Series:
    # Energia rano po nocach, które trwały duration ± 15 min.
    nights = frame[frame["duration"].notna() & frame["energy"].notna()]
    return nights.loc[(nights["duration"] - duration).abs() <= OPTION_WINDOW, "energy"]


def rate_options(frame: pd.DataFrame, options: list[int], source: str) -> list[RatedOption]:
    # Ocena opcji: "slabsza" tylko przy 3 warunkach wniosków (jak w compare), inaczej "dobra".
    if source == "zalecenia":
        return [RatedOption(duration, None, 0, "brak_oceny") for duration in options]

    energies = {duration: _energy_near(frame, duration) for duration in options}
    enough = {d: e for d, e in energies.items() if len(e) >= MIN_NIGHTS}
    # Punkt odniesienia: opcja z najwyższą średnią energią (spośród tych z co najmniej 5 nocami).
    best = max(enough, key=lambda d: enough[d].mean(), default=None)

    rated = []
    for duration, energy in energies.items():
        if len(energy) < MIN_NIGHTS:
            rated.append(RatedOption(duration, None, len(energy), "za_malo_danych"))
            continue
        weaker = False
        if duration != best:
            diff = energy.mean() - enough[best].mean()
            ci_low, ci_high = bootstrap_ci(energy, enough[best])
            weaker = ci_high < 0 and diff <= -MID["energy"]
        rating = "slabsza" if weaker else "dobra"
        rated.append(RatedOption(duration, float(energy.mean()), len(energy), rating))

    # Najpierw dobre, potem bez oceny z braku nocy, na końcu słabsze; w grupie według długości.
    return sorted(rated, key=lambda o: (RATING_ORDER[o.rating], o.duration))

def _to_minutes(hhmm: str) -> int:
    # "23:30" -> 1410 minut od północy.
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _to_hhmm(minutes: int) -> str:
    # Minuty -> "HH:MM"; reszta z dzielenia przez dobę obsługuje północ (1830 -> "06:30", -15 -> "23:45").
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _plan(onset: int, latency: int, option: RatedOption) -> SleepPlan:
    # Godziny jednej opcji liczone od chwili zaśnięcia.
    return SleepPlan(
        bedtime=_to_hhmm(onset - latency),
        onset=_to_hhmm(onset),
        wake=_to_hhmm(onset + option.duration),
        option=option,
    )


def _to_noon_axis(minutes: int) -> int:
    # Minuty od północy -> oś ramki (minuty od 12:00 dnia poprzedniego): 23:00 -> 660, 00:30 -> 750.
    return (minutes - 12 * 60) % (24 * 60)


def _unusual_onset_note(frame: pd.DataFrame, onset: int) -> str | None:
    # Uwaga, gdy użytkownik o tej porze prawie nigdy nie zasypia (mając już co najmniej 14 nocy).
    onsets = frame["onset_min"].dropna()
    if len(onsets) < MIN_NIGHTS_FOR_DATA:
        return None
    nearby = ((onsets - _to_noon_axis(onset)).abs() <= USUAL_RADIUS).sum()
    if nearby < USUAL_NIGHTS:
        return "O tej porze zwykle nie zasypiasz, więc zaśnięcie może potrwać dłużej, niż zakładamy."
    return None


def calculate_sleep_window(
    frame: pd.DataFrame, age: int, profile_latency: int, mode: str, time: str, goes_to_bed: bool = False,
) -> SleepWindow:
    # Kalkulator snu: zakres długości -> opcje z cykli -> ocena opcji -> godziny.
    duration = duration_range(frame, age)
    options = rate_options(frame, sleep_options(duration.low, duration.high), duration.source)
    latency, latency_source = typical_latency(frame, profile_latency)
    notes = [duration.note] if duration.note else []
    given = _to_minutes(time)

    if mode == "wake_time":
        # Znamy porę zaśnięcia (albo położenia się) i szukamy budzika.
        onset = given + latency if goes_to_bed else given
        plans = [_plan(onset, latency, option) for option in options]
        unusual = _unusual_onset_note(frame, onset)
        if unusual:
            notes.append(unusual)
    else:
        # mode == "bedtime": znamy porę pobudki i liczymy wstecz.
        plans = [_plan(given - option.duration, latency, option) for option in options]

    return SleepWindow(mode, duration, latency, latency_source, plans, notes)
