import { API_URL } from "../config"
import { http } from "./http"

export type LoginResponse = {
  access_token: string
  token_type: "bearer"
}

export type User = {
  id: number
  email: string
  name: string
  gender: "male" | "female"
  age: number
  typical_sleep_latency: number
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const body = new URLSearchParams()
  body.set("username", email)
  body.set("password", password)

  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  })

  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new Error(`HTTP ${res.status}: ${text}`)
  }

  return (await res.json()) as LoginResponse
}

export async function me(): Promise<User> {
  return http<User>("/auth/me")
}
