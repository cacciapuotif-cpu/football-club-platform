import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Navbar from '@/components/Navbar'
import Providers from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Football Club Platform - Gestionale per Società di Calcio',
  description: 'Gestionale innovativo per società di calcio',
}

const defaultLocale = process.env.NEXT_PUBLIC_DEFAULT_LOCALE ?? 'it'
const defaultTenant = process.env.NEXT_PUBLIC_TENANT ?? 'demo-fc'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang={defaultLocale}>
      <head>
        <meta httpEquiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
        <meta httpEquiv="Pragma" content="no-cache" />
        <meta httpEquiv="Expires" content="0" />
      </head>
      <body className={`${inter.className} theme-root`}>
        <Providers locale={defaultLocale} tenant={defaultTenant}>
          <Navbar />
          <main className="min-h-screen bg-[var(--brand-surface,#f8fafc)]">{children}</main>
        </Providers>
      </body>
    </html>
  )
}
