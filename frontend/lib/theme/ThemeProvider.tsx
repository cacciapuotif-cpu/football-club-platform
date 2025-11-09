'use client'

import { createContext, useContext, useEffect, useMemo } from 'react'

type Theme = {
  tenant: string
  primaryColor: string
  accentColor: string
  background: string
}

const defaultTheme: Theme = {
  tenant: 'default',
  primaryColor: '#2563eb',
  accentColor: '#1d4ed8',
  background: '#f8fafc',
}

const tenants: Record<string, Theme> = {
  'demo-fc': {
    tenant: 'demo-fc',
    primaryColor: '#1d4ed8',
    accentColor: '#1e40af',
    background: '#f1f5f9',
  },
  'aurora-academy': {
    tenant: 'aurora-academy',
    primaryColor: '#0f766e',
    accentColor: '#115e59',
    background: '#ecfdf5',
  },
}

const ThemeContext = createContext<Theme>(defaultTheme)

type ThemeProviderProps = {
  tenant: string
  children: React.ReactNode
}

export function ThemeProvider({ tenant, children }: ThemeProviderProps) {
  const theme = tenants[tenant] ?? defaultTheme

  useEffect(() => {
    const root = document.documentElement
    root.style.setProperty('--brand-primary', theme.primaryColor)
    root.style.setProperty('--brand-accent', theme.accentColor)
    root.style.setProperty('--brand-surface', theme.background)
  }, [theme])

  const value = useMemo(() => theme, [theme])

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export const useTheme = () => useContext(ThemeContext)

