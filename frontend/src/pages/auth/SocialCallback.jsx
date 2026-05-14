import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useAuth } from '../../context/AuthContext.jsx'

/**
 * OAuth provider callback page.
 *
 * The provider redirects here with `?code=...` (or `?error=...` on denial).
 * We hand the code to the backend, which exchanges it for a profile, creates
 * or links the User, and returns a SimpleJWT pair.
 *
 * Mounted twice in the router under /auth/google/callback and /auth/github/callback.
 */
export default function SocialCallback() {
  const { provider } = useParams()
  const [params] = useSearchParams()
  const { loginWithSocial } = useAuth()
  const nav = useNavigate()
  const [status, setStatus] = useState('loading') // loading | error
  const [message, setMessage] = useState('')
  const ran = useRef(false)

  useEffect(() => {
    // StrictMode mounts twice in dev — don't burn the OAuth code.
    if (ran.current) return
    ran.current = true

    const error = params.get('error')
    if (error) {
      setStatus('error')
      setMessage(params.get('error_description') || error)
      return
    }
    const code = params.get('code')
    if (!code) {
      setStatus('error')
      setMessage('Code OAuth manquant.')
      return
    }
    const redirect_uri = `${window.location.origin}/auth/${provider}/callback`
    loginWithSocial(provider, code, redirect_uri).then((ok) => {
      if (ok) nav('/app/tableau-de-bord', { replace: true })
      else { setStatus('error'); setMessage('La connexion a échoué.') }
    })
  }, [params, provider, loginWithSocial, nav])

  if (status === 'loading') {
    return (
      <div className="text-center py-10">
        <Loader2 size={32} className="animate-spin mx-auto text-terracotta-600" />
        <p className="mt-4 text-sand-600">Connexion via {provider}…</p>
      </div>
    )
  }
  return (
    <div className="text-center py-10">
      <h2 className="text-lg font-semibold text-red-700">Connexion impossible</h2>
      <p className="mt-2 text-sm text-sand-600">{message}</p>
      <button onClick={() => nav('/connexion', { replace: true })} className="btn-secondary mt-4">
        Retour à la connexion
      </button>
    </div>
  )
}
