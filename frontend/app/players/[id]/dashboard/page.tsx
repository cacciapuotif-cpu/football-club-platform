'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface PlayerSummary {
  player: {
    id: string
    first_name: string
    last_name: string
    age: number
    role_primary: string
    jersey_number: number | null
    is_injured: boolean
  }
  wellness_last_7_days: {
    avg_sleep_hours: number | null
    avg_sleep_quality: number | null
    avg_fatigue: number | null
    avg_stress: number | null
    avg_mood: number | null
    total_load: number | null
  }
  latest_physical_test: {
    date: string | null
    weight_kg: number | null
    height_cm: number | null
    bmi: number | null
    vo2max: number | null
    sprint_20m_s: number | null
    cmj_cm: number | null
  }
}

interface WellnessTrends {
  dates: string[]
  sleep_hours: (number | null)[]
  sleep_quality: (number | null)[]
  fatigue: (number | null)[]
  stress: (number | null)[]
  mood: (number | null)[]
  motivation: (number | null)[]
  training_load: (number | null)[]
}

interface TrainingLoad {
  daily_loads: { date: string; load: number; srpe: number | null }[]
  cumulative_load: number[]
  acwr: { date: string; acwr: number | null; acute_load: number | null }[]
  total_load: number
  average_daily_load: number
}

