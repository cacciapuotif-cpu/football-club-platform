'use client'

import { createContext, useContext, useMemo } from 'react'
import { dictionaries, fallbackLocale, type LocaleKey } from './dictionaries'

type I18nContextValue = {
  locale: LocaleKey
  t: (key: string, fallback?: string) => string
}

const I18nContext = createContext<I18nContextValue>({
  locale: fallbackLocale,
  t: (key: string, fallback?: string) => fallback ?? key,
})

type I18nProviderProps = {
  locale: string
  children: React.ReactNode
}

const normalizeLocale = (raw: string): LocaleKey => {
  const lower = raw?.toLowerCase?.() ?? fallbackLocale
  if (lower.startsWith('en')) return 'en'
  return 'it'
}

export function I18nProvider({ locale, children }: I18nProviderProps) {
  const normalized = normalizeLocale(locale)
  const dictionary = dictionaries[normalized] ?? dictionaries[fallbackLocale]

  const value = useMemo<I18nContextValue>(
    () => ({
      locale: normalized,
      t: (key: string, fallback?: string) => dictionary[key] ?? fallback ?? key,
    }),
    [dictionary, normalized]
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export const useI18n = () => useContext(I18nContext)

