// AuthContext zarządza globalnym stanem uwierzytelnienia użytkownika.
// Przechowuje informacje o aktualnym użytkowniku i statusie logowania
// oraz udostępnia funkcje login/logout dla całej aplikacji.

import React, { createContext, useContext, useEffect, useMemo, useState } from "react"
import { login as apiLogin, me, type User } from "../api/auth"
import { clearAccessToken, getAccessToken, setAccessToken } from "./tokenStorage"

type AuthStatus = "loading" | "authenticated" | "unauthenticated"

type AuthContextValue = {
  status: AuthStatus
  user: User | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading")
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      setStatus("unauthenticated")
      return
    }

    ;(async () => {
      try {
        const currentUser = await me()
        setUser(currentUser)
        setStatus("authenticated")
      } catch {
        clearAccessToken()
        setUser(null)
        setStatus("unauthenticated")
      }
    })()
  }, [])

  async function login(email: string, password: string) {
    setStatus("loading")
    try {
      const { access_token } = await apiLogin(email, password)
      setAccessToken(access_token)

      const currentUser = await me()
      setUser(currentUser)
      setStatus("authenticated")
    } catch (err) {
      clearAccessToken()
      setUser(null)
      setStatus("unauthenticated")
      throw err
    }
  }

  function logout() {
    clearAccessToken()
    setUser(null)
    setStatus("unauthenticated")
  }

  const value = useMemo<AuthContextValue>(() => ({ status, user, login, logout }), [status, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth musi być użyty wewnątrz <AuthProvider>")
  return ctx
}
