'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'

/**
 * PLACEHOLDER PAGE - Session Edit
 *
 * This is a temporary placeholder to prevent 404 errors.
 * The real edit functionality will be implemented later.
 */
export default function SessionEditPage({ params }: { params: { id: string } }) {
  const router = useRouter()

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Warning Banner */}
      <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6 rounded">
        <div className="flex items-center">
          <svg
            className="w-6 h-6 mr-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <div>
            <p className="font-semibold">Pagina in Costruzione</p>
            <p className="text-sm">
              Questa è una pagina placeholder temporanea per prevenire errori 404.
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">
          Editor Sessione (Placeholder)
        </h1>

        <div className="space-y-4">
          <div>
            <span className="text-sm text-gray-500">ID Sessione:</span>
            <p className="text-lg font-mono bg-gray-100 p-2 rounded">{params.id}</p>
          </div>

          <div className="border-t pt-4">
            <p className="text-gray-600 mb-4">
              La funzionalità di modifica sessione è in fase di sviluppo.
            </p>

            <div className="flex space-x-3">
              <button
                onClick={() => router.back()}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
              >
                ← Indietro
              </button>

              <Link
                href="/sessions"
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors inline-block"
              >
                Vai a Lista Sessioni
              </Link>

              <Link
                href={`/sessions/${params.id}`}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors inline-block"
              >
                Visualizza Dettaglio
              </Link>
            </div>
          </div>
        </div>

        {/* Dev Info */}
        <div className="mt-8 pt-4 border-t">
          <details className="text-sm text-gray-500">
            <summary className="cursor-pointer hover:text-gray-700 font-medium">
              Informazioni Sviluppatore
            </summary>
            <div className="mt-2 bg-gray-50 p-3 rounded">
              <p>
                <strong>File:</strong>{' '}
                <code className="text-xs">frontend/app/sessions/[id]/edit/page.tsx</code>
              </p>
              <p>
                <strong>Tipo:</strong> Placeholder temporaneo
              </p>
              <p>
                <strong>TODO:</strong> Implementare form di modifica sessione
              </p>
            </div>
          </details>
        </div>
      </div>
    </div>
  )
}
