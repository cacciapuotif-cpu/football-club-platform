'use client'

import { useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'

export default function EditWellnessPage() {
  const router = useRouter()
  const params = useParams()

  useEffect(() => {
    // For now, redirect to detail page
    // TODO: Implement full edit functionality
    router.push(`/wellness/${params.id}`)
  }, [params.id, router])

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-center items-center h-64">
        <div className="text-xl text-gray-600">Reindirizzamento...</div>
      </div>
    </div>
  )
}
