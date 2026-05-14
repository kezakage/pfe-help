import { Outlet, NavLink, Link } from 'react-router-dom'
import { Compass, Home as HomeIcon, LogIn, UserPlus } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Logo from '../components/Logo.jsx'
import ChatbotWidget from '../components/ChatbotWidget.jsx'
import LanguageSwitcher from '../components/LanguageSwitcher.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function PublicLayout() {
  const { user } = useAuth()
  const { t } = useTranslation()
  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-30 bg-sand-50/85 backdrop-blur border-b border-sand-200">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <Logo />
          <nav className="hidden md:flex items-center gap-1">
            <NavLink to="/" end className={({isActive}) => `nav-link ${isActive ? 'nav-link-active':''}`}>
              <span className="flex items-center gap-1.5"><HomeIcon size={16}/>{t('nav.home')}</span>
            </NavLink>
            <NavLink to="/explorer" className={({isActive}) => `nav-link ${isActive ? 'nav-link-active':''}`}>
              <span className="flex items-center gap-1.5"><Compass size={16}/>{t('nav.explore')}</span>
            </NavLink>
          </nav>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            {user ? (
              <Link to="/app/tableau-de-bord" className="btn-primary">{t('nav.myWorkspace')}</Link>
            ) : (
              <>
                <Link to="/connexion" className="btn-ghost"><LogIn size={16}/>{t('nav.login')}</Link>
                <Link to="/inscription" className="btn-primary"><UserPlus size={16}/>{t('nav.register')}</Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1"><Outlet /></main>

      <footer className="border-t border-sand-200 bg-white mt-12">
        <div className="max-w-7xl mx-auto px-4 py-10 grid md:grid-cols-4 gap-8">
          <div>
            <Logo />
            <p className="text-sm text-sand-600 mt-3 max-w-xs">{t('footer.tagline')}</p>
          </div>
          <div>
            <h4 className="font-semibold mb-3 text-sand-900">{t('footer.platform')}</h4>
            <ul className="space-y-2 text-sm text-sand-600">
              <li><Link to="/explorer">{t('nav.explore')}</Link></li>
              <li><Link to="/inscription">{t('footer.becomeContributor')}</Link></li>
              <li><Link to="/connexion">{t('footer.expertSpace')}</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-3 text-sand-900">{t('footer.resources')}</h4>
            <ul className="space-y-2 text-sm text-sand-600">
              <li>{t('footer.documentation')}</li>
              <li>{t('footer.contributorGuide')}</li>
              <li>{t('footer.scientificCharter')}</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-3 text-sand-900">{t('footer.contact')}</h4>
            <ul className="space-y-2 text-sm text-sand-600">
              <li>contact@patrimoine.dz</li>
              <li>{t('footer.city')}</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-sand-200 py-4 text-center text-xs text-sand-500">
          © {new Date().getFullYear()} {t('footer.rights')}
        </div>
      </footer>

      <ChatbotWidget />
    </div>
  )
}
