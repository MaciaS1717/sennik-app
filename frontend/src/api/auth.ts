import { API_URL } from "../config"
import { http } from "./http"

//login

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

//register

export type RegisterRequest = {
  email: string
  password: string
  name: string
  gender: "male" | "female"
  age: number
  typical_sleep_latency: number
}

function extractFastApiError(text: string): string | null {
  try {
    const data = JSON.parse(text) as { detail?: unknown }
    if (typeof data?.detail === "string") return data.detail
    return null
  } catch {
    return null
  }
}

export async function register(data: RegisterRequest): Promise<User> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })

  if (!res.ok) {
    const text = await res.text().catch(() => "")
    const detail = extractFastApiError(text)
    throw new Error(detail ?? (text ? `HTTP ${res.status}: ${text}` : `HTTP ${res.status}`))
  }

  return (await res.json()) as User
}
