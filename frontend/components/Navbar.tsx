'use client'

import Link from 'next/link'
import { useEffect } from 'react'
import { usePathname } from 'next/navigation'

// FORZA REBUILD: Timestamp per invalidare cache / versioning
const NAVBAR_VERSION = '2025-01-27-v3'

type NavItem = {
  name: string
  path: string
}

const NAV_ITEMS: NavItem[] = [
  { name: 'Home', path: '/' },
  { name: 'Giocatori', path: '/players' },
  { name: 'Sessioni', path: '/sessions' },
  { name: 'Wellness', path: '/wellness' },
  { name: 'Report', path: '/report' },
  { name: 'ML Predittivo', path: '/ml-predictive' },
]

export default function Navbar() {
  const pathname = usePathname()

  useEffect(() => {
    if (typeof window !== 'undefined') {
      console.log(`[Navbar v${NAVBAR_VERSION}] Items:`, NAV_ITEMS.map((i) => `${i.name} -> ${i.path}`))
      console.log(`[Navbar v${NAVBAR_VERSION}] Total items: ${NAV_ITEMS.length}`)
      console.log(`[Navbar v${NAVBAR_VERSION}] Current pathname: ${pathname}`)
    }
  }, [pathname])

  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="text-xl font-bold" prefetch={false}>
            Football Club Platform ⚽
          </Link>

          <div className="flex space-x-4">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.path}
                href={item.path}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  pathname === item.path
                    ? 'bg-blue-700 text-white'
                    : 'text-blue-100 hover:bg-blue-500 hover:text-white'
                }`}
              >
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}