export default function PlayerDashboard() {
  const params = useParams()
  const router = useRouter()
  const playerId = params.id as string

  const [summary, setSummary] = useState<PlayerSummary | null>(null)
  const [wellnessTrends, setWellnessTrends] = useState<WellnessTrends | null>(null)
  const [trainingLoad, setTrainingLoad] = useState<TrainingLoad | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(30)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }
    if (playerId) {
      fetchDashboardData()
    }
  }, [playerId, days, router])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem('access_token')
      const baseUrl = 'http://localhost:8000/api/v1'

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      }

      const [summaryRes, wellnessRes, loadRes] = await Promise.all([
        fetch(`${baseUrl}/analytics/players/${playerId}/summary`, { headers }),
        fetch(`${baseUrl}/analytics/players/${playerId}/wellness-trends?days=${days}`, { headers }),
        fetch(`${baseUrl}/analytics/players/${playerId}/training-load?days=${days}`, { headers }),
      ])

      if (!summaryRes.ok || !wellnessRes.ok || !loadRes.ok) {
        throw new Error('Errore nel caricamento dei dati')
      }

      const [summaryData, wellnessData, loadData] = await Promise.all([
        summaryRes.json(),
        wellnessRes.json(),
        loadRes.json(),
      ])

      setSummary(summaryData)
      setWellnessTrends(wellnessData)
      setTrainingLoad(loadData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  // Format data for charts
  const getWellnessChartData = () => {
    if (!wellnessTrends) return []
    return wellnessTrends.dates.map((date, i) => ({
      date: new Date(date).toLocaleDateString('it-IT', { month: 'short', day: 'numeric' }),
      sonno: wellnessTrends.sleep_hours[i],
      fatica: wellnessTrends.fatigue[i],
      stress: wellnessTrends.stress[i],
      umore: wellnessTrends.mood[i],
      motivazione: wellnessTrends.motivation[i],
    }))
  }

  const getLoadChartData = () => {
    if (!trainingLoad) return []
    return trainingLoad.daily_loads.map((load, i) => ({
      date: new Date(load.date).toLocaleDateString('it-IT', { month: 'short', day: 'numeric' }),
      carico: load.load,
      acwr: trainingLoad.acwr[i]?.acwr,
    }))
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="text-xl text-gray-600">Caricamento dashboard...</div>
        </div>
      </div>
    )
  }

  if (error || !summary) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error || 'Impossibile caricare i dati'}
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <Link href="/players" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
          ← Torna ai giocatori
        </Link>
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">
              {summary.player.first_name} {summary.player.last_name}
              {summary.player.jersey_number && (
                <span className="text-blue-600"> #{summary.player.jersey_number}</span>
              )}
            </h1>
            <p className="text-gray-600">
              {summary.player.age} anni • {summary.player.role_primary}
              {summary.player.is_injured && (
                <span className="ml-2 px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                  Infortunato
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-2">
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={7}>Ultimi 7 giorni</option>
              <option value={14}>Ultimi 14 giorni</option>
              <option value={30}>Ultimi 30 giorni</option>
              <option value={90}>Ultimi 3 mesi</option>
            </select>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Sonno Medio</h3>
          <p className="text-3xl font-bold text-gray-800">
            {summary.wellness_last_7_days.avg_sleep_hours?.toFixed(1) || '-'}
            <span className="text-lg text-gray-500"> ore</span>
          </p>
          <p className="text-sm text-gray-600 mt-1">
            Qualità: {summary.wellness_last_7_days.avg_sleep_quality?.toFixed(1) || '-'}/5
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Fatica Media</h3>
          <p className="text-3xl font-bold text-gray-800">
            {summary.wellness_last_7_days.avg_fatigue?.toFixed(1) || '-'}
            <span className="text-lg text-gray-500">/5</span>
          </p>
          <p className="text-sm text-gray-600 mt-1">Ultimi 7 giorni</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Carico Totale</h3>
          <p className="text-3xl font-bold text-gray-800">
            {summary.wellness_last_7_days.total_load?.toFixed(0) || '0'}
            <span className="text-lg text-gray-500"> AU</span>
          </p>
          <p className="text-sm text-gray-600 mt-1">Ultimi 7 giorni</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Umore Medio</h3>
          <p className="text-3xl font-bold text-gray-800">
            {summary.wellness_last_7_days.avg_mood?.toFixed(1) || '-'}
            <span className="text-lg text-gray-500">/5</span>
          </p>
          <p className="text-sm text-gray-600 mt-1">Ultimi 7 giorni</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Wellness Trends */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Trend Wellness</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={getWellnessChartData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" style={{ fontSize: '12px' }} />
              <YAxis domain={[0, 10]} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="sonno" stroke="#8b5cf6" name="Ore Sonno" />
              <Line type="monotone" dataKey="fatica" stroke="#ef4444" name="Fatica" />
              <Line type="monotone" dataKey="stress" stroke="#f59e0b" name="Stress" />
              <Line type="monotone" dataKey="umore" stroke="#10b981" name="Umore" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Training Load */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Carico di Allenamento</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getLoadChartData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" style={{ fontSize: '12px' }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="carico" fill="#3b82f6" name="Carico Giornaliero (AU)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* ACWR */}
        {trainingLoad && trainingLoad.acwr.some(a => a.acwr !== null) && (
          <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              ACWR - Acute:Chronic Workload Ratio
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Rapporto tra carico acuto (7 giorni) e carico cronico (28 giorni). Range ideale: 0.8-1.3
            </p>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={getLoadChartData()}>
                <defs>
                  <linearGradient id="colorAcwr" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" style={{ fontSize: '12px' }} />
                <YAxis domain={[0, 2]} />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="acwr"
                  stroke="#8b5cf6"
                  fillOpacity={1}
                  fill="url(#colorAcwr)"
                  name="ACWR"
                />
                {/* Reference lines for ideal range */}
                <line x1="0" y1="0.8" x2="100%" y2="0.8" stroke="green" strokeDasharray="5 5" />
                <line x1="0" y1="1.3" x2="100%" y2="1.3" stroke="orange" strokeDasharray="5 5" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Physical Data */}
      {summary.latest_physical_test.date && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">
            Dati Fisici
            <span className="text-sm font-normal text-gray-500 ml-2">
              (Ultimo test: {new Date(summary.latest_physical_test.date).toLocaleDateString('it-IT')})
            </span>
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">Peso</p>
              <p className="text-2xl font-bold text-gray-800">
                {summary.latest_physical_test.weight_kg || '-'} kg
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Altezza</p>
              <p className="text-2xl font-bold text-gray-800">
                {summary.latest_physical_test.height_cm || '-'} cm
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">BMI</p>
              <p className="text-2xl font-bold text-gray-800">
                {summary.latest_physical_test.bmi?.toFixed(1) || '-'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">VO2max</p>
              <p className="text-2xl font-bold text-gray-800">
                {summary.latest_physical_test.vo2max?.toFixed(1) || '-'} ml/kg/min
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Sprint 20m</p>
              <p className="text-2xl font-bold text-gray-800">
                {summary.latest_physical_test.sprint_20m_s?.toFixed(2) || '-'} s
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-500">CMJ</p>
              <p className="text-2xl font-bold text-gray-800">
                {summary.latest_physical_test.cmj_cm?.toFixed(1) || '-'} cm
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
