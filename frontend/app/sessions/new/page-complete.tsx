'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

type FormStep = 1 | 2 | 3 | 4 | 5

interface SessionFormData {
  // Session info
  player_code: string
  session_date: string
  session_type: string
  minutes_played: string
  coach_rating: string
  match_score: string
  notes: string
  video_url: string
  pitch_type: string
  weather: string
  time_of_day: string
  status: string

  // Physical metrics
  height_cm: string
  weight_kg: string
  body_fat_pct: string
  lean_mass_kg: string
  resting_hr_bpm: string
  max_speed_kmh: string
  accel_0_10m_s: string
  accel_0_20m_s: string
  distance_km: string
  sprints_over_25kmh: string
  vertical_jump_cm: string
  agility_illinois_s: string
  yoyo_level: string
  rpe: string
  sleep_hours: string

  // Technical metrics
  passes_attempted: string
  passes_completed: string
  progressive_passes: string
  long_pass_accuracy_pct: string
  shots: string
  shots_on_target: string
  crosses: string
  cross_accuracy_pct: string
  successful_dribbles: string
  failed_dribbles: string
  ball_losses: string
  ball_recoveries: string
  set_piece_accuracy_pct: string

  // Tactical metrics
  xg: string
  xa: string
  pressures: string
  interceptions: string
  influence_zones_pct: string
  effective_off_ball_runs: string
  transition_reaction_time_s: string
  involvement_pct: string

  // Psychological metrics
  attention_score: string
  decision_making: string
  motivation: string
  stress_management: string
  self_esteem: string
  team_leadership: string
  sleep_quality: string
  mood_pre: string
  mood_post: string
  tactical_adaptability: string
}

