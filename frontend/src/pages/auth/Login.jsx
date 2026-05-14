import { useEffect, useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Mail, Lock, ArrowRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../context/AuthContext.jsx'
import { auth } from '../../lib/api.js'

/**
 * Build the provider's authorize URL with our client_id + the frontend
 * callback URL. The provider will redirect the user here on success with
 * `?code=...`, which SocialCallback.jsx hands to the backend.
 */
function buildAuthorizeUrl(provider, cfg) {
  const redirect_uri = `${window.location.origin}${cfg.callback_path}`
  const params = new URLSearchParams({
    client_id: cfg.client_id,
    redirect_uri,
    response_type: 'code',
    scope: cfg.scope.join(' '),
  })
  if (provider === 'google') params.set('access_type', 'online')
  return `${cfg.authorize_url}?${params.toString()}`
}

export default function Login() {
  const { login, loginAs } = useAuth()
  const { t } = useTranslation()
  const [email, setEmail] = useState('amina.belhadj@univ-alger.dz')
  const [password, setPassword] = useState('demo')
  const [providers, setProviders] = useState({ google: { enabled: false }, github: { enabled: false } })
  const nav = useNavigate()
  const loc = useLocation()
  const from = loc.state?.from || '/app/tableau-de-bord'

  useEffect(() => {
    auth.socialProviders().then(setProviders).catch(() => {})
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    await login(email, password)
    nav(from, { replace: true })
  }
  const quick = (role) => { loginAs(role); nav(from, { replace: true }) }

  const goSocial = (provider) => {
    const cfg = providers[provider]
    if (!cfg?.enabled) return
    window.location.href = buildAuthorizeUrl(provider, cfg)
  }

  const anySocial = providers.google?.enabled || providers.github?.enabled

  return (
    <div>
      <h1 className="text-2xl font-semibold">{t('auth.loginTitle')}</h1>
      <p className="text-sand-600 text-sm mt-1">{t('auth.loginSubtitle')}</p>

      {anySocial && (
        <div className="mt-6 space-y-2">
          {providers.google?.enabled && (
            <button onClick={() => goSocial('google')}
                    className="btn-secondary w-full justify-center gap-2">
              <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
                <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"/>
                <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.836.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"/>
                <path fill="#FBBC05" d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"/>
                <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/>
              </svg>
              {t('auth.continueWithGoogle')}
            </button>
          )}
          {providers.github?.enabled && (
            <button onClick={() => goSocial('github')}
                    className="btn-secondary w-full justify-center gap-2">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55 0-.27-.01-1.18-.02-2.13-3.2.7-3.88-1.36-3.88-1.36-.52-1.32-1.27-1.67-1.27-1.67-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.68 1.25 3.34.96.1-.74.4-1.25.72-1.54-2.55-.29-5.24-1.27-5.24-5.66 0-1.25.45-2.27 1.18-3.07-.12-.29-.51-1.46.11-3.05 0 0 .96-.31 3.15 1.17.91-.25 1.89-.38 2.86-.39.97.01 1.95.14 2.87.39 2.18-1.48 3.14-1.17 3.14-1.17.62 1.59.23 2.76.11 3.05.74.8 1.18 1.82 1.18 3.07 0 4.4-2.69 5.36-5.25 5.65.41.36.78 1.06.78 2.13 0 1.54-.01 2.78-.01 3.16 0 .3.21.67.8.55C20.21 21.39 23.5 17.08 23.5 12 23.5 5.65 18.35.5 12 .5z"/>
              </svg>
              {t('auth.continueWithGithub')}
            </button>
          )}
          <div className="flex items-center gap-3 my-4 text-xs text-sand-500">
            <div className="flex-1 h-px bg-sand-200"/>{t('auth.or')}<div className="flex-1 h-px bg-sand-200"/>
          </div>
        </div>
      )}

      <form onSubmit={submit} className="mt-2 space-y-4">
        <div>
          <label className="label">{t('auth.email')}</label>
          <div className="relative">
            <Mail size={16} className="absolute start-3 top-1/2 -translate-y-1/2 text-sand-400"/>
            <input type="email" required value={email} onChange={e=>setEmail(e.target.value)} className="input ps-9"/>
          </div>
        </div>
        <div>
          <label className="label">{t('auth.password')}</label>
          <div className="relative">
            <Lock size={16} className="absolute start-3 top-1/2 -translate-y-1/2 text-sand-400"/>
            <input type="password" required value={password} onChange={e=>setPassword(e.target.value)} className="input ps-9"/>
          </div>
        </div>
        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-sand-700"><input type="checkbox"/>{t('auth.rememberMe')}</label>
          <Link to="/mot-de-passe-oublie" className="text-terracotta-700 hover:underline">{t('auth.forgotPassword')}</Link>
        </div>
        <button className="btn-primary w-full">{t('auth.submit')} <ArrowRight size={16}/></button>
      </form>

      <div className="mt-6 text-center text-sm text-sand-600">
        {t('auth.noAccount')} <Link to="/inscription" className="text-terracotta-700 font-medium">{t('auth.createAccount')}</Link>
      </div>

      <div className="mt-8 border-t border-sand-200 pt-5">
        <div className="text-xs uppercase tracking-widest text-sand-500 mb-2">{t('auth.demoQuickAccess')}</div>
        <div className="grid grid-cols-3 gap-2">
          <button onClick={()=>quick('expert')} className="btn-secondary text-xs">{t('auth.demoExpert')}</button>
          <button onClick={()=>quick('chercheur')} className="btn-secondary text-xs">{t('auth.demoResearcher')}</button>
          <button onClick={()=>quick('admin')} className="btn-secondary text-xs">{t('auth.demoAdmin')}</button>
        </div>
      </div>
    </div>
  )
}
