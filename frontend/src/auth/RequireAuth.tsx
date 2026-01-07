//Ten komponent pilnuje, żeby niezalogowany użytkownik nie mógł wejść 
// na chronioną stronę i w razie czego przekierowuje go na /login.
import { Navigate, useLocation } from "react-router-dom"
import { useAuth } from "./AuthContext"

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const auth = useAuth()
  const location = useLocation()

  if (auth.status === "loading") return <p>Sprawdzam logowanie...</p>

  if (auth.status === "unauthenticated") {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <>{children}</> //zalogowany użytkownik może zobaczyć chronioną stronę
}
