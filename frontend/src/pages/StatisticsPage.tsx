import { useEffect, useState } from "react"
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { apiGetStatistics, type StatisticsResponse } from "../api/statistics"
import "../styles/pages/statistics.css"

function toDateInputValue(date: Date) {
  return date.toISOString().slice(0, 10)
}

function getTodayDate() {
  return toDateInputValue(new Date())
}

function getDateDaysAgo(days: number) {
  const date = new Date()
  date.setDate(date.getDate() - days)
  return toDateInputValue(date)
}

function formatValue(value: number | null, suffix = "") {
  if (value === null) {
    return "-"
  }

  return `${value}${suffix}`
}

export default function StatisticsPage() {
  const [dateFrom, setDateFrom] = useState(getDateDaysAgo(14))
  const [dateTo, setDateTo] = useState(getTodayDate())
  const [statistics, setStatistics] = useState<StatisticsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadStatistics() {
    setError(null)

    if (dateFrom > dateTo) {
      setStatistics(null)
      setError("Data początkowa nie może być późniejsza niż data końcowa.")
      return
    }

    setIsLoading(true)

    try {
      const data = await apiGetStatistics(dateFrom, dateTo)
      setStatistics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nie udało się pobrać statystyk.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadStatistics()
  }, [])

  return (
    <div className="statisticsPage">
      <div className="statisticsContainer">
        <header className="statisticsHeader">
          <h1>Statystyki snu</h1>
          <p>Prototyp panelu do sprawdzenia danych z raportów dziennych.</p>
        </header>

        <div className="statisticsFilters">
          <label className="statisticsField">
            Od
            <input
              className="statisticsControl"
              type="date"
              value={dateFrom}
              onChange={(event) => setDateFrom(event.target.value)}
            />
          </label>

          <label className="statisticsField">
            Do
            <input
              className="statisticsControl"
              type="date"
              value={dateTo}
              onChange={(event) => setDateTo(event.target.value)}
            />
          </label>

          <button
            className="statisticsButton"
            type="button"
            onClick={loadStatistics}
            disabled={isLoading}
          >
            {isLoading ? "Pobieranie..." : "Pobierz statystyki"}
          </button>
        </div>

        {error && <p className="statisticsError">{error}</p>}

        {statistics && (
          <>
            <section className="statisticsSummary">
              <div className="statisticsSummaryItem">
                <p className="statisticsSummaryLabel">Raporty</p>
                <p className="statisticsSummaryValue">{statistics.period.report_count}</p>
              </div>

              <div className="statisticsSummaryItem">
                <p className="statisticsSummaryLabel">Średni sen</p>
                <p className="statisticsSummaryValue">
                  {formatValue(statistics.summary.average_sleep_duration, " h")}
                </p>
              </div>

              <div className="statisticsSummaryItem">
                <p className="statisticsSummaryLabel">Jakość snu</p>
                <p className="statisticsSummaryValue">
                  {formatValue(statistics.summary.average_sleep_quality)}
                </p>
              </div>

              <div className="statisticsSummaryItem">
                <p className="statisticsSummaryLabel">Energia rano</p>
                <p className="statisticsSummaryValue">
                  {formatValue(statistics.summary.average_morning_energy)}
                </p>
              </div>

              <div className="statisticsSummaryItem">
                <p className="statisticsSummaryLabel">Wybudzenia</p>
                <p className="statisticsSummaryValue">
                  {formatValue(statistics.summary.average_night_awakenings)}
                </p>
              </div>

              <div className="statisticsSummaryItem">
                <p className="statisticsSummaryLabel">Stres</p>
                <p className="statisticsSummaryValue">
                  {formatValue(statistics.summary.average_stress_level)}
                </p>
              </div>
            </section>

            {statistics.daily.length === 0 ? (
              <p className="statisticsEmpty">Brak raportów w wybranym zakresie.</p>
            ) : (
              <>
                <section className="statisticsChartBox">
                  <h2>Długość snu</h2>

                  <div className="statisticsChart">
                    <ResponsiveContainer>
                      <LineChart data={statistics.daily}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Line
                          type="monotone"
                          dataKey="sleep_duration"
                          name="Długość snu"
                          stroke="#2563eb"
                          connectNulls
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </section>

                <section className="statisticsChartBox">
                  <h2>Jakość snu</h2>

                  <div className="statisticsChart">
                    <ResponsiveContainer>
                      <LineChart data={statistics.daily}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis domain={[0, 10]} />
                        <Tooltip />
                        <Line
                          type="monotone"
                          dataKey="sleep_quality"
                          name="Jakość snu"
                          stroke="#16a34a"
                          connectNulls
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </section>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}