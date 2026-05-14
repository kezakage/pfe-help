/**
 * i18next bootstrap.
 *
 * Loaded once from main.jsx. Detects the user's preferred language from
 * (in order): localStorage > <html lang> attribute > navigator. Resources
 * are bundled at build time so we don't need an HTTP backend.
 *
 * Side-effect: keeps the document <html> dir/lang attributes in sync with
 * the active language so RTL flips automatically when Arabic is active.
 */
import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next } from 'react-i18next'

import fr from './locales/fr.json'
import ar from './locales/ar.json'

export const SUPPORTED_LANGUAGES = [
  { code: 'fr', label: 'Français', dir: 'ltr' },
  { code: 'ar', label: 'العربية', dir: 'rtl' },
]

export function applyDirAndLang(lang) {
  const meta = SUPPORTED_LANGUAGES.find((l) => l.code === lang) || SUPPORTED_LANGUAGES[0]
  if (typeof document !== 'undefined') {
    document.documentElement.lang = meta.code
    document.documentElement.dir = meta.dir
  }
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      fr: { translation: fr },
      ar: { translation: ar },
    },
    fallbackLng: 'fr',
    supportedLngs: ['fr', 'ar'],
    interpolation: { escapeValue: false }, // React already escapes
    detection: {
      order: ['localStorage', 'htmlTag', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'patrimoinehub_lang',
    },
    returnNull: false,
  })

applyDirAndLang(i18n.language)
i18n.on('languageChanged', applyDirAndLang)

export default i18n
