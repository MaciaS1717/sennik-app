import { http } from "./http"
//komunikacja z backendem do pobierania statystyk snu i dziennych logów
export type StatisticsSummary = {
  average_sleep_duration: number | null
  average_sleep_quality: number | null
  average_morning_energy: number | null
  average_night_awakenings: number | null
  average_day_rating: number | null
  average_stress_level: number | null
}

export type StatisticsDailyPoint = {
  date: string
  sleep_duration: number | null
  sleep_quality: number | null
  night_awakenings: number | null
  morning_energy: number | null
  day_rating: number | null
  stress_level: number | null
}

export type StatisticsResponse = {
  period: {
    date_from: string
    date_to: string
    report_count: number
  }
  summary: StatisticsSummary
  daily: StatisticsDailyPoint[]
}

export async function apiGetStatistics(
  dateFrom: string,
  dateTo: string,
): Promise<StatisticsResponse> {
  const params = new URLSearchParams({
    date_from: dateFrom,
    date_to: dateTo,
  })

  return http<StatisticsResponse>(`/statistics?${params.toString()}`)
}