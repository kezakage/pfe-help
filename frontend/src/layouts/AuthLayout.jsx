import { Outlet, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Logo from '../components/Logo.jsx'
import LanguageSwitcher from '../components/LanguageSwitcher.jsx'

export default function AuthLayout() {
  const { t } = useTranslation()
  return (
    <div className="min-h-screen grid md:grid-cols-2">
      <div className="hidden md:flex flex-col justify-between p-10 text-white relative overflow-hidden"
           style={{ background: 'linear-gradient(135deg,#67241a,#3e2417)' }}>
        <div className="absolute inset-0 opacity-20"
             style={{ backgroundImage: 'repeating-linear-gradient(45deg, rgba(255,255,255,.4) 0 1px, transparent 1px 16px)' }}/>
        <div className="relative flex items-center justify-between">
          <Logo white />
          <LanguageSwitcher variant="pill" />
        </div>
        <div className="relative">
          <h2 className="font-display text-4xl font-bold leading-tight max-w-md">
            {t('auth.heroTitle')}
          </h2>
          <p className="mt-4 text-sand-200 max-w-md">
            {t('auth.heroBody')}
          </p>
          <div className="mt-8 grid grid-cols-3 gap-3 max-w-md">
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="text-2xl font-bold">+150</div>
              <div className="text-xs text-sand-200">{t('auth.heroMonuments')}</div>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="text-2xl font-bold">+80</div>
              <div className="text-xs text-sand-200">{t('auth.heroExperts')}</div>
            </div>
            <div className="bg-white/10 backdrop-blur rounded-lg p-3">
              <div className="text-2xl font-bold">12k</div>
              <div className="text-xs text-sand-200">{t('auth.heroAnnotations')}</div>
            </div>
          </div>
        </div>
        <Link to="/" className="text-sm text-sand-200 hover:text-white relative">← {t('nav.backToHome')}</Link>
      </div>
      <div className="flex items-center justify-center p-6 md:p-10">
        <div className="md:hidden flex justify-end mb-4">
          <LanguageSwitcher />
        </div>
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
