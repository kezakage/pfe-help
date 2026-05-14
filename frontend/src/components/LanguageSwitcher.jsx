import { useTranslation } from 'react-i18next'
import { Languages } from 'lucide-react'
import { SUPPORTED_LANGUAGES } from '../i18n'

/**
 * Compact FR ⟷ AR toggle. Persists the choice via i18next-browser-language-
 * detector (localStorage key `patrimoinehub_lang`); the i18n bootstrap then
 * keeps `<html dir>` in sync so Tailwind RTL utilities flip on Arabic.
 */
export default function LanguageSwitcher({ variant = 'ghost', className = '' }) {
  const { i18n } = useTranslation()
  const current = i18n.language?.startsWith('ar') ? 'ar' : 'fr'

  const next = current === 'fr' ? 'ar' : 'fr'
  const meta = SUPPORTED_LANGUAGES.find((l) => l.code === next)

  const baseClass =
    variant === 'pill'
      ? 'inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 hover:bg-white/20 text-xs text-white border border-white/20'
      : 'inline-flex items-center gap-1.5 text-sm text-sand-700 hover:text-sand-900 px-2 py-1 rounded'

  return (
    <button
      type="button"
      onClick={() => i18n.changeLanguage(next)}
      className={`${baseClass} ${className}`}
      aria-label={`Switch language to ${meta?.label}`}
      title={meta?.label}
    >
      <Languages size={14} />
      <span>{meta?.label}</span>
    </button>
  )
}
