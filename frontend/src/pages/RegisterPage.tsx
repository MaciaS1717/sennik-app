import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useAuth } from "../auth/AuthContext"
import { register as apiRegister } from "../api/auth"
import "../styles/pages/register.css"

type Gender = "male" | "female"

export default function RegisterPage() {
  const navigate = useNavigate()
  const auth = useAuth()

  const [email, setEmail] = useState("")
  const [name, setName] = useState("")
  const [gender, setGender] = useState<Gender>("male")
  const [age, setAge] = useState("18")
  const [typicalSleepLatency, setTypicalSleepLatency] = useState("15")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  const [isSubmitting, setIsSubmitting] = useState(false) //stan przy wysylaniu formularza
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)

    //usun spacje z poczatku i konca
    const trimmedEmail = email.trim()
    const trimmedName = name.trim()

    if (!trimmedEmail) return setError("Email jest wymagany")
    if (!trimmedName) return setError("Imię jest wymagane")
    if (password.length < 6) return setError("Hasło musi mieć minimum 6 znaków")
    if (password !== confirmPassword) return setError("Hasła nie są takie same")

    const ageNumber = Number(age)
    if (!Number.isFinite(ageNumber) || ageNumber < 0) return setError("Wiek musi być liczbą ≥ 0")

    const latencyNumber = Number(typicalSleepLatency)
    if (!Number.isFinite(latencyNumber) || latencyNumber < 0)
      return setError("Czas zasypiania musi być liczbą ≥ 0")

    const payload = {
      email: trimmedEmail,
      password,
      name: trimmedName,
      gender,
      age: ageNumber,
      typical_sleep_latency: latencyNumber,
    }

    setIsSubmitting(true) //blokuj przycisk w trakcie wysylania
    try {
      await apiRegister(payload)
      await auth.login(trimmedEmail, password) //automatyczne logowanie po rejestracji
      navigate("/", { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nie udało się zarejestrować")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="registerPage">
      <div className="registerCard">
        <h1>Rejestracja</h1>

        <form onSubmit={onSubmit}>
          <label className="registerField">
            Email
            <input className="registerControl"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              autoComplete="email"
            />
          </label>

          <label className="registerField">
            Imię
            <input className="registerControl"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
            />
          </label>

          <label className="registerField">
            Płeć
            <select className="registerControl"
              value={gender}
              onChange={(e) => setGender(e.target.value as Gender)}
            >
              <option value="male">Mężczyzna</option>
              <option value="female">Kobieta</option>
            </select>
          </label>

          <label className="registerField">
            Wiek
            <input className="registerControl"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              type="number"
              min={0}
              inputMode="numeric"
            />
          </label>

          <label className="registerField">
            Typowy czas zasypiania (min)
            <input className="registerControl"
              value={typicalSleepLatency}
              onChange={(e) => setTypicalSleepLatency(e.target.value)}
              type="number"
              min={0}
              inputMode="numeric"
            />
          </label>

          <label className="registerField">
            Hasło
            <input className="registerControl"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              autoComplete="new-password"
            />
          </label>

          <label className="registerField">
            Powtórz hasło
            <input className="registerControl"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              type="password"
              autoComplete="new-password"
            />
          </label>

          <button className="registerButton" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Tworzenie konta..." : "Utwórz konto"}
          </button>

          {error && <p className="registerError">{error}</p>}
        </form>

        <p>
          Masz już konto? <Link to="/login">Zaloguj się</Link>
        </p>
      </div>
    </div>
  )
}