export default function NewSessionCompletePage() {
  const router = useRouter()
  const [step, setStep] = useState<FormStep>(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState<SessionFormData>({
    player_code: '',
    session_date: new Date().toISOString().split('T')[0],
    session_type: 'TRAINING',
    minutes_played: '90',
    coach_rating: '',
    match_score: '',
    notes: '',
    video_url: '',
    pitch_type: '',
    weather: '',
    time_of_day: '',
    status: 'OK',
    height_cm: '',
    weight_kg: '',
    body_fat_pct: '',
    lean_mass_kg: '',
    resting_hr_bpm: '60',
    max_speed_kmh: '',
    accel_0_10m_s: '',
    accel_0_20m_s: '',
    distance_km: '5.0',
    sprints_over_25kmh: '0',
    vertical_jump_cm: '',
    agility_illinois_s: '',
    yoyo_level: '',
    rpe: '5',
    sleep_hours: '7.5',
    passes_attempted: '0',
    passes_completed: '0',
    progressive_passes: '0',
    long_pass_accuracy_pct: '',
    shots: '0',
    shots_on_target: '0',
    crosses: '0',
    cross_accuracy_pct: '',
    successful_dribbles: '0',
    failed_dribbles: '0',
    ball_losses: '0',
    ball_recoveries: '0',
    set_piece_accuracy_pct: '',
    xg: '',
    xa: '',
    pressures: '0',
    interceptions: '0',
    influence_zones_pct: '',
    effective_off_ball_runs: '0',
    transition_reaction_time_s: '',
    involvement_pct: '',
    attention_score: '',
    decision_making: '',
    motivation: '',
    stress_management: '',
    self_esteem: '',
    team_leadership: '',
    sleep_quality: '',
    mood_pre: '',
    mood_post: '',
    tactical_adaptability: ''
  })

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const nextStep = () => {
    if (step < 5) setStep((step + 1) as FormStep)
  }

  const prevStep = () => {
    if (step > 1) setStep((step - 1) as FormStep)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const apiData = {
        player_code: formData.player_code,
        session: {
          session_date: formData.session_date,
          session_type: formData.session_type,
          minutes_played: parseInt(formData.minutes_played) || 0,
          coach_rating: formData.coach_rating ? parseFloat(formData.coach_rating) : null,
          match_score: formData.match_score || null,
          notes: formData.notes || null,
          video_url: formData.video_url || null,
          pitch_type: formData.pitch_type || null,
          weather: formData.weather || null,
          time_of_day: formData.time_of_day || null,
          status: formData.status
        },
        metrics_physical: {
          height_cm: formData.height_cm ? parseFloat(formData.height_cm) : null,
          weight_kg: formData.weight_kg ? parseFloat(formData.weight_kg) : null,
          body_fat_pct: formData.body_fat_pct ? parseFloat(formData.body_fat_pct) : null,
          lean_mass_kg: formData.lean_mass_kg ? parseFloat(formData.lean_mass_kg) : null,
          resting_hr_bpm: parseInt(formData.resting_hr_bpm) || 60,
          max_speed_kmh: formData.max_speed_kmh ? parseFloat(formData.max_speed_kmh) : null,
          accel_0_10m_s: formData.accel_0_10m_s ? parseFloat(formData.accel_0_10m_s) : null,
          accel_0_20m_s: formData.accel_0_20m_s ? parseFloat(formData.accel_0_20m_s) : null,
          distance_km: parseFloat(formData.distance_km) || 0,
          sprints_over_25kmh: parseInt(formData.sprints_over_25kmh) || 0,
          vertical_jump_cm: formData.vertical_jump_cm ? parseFloat(formData.vertical_jump_cm) : null,
          agility_illinois_s: formData.agility_illinois_s ? parseFloat(formData.agility_illinois_s) : null,
          yoyo_level: formData.yoyo_level ? parseFloat(formData.yoyo_level) : null,
          rpe: parseFloat(formData.rpe) || 5,
          sleep_hours: formData.sleep_hours ? parseFloat(formData.sleep_hours) : null
        },
        metrics_technical: {
          passes_attempted: parseInt(formData.passes_attempted) || 0,
          passes_completed: parseInt(formData.passes_completed) || 0,
          progressive_passes: parseInt(formData.progressive_passes) || 0,
          long_pass_accuracy_pct: formData.long_pass_accuracy_pct ? parseFloat(formData.long_pass_accuracy_pct) : null,
          shots: parseInt(formData.shots) || 0,
          shots_on_target: parseInt(formData.shots_on_target) || 0,
          crosses: parseInt(formData.crosses) || 0,
          cross_accuracy_pct: formData.cross_accuracy_pct ? parseFloat(formData.cross_accuracy_pct) : null,
          successful_dribbles: parseInt(formData.successful_dribbles) || 0,
          failed_dribbles: parseInt(formData.failed_dribbles) || 0,
          ball_losses: parseInt(formData.ball_losses) || 0,
          ball_recoveries: parseInt(formData.ball_recoveries) || 0,
          set_piece_accuracy_pct: formData.set_piece_accuracy_pct ? parseFloat(formData.set_piece_accuracy_pct) : null
        },
        metrics_tactical: {
          xg: formData.xg ? parseFloat(formData.xg) : null,
          xa: formData.xa ? parseFloat(formData.xa) : null,
          pressures: parseInt(formData.pressures) || 0,
          interceptions: parseInt(formData.interceptions) || 0,
          heatmap_zone_json: null,
          influence_zones_pct: formData.influence_zones_pct ? parseFloat(formData.influence_zones_pct) : null,
          effective_off_ball_runs: parseInt(formData.effective_off_ball_runs) || 0,
          transition_reaction_time_s: formData.transition_reaction_time_s ? parseFloat(formData.transition_reaction_time_s) : null,
          involvement_pct: formData.involvement_pct ? parseFloat(formData.involvement_pct) : null
        },
        metrics_psych: {
          attention_score: formData.attention_score ? parseInt(formData.attention_score) : null,
          decision_making: formData.decision_making ? parseInt(formData.decision_making) : null,
          motivation: formData.motivation ? parseInt(formData.motivation) : null,
          stress_management: formData.stress_management ? parseInt(formData.stress_management) : null,
          self_esteem: formData.self_esteem ? parseInt(formData.self_esteem) : null,
          team_leadership: formData.team_leadership ? parseInt(formData.team_leadership) : null,
          sleep_quality: formData.sleep_quality ? parseInt(formData.sleep_quality) : null,
          mood_pre: formData.mood_pre ? parseInt(formData.mood_pre) : null,
          mood_post: formData.mood_post ? parseInt(formData.mood_post) : null,
          tactical_adaptability: formData.tactical_adaptability ? parseInt(formData.tactical_adaptability) : null
        }
      }

      const response = await fetch('http://localhost:8000/api/v1/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(apiData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Errore nella creazione della sessione')
      }

      router.push('/sessions')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Errore sconosciuto')
    } finally {
      setLoading(false)
    }
  }

  const renderStep = () => {
    switch (step) {
      case 1:
        return renderSessionInfo()
      case 2:
        return renderPhysicalMetrics()
      case 3:
        return renderTechnicalMetrics()
      case 4:
        return renderTacticalMetrics()
      case 5:
        return renderPsychologicalMetrics()
    }
  }

  const renderSessionInfo = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800 border-b pb-2">1. Informazioni Sessione</h2>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Codice Giocatore * <span className="text-xs text-gray-500">(es: PLR001)</span>
        </label>
        <input
          type="text"
          name="player_code"
          value={formData.player_code}
          onChange={handleChange}
          required
          placeholder="PLR001"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Data *</label>
          <input
            type="date"
            name="session_date"
            value={formData.session_date}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Sessione *</label>
          <select
            name="session_type"
            value={formData.session_type}
            onChange={handleChange}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="TRAINING">Allenamento</option>
            <option value="MATCH">Partita</option>
            <option value="TEST">Test Fisico</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Minuti Giocati *</label>
          <input
            type="number"
            name="minutes_played"
            value={formData.minutes_played}
            onChange={handleChange}
            required
            min="0"
            max="180"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Valutazione Allenatore (0-10)</label>
          <input
            type="number"
            name="coach_rating"
            value={formData.coach_rating}
            onChange={handleChange}
            min="0"
            max="10"
            step="0.5"
            placeholder="7.5"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Campo</label>
          <select
            name="pitch_type"
            value={formData.pitch_type}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Seleziona...</option>
            <option value="NATURAL">Erba Naturale</option>
            <option value="SYNTHETIC">Sintetico</option>
            <option value="INDOOR">Indoor</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Meteo</label>
          <input
            type="text"
            name="weather"
            value={formData.weather}
            onChange={handleChange}
            placeholder="Sereno, 20°C"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Orario</label>
          <select
            name="time_of_day"
            value={formData.time_of_day}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Seleziona...</option>
            <option value="MORNING">Mattina</option>
            <option value="AFTERNOON">Pomeriggio</option>
            <option value="EVENING">Sera</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Note</label>
        <textarea
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          rows={3}
          placeholder="Note aggiuntive sulla sessione..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </div>
  )

  const renderPhysicalMetrics = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800 border-b pb-2">2. Metriche Fisiche</h2>

      <div className="bg-blue-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Antropometria</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Altezza (cm)</label>
            <input
              type="number"
              name="height_cm"
              value={formData.height_cm}
              onChange={handleChange}
              placeholder="175"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Peso (kg)</label>
            <input
              type="number"
              name="weight_kg"
              value={formData.weight_kg}
              onChange={handleChange}
              placeholder="70"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Grasso Corporeo (%)</label>
            <input
              type="number"
              name="body_fat_pct"
              value={formData.body_fat_pct}
              onChange={handleChange}
              placeholder="12"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Massa Magra (kg)</label>
            <input
              type="number"
              name="lean_mass_kg"
              value={formData.lean_mass_kg}
              onChange={handleChange}
              placeholder="61.6"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-green-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Cardio & Velocità</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">FC Riposo (bpm) *</label>
            <input
              type="number"
              name="resting_hr_bpm"
              value={formData.resting_hr_bpm}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Vel. Max (km/h)</label>
            <input
              type="number"
              name="max_speed_kmh"
              value={formData.max_speed_kmh}
              onChange={handleChange}
              placeholder="32.5"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Distanza (km) *</label>
            <input
              type="number"
              name="distance_km"
              value={formData.distance_km}
              onChange={handleChange}
              required
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-yellow-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Accelerazione & Potenza</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Accel 0-10m (s)</label>
            <input
              type="number"
              name="accel_0_10m_s"
              value={formData.accel_0_10m_s}
              onChange={handleChange}
              placeholder="1.8"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Accel 0-20m (s)</label>
            <input
              type="number"
              name="accel_0_20m_s"
              value={formData.accel_0_20m_s}
              onChange={handleChange}
              placeholder="3.1"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sprint {'>'}25km/h</label>
            <input
              type="number"
              name="sprints_over_25kmh"
              value={formData.sprints_over_25kmh}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Salto Verticale (cm)</label>
            <input
              type="number"
              name="vertical_jump_cm"
              value={formData.vertical_jump_cm}
              onChange={handleChange}
              placeholder="45"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-purple-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Test & Recupero</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Agilità Illinois (s)</label>
            <input
              type="number"
              name="agility_illinois_s"
              value={formData.agility_illinois_s}
              onChange={handleChange}
              placeholder="15.5"
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Yo-Yo Test (livello)</label>
            <input
              type="number"
              name="yoyo_level"
              value={formData.yoyo_level}
              onChange={handleChange}
              placeholder="18.5"
              step="0.5"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">RPE (1-10) *</label>
            <input
              type="number"
              name="rpe"
              value={formData.rpe}
              onChange={handleChange}
              required
              min="1"
              max="10"
              step="0.5"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ore Sonno</label>
            <input
              type="number"
              name="sleep_hours"
              value={formData.sleep_hours}
              onChange={handleChange}
              placeholder="7.5"
              step="0.5"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>
    </div>
  )

  const renderTechnicalMetrics = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800 border-b pb-2">3. Metriche Tecniche</h2>

      <div className="bg-blue-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Passaggi</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Passaggi Tentati</label>
            <input
              type="number"
              name="passes_attempted"
              value={formData.passes_attempted}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Passaggi Completati</label>
            <input
              type="number"
              name="passes_completed"
              value={formData.passes_completed}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Pass. Progressivi</label>
            <input
              type="number"
              name="progressive_passes"
              value={formData.progressive_passes}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Precisione Pass Lunghi (%)</label>
            <input
              type="number"
              name="long_pass_accuracy_pct"
              value={formData.long_pass_accuracy_pct}
              onChange={handleChange}
              placeholder="75"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-red-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Tiri & Finalizzazione</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tiri Totali</label>
            <input
              type="number"
              name="shots"
              value={formData.shots}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tiri in Porta</label>
            <input
              type="number"
              name="shots_on_target"
              value={formData.shots_on_target}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cross Totali</label>
            <input
              type="number"
              name="crosses"
              value={formData.crosses}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Precisione Cross (%)</label>
            <input
              type="number"
              name="cross_accuracy_pct"
              value={formData.cross_accuracy_pct}
              onChange={handleChange}
              placeholder="40"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-green-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Dribbling & Possesso</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dribbling Riusciti</label>
            <input
              type="number"
              name="successful_dribbles"
              value={formData.successful_dribbles}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dribbling Falliti</label>
            <input
              type="number"
              name="failed_dribbles"
              value={formData.failed_dribbles}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Perdite Palla</label>
            <input
              type="number"
              name="ball_losses"
              value={formData.ball_losses}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Recuperi Palla</label>
            <input
              type="number"
              name="ball_recoveries"
              value={formData.ball_recoveries}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-yellow-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Calci Piazzati</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Precisione Calci Piazzati (%)</label>
            <input
              type="number"
              name="set_piece_accuracy_pct"
              value={formData.set_piece_accuracy_pct}
              onChange={handleChange}
              placeholder="60"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>
    </div>
  )

  const renderTacticalMetrics = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800 border-b pb-2">4. Metriche Tattiche</h2>

      <div className="bg-blue-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Expected Goals & Assists</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">xG (Expected Goals)</label>
            <input
              type="number"
              name="xg"
              value={formData.xg}
              onChange={handleChange}
              placeholder="0.45"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">xA (Expected Assists)</label>
            <input
              type="number"
              name="xa"
              value={formData.xa}
              onChange={handleChange}
              placeholder="0.35"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-green-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Fase Difensiva</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Pressioni</label>
            <input
              type="number"
              name="pressures"
              value={formData.pressures}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Intercetti</label>
            <input
              type="number"
              name="interceptions"
              value={formData.interceptions}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-purple-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Posizionamento & Movimenti</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Zone Influenza (%)</label>
            <input
              type="number"
              name="influence_zones_pct"
              value={formData.influence_zones_pct}
              onChange={handleChange}
              placeholder="65"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Movimenti Senza Palla</label>
            <input
              type="number"
              name="effective_off_ball_runs"
              value={formData.effective_off_ball_runs}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tempo Reazione Transiz. (s)</label>
            <input
              type="number"
              name="transition_reaction_time_s"
              value={formData.transition_reaction_time_s}
              onChange={handleChange}
              placeholder="2.5"
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Coinvolgimento (%)</label>
            <input
              type="number"
              name="involvement_pct"
              value={formData.involvement_pct}
              onChange={handleChange}
              placeholder="75"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>
    </div>
  )

  const renderPsychologicalMetrics = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-gray-800 border-b pb-2">5. Metriche Psicologiche</h2>
      <p className="text-sm text-gray-600">Valutazioni su scala 1-10 (1=Molto Basso, 10=Eccellente)</p>

      <div className="bg-blue-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Stato Mentale</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Attenzione (0-100)</label>
            <input
              type="number"
              name="attention_score"
              value={formData.attention_score}
              onChange={handleChange}
              placeholder="75"
              min="0"
              max="100"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Decision Making (1-10)</label>
            <input
              type="number"
              name="decision_making"
              value={formData.decision_making}
              onChange={handleChange}
              placeholder="7"
              min="1"
              max="10"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Adattabilità Tattica (1-10)</label>
            <input
              type="number"
              name="tactical_adaptability"
              value={formData.tactical_adaptability}
              onChange={handleChange}
              placeholder="7"
              min="1"
              max="10"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-green-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Caratteristiche Personali</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Motivazione (1-10)</label>
            <input
              type="number"
              name="motivation"
              value={formData.motivation}
              onChange={handleChange}
              placeholder="8"
              min="1"
              max="10"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Autostima (1-10)</label>
            <input
              type="number"
              name="self_esteem"
              value={formData.self_esteem}
              onChange={handleChange}
              placeholder="7"
              min="1"
              max="10"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Leadership (1-10)</label>
            <input
              type="number"
              name="team_leadership"
              value={formData.team_leadership}
              onChange={handleChange}
              placeholder="6"
              min="1"
              max="10"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Gestione Stress (1-10)</label>
            <input
              type="number"
              name="stress_management"
              value={formData.stress_management}
              onChange={handleChange}
              placeholder="7"
              min="1"
              max="10"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-purple-50 p-4 rounded-md">
        <h3 className="font-semibold text-gray-800 mb-3">Umore & Riposo</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Qualità Sonno (1-10)</label>
            <input
              type="number"
              name="sleep_quality"
              value={formData.sleep_quality}
              onChange={handleChange}
              placeholder="8"
              min="1"
              max="10"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Umore Pre-Sessione (1-10)</label>
            <input
              type="number"
              name="mood_pre"
              value={formData.mood_pre}
              onChange={handleChange}
              placeholder="7"
              min="1"
              max="10"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Umore Post-Sessione (1-10)</label>
            <input
              type="number"
              name="mood_post"
              value={formData.mood_post}
              onChange={handleChange}
              placeholder="8"
              min="1"
              max="10"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-6">
        <Link href="/sessions" className="text-blue-600 hover:text-blue-800">
          ← Torna alla lista
        </Link>
      </div>

      <h1 className="text-3xl font-bold text-gray-800 mb-6">Nuova Sessione - Form Completo</h1>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between mb-2">
          {[1, 2, 3, 4, 5].map((s) => (
            <div key={s} className={`text-sm font-medium ${step === s ? 'text-blue-600' : step > s ? 'text-green-600' : 'text-gray-400'}`}>
              Step {s}
            </div>
          ))}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(step / 5) * 100}%` }}
          />
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-lg p-6">
        {renderStep()}

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8 pt-6 border-t">
          <button
            type="button"
            onClick={prevStep}
            disabled={step === 1}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← Indietro
          </button>

          <div className="flex gap-4">
            {step < 5 ? (
              <button
                type="button"
                onClick={nextStep}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Avanti →
              </button>
            ) : (
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? 'Salvataggio...' : 'Salva Sessione Completa'}
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  )
}
