import { useEffect, useState, type FormEvent } from "react"
import {
  apiGetDailyLogsHistory,
  apiGetDailyLogDetails,
  apiUpdateDailyLog,
  type DailyLogRead,
  type ScreensLastHour,
  type NapType,
} from "../api/log"

export default function HistoryPage() {
  const [logs, setLogs] = useState<DailyLogRead[]>([])
  const [selectedLog, setSelectedLog] = useState<DailyLogRead | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadHistory()
  }, [])

  async function loadHistory() {
    setIsLoading(true)
    setError(null)

    try {
      const data = await apiGetDailyLogsHistory(true)
      setLogs(data)
    } catch {
      setError("Nie udało się pobrać historii wpisów.")
    } finally {
      setIsLoading(false)
    }
  }

  async function selectLog(logId: number) {
    setError(null)
    setIsEditing(false)

    try {
      const data = await apiGetDailyLogDetails(logId)
      setSelectedLog(data)
    } catch {
      setError("Nie udało się pobrać szczegółów wpisu.")
    }
  }

  function updateSelected<K extends keyof DailyLogRead>(field: K, value: DailyLogRead[K]) {
    if (!selectedLog) return
    setSelectedLog({
      ...selectedLog,
      [field]: value,
    })
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!selectedLog) return

    setIsSaving(true)
    setError(null)

    try {
      const updated = await apiUpdateDailyLog(selectedLog.id, {
        date: selectedLog.date,

        sleep_start: selectedLog.sleep_start,
        sleep_latency_extra: selectedLog.sleep_latency_extra,
        sleep_end: selectedLog.sleep_end,
        sleep_quality: selectedLog.sleep_quality,
        night_awakenings: selectedLog.night_awakenings,
        morning_energy: selectedLog.morning_energy,

        day_rating: selectedLog.day_rating ?? undefined,
        stress_level: selectedLog.stress_level ?? undefined,
        coffee_last_6h: selectedLog.coffee_last_6h ?? undefined,
        alcohol_last_4h: selectedLog.alcohol_last_4h ?? undefined,
        screens_last_hour: selectedLog.screens_last_hour ?? undefined,
        nap_type: selectedLog.nap_type ?? undefined,
      })

      setSelectedLog(updated)
      setIsEditing(false)
      await loadHistory()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nie udało się zapisać zmian.")
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return <p>Ładowanie historii...</p>
  }

  return (
    <div style={{ padding: 16 }}>
      <h1>Historia wpisów</h1>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      <h2>Lista wpisów</h2>

      {logs.length === 0 ? (
        <p>Brak wpisów.</p>
      ) : (
        <ul>
          {logs.map((log) => (
            <li key={log.id}>
              <button type="button" onClick={() => selectLog(log.id)}>
                {log.date} | sen: {log.sleep_duration ?? "-"} h | wynik dnia: {log.day_score ?? "-"}
              </button>
            </li>
          ))}
        </ul>
      )}

      {selectedLog && (
        <>
          <h2>Podgląd wpisu: {selectedLog.date}</h2>

          {!isEditing && (
            <button type="button" onClick={() => setIsEditing(true)}>
              Edytuj
            </button>
          )}

          <form onSubmit={onSubmit}>
            <fieldset disabled={!isEditing || isSaving}>
              <label>
                Data
                <input
                  type="date"
                  value={selectedLog.date}
                  onChange={(e) => updateSelected("date", e.target.value)}
                />
              </label>

              <br />

              <label>
                Początek snu
                <input
                  type="datetime-local"
                  value={selectedLog.sleep_start?.slice(0, 16) ?? ""}
                  onChange={(e) => updateSelected("sleep_start", e.target.value)}
                />
              </label>

              <br />

              <label>
                Dodatkowy czas zasypiania
                <input
                  type="number"
                  min={0}
                  max={180}
                  value={selectedLog.sleep_latency_extra ?? 0}
                  onChange={(e) => updateSelected("sleep_latency_extra", Number(e.target.value))}
                />
              </label>

              <br />

              <label>
                Koniec snu
                <input
                  type="datetime-local"
                  value={selectedLog.sleep_end?.slice(0, 16) ?? ""}
                  onChange={(e) => updateSelected("sleep_end", e.target.value)}
                />
              </label>

              <br />

              <label>
                Jakość snu
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={selectedLog.sleep_quality ?? 1}
                  onChange={(e) => updateSelected("sleep_quality", Number(e.target.value))}
                />
              </label>

              <br />

              <label>
                Przebudzenia
                <input
                  type="number"
                  min={0}
                  max={10}
                  value={selectedLog.night_awakenings ?? 0}
                  onChange={(e) => updateSelected("night_awakenings", Number(e.target.value))}
                />
              </label>

              <br />

              <label>
                Energia rano
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={selectedLog.morning_energy ?? 1}
                  onChange={(e) => updateSelected("morning_energy", Number(e.target.value))}
                />
              </label>

              <br />

              <label>
                Ocena dnia
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={selectedLog.day_rating ?? 1}
                  onChange={(e) => updateSelected("day_rating", Number(e.target.value))}
                />
              </label>

              <br />

              <label>
                Poziom stresu
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={selectedLog.stress_level ?? 1}
                  onChange={(e) => updateSelected("stress_level", Number(e.target.value))}
                />
              </label>

              <br />

              <label>
                Kawa ostatnie 6h
                <input
                  type="checkbox"
                  checked={selectedLog.coffee_last_6h ?? false}
                  onChange={(e) => updateSelected("coffee_last_6h", e.target.checked)}
                />
              </label>

              <br />

              <label>
                Alkohol ostatnie 4h
                <input
                  type="checkbox"
                  checked={selectedLog.alcohol_last_4h ?? false}
                  onChange={(e) => updateSelected("alcohol_last_4h", e.target.checked)}
                />
              </label>

              <br />

              <label>
                Ekrany ostatnia godzina
                <select
                  value={selectedLog.screens_last_hour ?? "low"}
                  onChange={(e) =>
                    updateSelected("screens_last_hour", e.target.value as ScreensLastHour)
                  }
                >
                  <option value="low">Niski</option>
                  <option value="medium">Średni</option>
                  <option value="high">Wysoki</option>
                </select>
              </label>

              <br />

              <label>
                Drzemka
                <select
                  value={selectedLog.nap_type ?? "none"}
                  onChange={(e) => updateSelected("nap_type", e.target.value as NapType)}
                >
                  <option value="none">Brak</option>
                  <option value="short">Krótka</option>
                  <option value="medium">Średnia</option>
                  <option value="long">Długa</option>
                </select>
              </label>
            </fieldset>

            <p>Czas snu: {selectedLog.sleep_duration ?? "-"} h</p>
            <p>Wynik dnia: {selectedLog.day_score ?? "-"}</p>

            {isEditing && (
              <>
                <button type="submit" disabled={isSaving}>
                  {isSaving ? "Zapisywanie..." : "Zapisz zmiany"}
                </button>

                <button
                  type="button"
                  disabled={isSaving}
                  onClick={() => {
                    setIsEditing(false)
                    selectLog(selectedLog.id)
                  }}
                >
                  Anuluj
                </button>
              </>
            )}
          </form>
        </>
      )}
    </div>
  )
}