'use client'

import { I18nProvider } from '@/lib/i18n/I18nProvider'
import { ThemeProvider } from '@/lib/theme/ThemeProvider'

type ProvidersProps = {
  locale: string
  tenant: string
  children: React.ReactNode
}

export default function Providers({ locale, tenant, children }: ProvidersProps) {
  return (
    <ThemeProvider tenant={tenant}>
      <I18nProvider locale={locale}>{children}</I18nProvider>
    </ThemeProvider>
  )
}

