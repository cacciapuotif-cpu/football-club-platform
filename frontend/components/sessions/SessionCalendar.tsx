'use client'

import { format, parseISO } from 'date-fns'
import { it } from 'date-fns/locale'
import Link from 'next/link'
import type { SessionListItem } from '@/types/sessions'

type Props = {
  sessions: SessionListItem[]
}

type GroupedSessions = Record<string, SessionListItem[]>

const groupByDate = (items: SessionListItem[]): GroupedSessions => {
  return items.reduce<GroupedSessions>((acc, session) => {
    const key = format(parseISO(session.start_ts), 'yyyy-MM-dd')
    if (!acc[key]) acc[key] = []
    acc[key].push(session)
    return acc
  }, {})
}

export function SessionCalendar({ sessions }: Props) {
  if (!sessions.length) {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-gray-500">
        Nessuna sessione in calendario nel periodo selezionato.
      </div>
    )
  }

  const grouped = groupByDate(sessions)
  const sortedDates = Object.keys(grouped).sort()

  return (
    <div className="space-y-6">
      {sortedDates.map((dateKey) => {
        const displayDate = format(parseISO(dateKey), "EEEE d MMMM yyyy", { locale: it })
        const daySessions = grouped[dateKey].sort(
          (a, b) => new Date(a.start_ts).getTime() - new Date(b.start_ts).getTime()
        )

        return (
          <section key={dateKey} className="rounded-lg border border-gray-200 bg-white shadow-sm">
            <header className="border-b border-gray-200 bg-gray-50 px-4 py-3">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-600">{displayDate}</h3>
            </header>
            <div className="divide-y divide-gray-100">
              {daySessions.map((session) => (
                <Link
                  key={session.session_id}
                  href={`/sessions/${session.session_id}`}
                  className="flex items-center justify-between gap-4 px-4 py-3 transition hover:bg-blue-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500"
                >
                  <div>
                    <p className="text-sm font-semibold text-gray-900">
                      {format(parseISO(session.start_ts), 'HH:mm', { locale: it })}
                    </p>
                    <p className="text-sm text-gray-500">
                      {session.notes ? session.notes : session.type.toUpperCase()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {session.load && (
                      <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-semibold text-violet-700">
                        Load {Math.round(session.load)}
                      </span>
                    )}
                    {session.rpe_avg && (
                      <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                        RPE {session.rpe_avg.toFixed(1)}
                      </span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )
      })}
    </div>
  )
}

