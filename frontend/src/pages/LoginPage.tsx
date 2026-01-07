import { useState } from "react"
import { useLocation, useNavigate, Link } from "react-router-dom"
import { useAuth } from "../auth/AuthContext"
import "../styles/pages/login.css"

type LocationState = { from?: { pathname: string } }

export default function LoginPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as LocationState | null)?.from?.pathname ?? "/"

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)

  //obsługa formularza logowania gdy użytkownik kliknie "Zaloguj"
  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)

    try {
      await auth.login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nie udało się zalogować")
    }
  }

  return (
    <div className="loginPage">
      <div className="loginCard">
      <h1>Logowanie</h1>

      <form onSubmit={onSubmit}>
        <label>
          Email
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            style={{ width: "100%", padding: 8, marginTop: 4, marginBottom: 12 }}
          />
        </label>

        <label>
          Hasło
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            autoComplete="current-password"
            style={{ width: "100%", padding: 8, marginTop: 4, marginBottom: 12 }}
          />
        </label>

        <button type="submit" disabled={auth.status === "loading"} style={{ width: "100%" }}>
          Zaloguj
        </button>

        {error && <p style={{ color: "crimson" }}>{error}</p>}
      </form>

      <p>
        Nie masz konta? <Link to="/register">Zarejestruj się</Link>
      </p>
      </div>
    </div>
  )
}
