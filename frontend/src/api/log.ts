//morning log
import { http } from "./http"

export type ScreensLastHour = "low" | "medium" | "high"
export type NapType = "none" | "short" | "medium" | "long"

export type MorningLog = {
  date: string
  sleep_start: string
  sleep_latency_extra: number
  sleep_end: string
  sleep_quality: number
  night_awakenings: number
  morning_energy: number
}

export type DailyLogRead = {
  id: number
  user_id: number
  date: string

  sleep_start: string
  sleep_latency_extra: number
  sleep_end: string
  sleep_quality: number
  night_awakenings: number
  morning_energy: number

  day_rating: number | null
  stress_level: number | null
  coffee_last_6h: boolean | null
  alcohol_last_4h: boolean | null
  screens_last_hour: ScreensLastHour | null
  nap_type: NapType | null

  sleep_duration: number | null
  day_score: number | null

  created_at: string
  updated_at: string
}

export async function apiSubmitMorningLog(data: MorningLog): Promise<DailyLogRead> {
  return http<DailyLogRead>("/daily-logs/morning", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

//evening log
export type EveningLog = {
  date: string
  day_rating: number
  stress_level: number
  coffee_last_6h: boolean
  alcohol_last_4h: boolean
  screens_last_hour: ScreensLastHour
  nap_type: NapType
}

export type DailyLogEveningResponse = { //bo wieczorny raport zapisuje dane do 2 wpisow
  today: DailyLogRead
  tomorrow: DailyLogRead
}

export async function apiSubmitEveningLog(data: EveningLog): Promise<DailyLogEveningResponse> {
  return http<DailyLogEveningResponse>("/daily-logs/evening", {
    method: "POST",
    body: JSON.stringify(data),
  })
}