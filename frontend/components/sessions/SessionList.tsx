'use client'

import Link from 'next/link'
import { format, isToday, isTomorrow } from 'date-fns'
import { it } from 'date-fns/locale'
import type { SessionListItem } from '@/types/sessions'
import { useI18n } from '@/lib/i18n/I18nProvider'

const SESSION_TYPE_STYLE: Record<string, string> = {
  training: 'bg-blue-100 text-blue-700',
  match: 'bg-emerald-100 text-emerald-700',
  recovery: 'bg-amber-100 text-amber-700',
  other: 'bg-gray-100 text-gray-700',
}

type Props = {
  sessions: SessionListItem[]
  loading?: boolean
  error?: string | null
}

const formatDate = (value: string) => {
  const date = new Date(value)
  if (isToday(date)) return `Oggi • ${format(date, "HH:mm", { locale: it })}`
  if (isTomorrow(date)) return `Domani • ${format(date, "HH:mm", { locale: it })}`
  return format(date, "EEE d MMM yyyy • HH:mm", { locale: it })
}

export function SessionList({ sessions, loading = false, error }: Props) {
  const { t } = useI18n()
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="animate-pulse rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <div className="h-5 w-1/3 rounded bg-gray-200" />
            <div className="mt-3 h-4 w-1/2 rounded bg-gray-100" />
            <div className="mt-4 flex gap-3">
              <div className="h-6 w-20 rounded-full bg-gray-100" />
              <div className="h-6 w-20 rounded-full bg-gray-100" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        <p className="font-semibold">{t('sessions.error.title', 'Impossibile caricare le sessioni')}</p>
        <p className="mt-1">{error}</p>
      </div>
    )
  }

  if (!sessions.length) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-gray-500">
        {t('sessions.empty', 'Nessuna sessione trovata con i filtri selezionati.')}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {sessions.map((session) => (
        <Link
          key={session.session_id}
          href={`/sessions/${session.session_id}`}
          className="block rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition hover:border-blue-200 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
        >
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-500">{formatDate(session.start_ts)}</p>
              <p className="mt-1 text-lg font-semibold text-gray-900">
                {session.notes ? session.notes : t('sessions.card.defaultTitle', 'Sessione programmata')}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              {(() => {
                const typeKey = session.type?.toLowerCase?.() ?? session.type
                return (
                  <span
                    className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase ${
                      SESSION_TYPE_STYLE[typeKey] ?? 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {typeKey}
                  </span>
                )
              })()}
              {session.load && (
                <span className="inline-flex items-center rounded-full bg-violet-100 px-3 py-1 text-xs font-semibold text-violet-700">
                  {t('sessions.card.load', 'Load')} {Math.round(session.load)}
                </span>
              )}
              {session.rpe_avg && (
                <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                  {t('sessions.card.rpe', 'RPE')} {session.rpe_avg.toFixed(1)}
                </span>
              )}
            </div>
          </div>
        </Link>
      ))}
    </div>
  )
}
