import { useState, type FormEvent } from "react"
import { apiSubmitMorningLog } from "../api/log"
import { useNavigate } from "react-router-dom"
import "../styles/pages/morning_log.css"

export default function MorningLogPage() {
  const navigate = useNavigate()
  const [date, setDate] = useState("")
  const [sleepStart, setSleepStart] = useState("")
  const [sleepLatencyExtra, setSleepLatencyExtra] = useState(0)
  const [sleepEnd, setSleepEnd] = useState("")
  const [sleepQuality, setSleepQuality] = useState<number>(5)
  const [nightAwakenings, setNightAwakenings] = useState(0)
  const [morningEnergy, setMorningEnergy] = useState<number>(5)

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    //walidacja
    const sleepEndDay = sleepEnd.split("T")[0] // "YYYY-MM-DD"
    //do czasu spania
    const startMs = new Date(sleepStart).getTime()
    const endMs = new Date(sleepEnd).getTime()
    const hoursInBed = (endMs - startMs) / 3600000
    
    if(sleepStart > sleepEnd) {
        setError("Godzina rozpoczęcia snu nie może być późniejsza niż godzina zakończenia snu.")
        return
    }
    if (sleepEnd && date !== sleepEndDay) {
        setError("Data wpisu musi być taka sama jak data z godziny zakończenia snu.")
        return
    }
    if (sleepLatencyExtra < 0|| sleepLatencyExtra > 180) {
        setError("Podaj prawidłowy dodatkowy czas zasypiania (0-180 minut).")
        return
    }
    if(nightAwakenings < 0 || nightAwakenings > 10) {
        setError("Podaj prawidłową liczbę przebudzeń w nocy (0-10).")
        return
    }
    if (hoursInBed > 18) {
      setError("Maksymalny czas w łóżku to 18 godzin.")
      return
    }


    const payload = {
      date,
      sleep_start: sleepStart,
      sleep_latency_extra: sleepLatencyExtra,
      sleep_end: sleepEnd,
      sleep_quality: sleepQuality,
      night_awakenings: nightAwakenings,
      morning_energy: morningEnergy,
    }

    setIsSubmitting(true)
    try {
      await apiSubmitMorningLog(payload)
      setSuccess("Poranny dziennik został zapisany pomyślnie.")
      setTimeout(() => navigate("/", { replace: true }), 2000) //po 2 sekundach wracamy do strony głównej
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nie udało się zapisać porannego dziennika.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="morningLogPage">
      <div className="morningLogCard">
        <h1>Poranny Dziennik</h1>
        <form onSubmit={onSubmit}>
          <label className="morningLogField">
            Data
            <input
              className="morningLogControl"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </label>

          <label className="morningLogField">
            Godzina rozpoczęcia snu
            <input
              className="morningLogControl"
              type="datetime-local"
              value={sleepStart}
              onChange={(e) => setSleepStart(e.target.value)}
              required
            />
          </label>

          <label className="morningLogField">
            Dodatkowy czas zasypiania (minuty)
            <input
              className="morningLogControl"
              type="number"
              value={sleepLatencyExtra}
              min={0}
              onChange={(e) => setSleepLatencyExtra(Number(e.target.value))}
              required
            />
          </label>

          <label className="morningLogField">
            Godzina zakończenia snu
            <input
              className="morningLogControl"
              type="datetime-local"
              value={sleepEnd}
              onChange={(e) => setSleepEnd(e.target.value)}
              required
            />
          </label>

          <label className="morningLogField">
            Jakość snu (1-10)
            <select
              className="morningLogControl"
              value={sleepQuality}
              onChange={(e) => setSleepQuality(Number(e.target.value))}
              required
            >
              <option value={1}>1 – bardzo źle</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
              <option value={4}>4</option>
              <option value={5}>5 – ok</option>
              <option value={6}>6</option>
              <option value={7}>7</option>
              <option value={8}>8</option>
              <option value={9}>9</option>
              <option value={10}>10 – świetnie</option>
            </select>
          </label>

          <label className="morningLogField">
            Liczba przebudzeń w nocy
            <input
              className="morningLogControl"
              type="number"
              value={nightAwakenings}
              min={0}
              onChange={(e) => setNightAwakenings(Number(e.target.value))}
              required
            />
          </label>

          <label className="morningLogField">
            Poziom energii rano (1-10)
            <select
              className="morningLogControl"
              value={morningEnergy}
              onChange={(e) => setMorningEnergy(Number(e.target.value))}
              required
            >
              <option value={1}>1 – bardzo nisko</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
              <option value={4}>4</option>
              <option value={5}>5 – średnio</option>
              <option value={6}>6</option>
              <option value={7}>7</option>
              <option value={8}>8</option>
              <option value={9}>9</option>
              <option value={10}>10 – bardzo wysoko</option>
            </select>
          </label>

          <button className="morningLogButton" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Zapisywanie..." : "Zapisz Poranny Dziennik"}
          </button>

          {error && <p className="morningLogError">{error}</p>}
          {success && <p className="morningLogSuccess">{success}</p>}
        </form>
      </div>
    </div>
  )
}
