'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Navbar() {
  const pathname = usePathname()

  const navItems = [
    { name: 'Home', path: '/', prefetch: true },
    { name: 'Giocatori', path: '/players', prefetch: true },
    { name: 'Dati Wellness', path: '/data', prefetch: true },
    { name: 'Report', path: '/report', prefetch: true },
    { name: 'ML Predittivo', path: '/ml-predictive', prefetch: true },
    { name: 'Video Analysis', path: '/video-analysis', prefetch: true },
  ]

  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="text-xl font-bold" prefetch={false}>
            Football Club Platform ⚽
          </Link>

          <div className="flex space-x-4">
            {navItems.map((item) => (
              <Link
                key={item.path}
                href={item.path}
                prefetch={item.prefetch}
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
