import { useState, type FormEvent } from "react"
import { apiSubmitEveningLog, type ScreensLastHour, type NapType } from "../api/log"
import "../styles/pages/evening_log.css"

export default function EveningLogPage() {
    const [date, setDate] = useState("")
    const [dayRating, setDayRating] = useState(5)
    const [stressLevel, setStressLevel] = useState(5)
    const [coffeeLast6h, setCoffeeLast6h] = useState(false)
    const [alcoholLast4h, setAlcoholLast4h] = useState(false)
    const [screensLastHour, setScreensLastHour] = useState<"low" | "medium" | "high">("low")
    const [napType, setNapType] = useState<"none" | "short" | "medium" | "long">("none")

    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)

    async function onSubmit(e: FormEvent<HTMLFormElement>) {
        e.preventDefault()
        setError(null)
        setSuccess(null)

        const payload = {
            date,
            day_rating: dayRating,
            stress_level: stressLevel,
            coffee_last_6h: coffeeLast6h,
            alcohol_last_4h: alcoholLast4h,
            screens_last_hour: screensLastHour,
            nap_type: napType,
        }

        setIsSubmitting(true)
        try {
            await apiSubmitEveningLog(payload)
            setSuccess("Wieczorny dziennik został pomyślnie zapisany!")
        } catch (err) {
            setError("Nie udało się zapisać wieczornego dziennika.")
        } finally {
            setIsSubmitting(false)
        }
    }
    return (
        <div className="eveningLogPage">
            <div className="eveningLogCard">
                <h1>Wieczorny dziennik</h1>
                <form onSubmit={onSubmit}>
                    <label className="eveningLogField">
                        Data:
                        <input
                                className="eveningLogControl"
                                type="date"
                                value={date}
                                onChange={(e) => setDate(e.target.value)}
                                required
                            />
                        </label>
                        <label className="eveningLogField">
                            Ocena dnia (1-10):
                            <input
                                className="eveningLogControl"
                                type="number"
                                min={1}
                                max={10}
                                value={dayRating}
                                onChange={(e) => setDayRating(Number(e.target.value))}
                                required
                            />
                        </label>
                        <label className="eveningLogField">
                            Poziom stresu dzisiaj (1-10):
                            <input
                                className="eveningLogControl"
                                type="number"
                                min={1}
                                max={10}
                                value={stressLevel}
                                onChange={(e) => setStressLevel(Number(e.target.value))}
                                required
                            />
                        </label>
                        <label className="eveningLogField">
                            Czy piłeś kawę w ciągu ostatnich 6 godzin?
                            <input
                                className="eveningLogControl"
                                type="checkbox"
                                checked={coffeeLast6h}
                                onChange={(e) => setCoffeeLast6h(e.target.checked)}
                            />
                        </label>
                        <label className="eveningLogField">
                            Czy piłeś alkohol w ciągu ostatnich 4 godzin?
                            <input
                                className="eveningLogControl"
                                type="checkbox"
                                checked={alcoholLast4h}
                                onChange={(e) => setAlcoholLast4h(e.target.checked)}
                            />
                        </label>
                        <label className="eveningLogField">
                            Czas spędzony przed ekranem w ostatniej godzinie:
                            <select
                                className="eveningLogControl"
                                value={screensLastHour}
                                onChange={(e) => setScreensLastHour(e.target.value as ScreensLastHour)}
                                required
                            >
                                <option value="low">Niski</option>
                                <option value="medium">Średni</option>
                                <option value="high">Wysoki</option>
                            </select>
                        </label>
                        <label className="eveningLogField">
                            Drzemka w ciągu dnia:
                            <select
                                className="eveningLogControl"
                                value={napType}
                                onChange={(e) => setNapType(e.target.value as NapType)}
                                required
                            >
                                <option value="none">Brak</option>
                                <option value="short">Krótka</option>
                                <option value="medium">Średnia</option>
                                <option value="long">Długa</option>
                            </select>
                        </label>
                        <button className="eveningLogButton" type="submit" disabled={isSubmitting}>
                            {isSubmitting ? "Zapisuję..." : "Zapisz dziennik"}
                        </button>
                        {error && <div className="eveningLogError">{error}</div>}
                        {success && <div className="eveningLogSuccess">{success}</div>}
                    </form>
                </div>
        </div>
    )
}