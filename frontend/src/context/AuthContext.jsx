import { createContext, useContext, useEffect, useState } from 'react'
import { auth, tokens } from '../lib/api'

const AuthContext = createContext(null)

function userToAvatar(u) {
  const fn = (u.first_name || '').trim()
  const ln = (u.last_name || '').trim()
  if (fn || ln) return ((fn[0] || '') + (ln[0] || '')).toUpperCase() || u.email.slice(0, 2).toUpperCase()
  return (u.email || 'U').slice(0, 2).toUpperCase()
}

function normalize(u) {
  if (!u) return null
  return {
    id: u.id,
    email: u.email,
    first_name: u.first_name,
    last_name: u.last_name,
    name: `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.email,
    role: u.role,
    status: u.status,
    validated: u.status === 'active',
    institution: u.institution_name || '',
    bio: u.bio || '',
    discipline: (u.disciplines && u.disciplines[0]?.name_fr) || '—',
    disciplines: u.disciplines || [],
    avatar: userToAvatar(u),
    is_validated_expert: u.is_validated_expert,
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    if (!tokens.access) {
      setLoading(false)
      return () => {}
    }
    auth.me()
      .then((u) => { if (!cancelled) setUser(normalize(u)) })
      .catch(() => { if (!cancelled) { tokens.clear(); setUser(null) } })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const login = async (email, password) => {
    setError(null)
    try {
      const data = await auth.login(email, password)
      tokens.set(data.access, data.refresh)
      const u = data.user || await auth.me()
      setUser(normalize(u))
      return true
    } catch (e) {
      setError(e.data?.detail || e.message || 'Échec de connexion')
      return false
    }
  }

  const register = async (data) => {
    setError(null)
    try {
      // Map UI fields → backend fields
      const payload = {
        email: data.email,
        password: data.password,
        first_name: data.first_name || (data.name || '').split(' ')[0] || '',
        last_name: data.last_name || (data.name || '').split(' ').slice(1).join(' ') || '',
        requested_role: data.role === 'expert' ? 'expert' : 'researcher',
        institution_name: data.institution || '',
        bio: data.bio || '',
        discipline_ids: data.discipline_ids || [],
      }
      await auth.register(payload)
      // Auto-login only if researcher (experts are PENDING and cannot log in until validated)
      if (payload.requested_role === 'researcher') {
        const ok = await login(data.email, data.password)
        return ok
      }
      return true
    } catch (e) {
      setError(e.data?.detail || JSON.stringify(e.data || {}) || 'Échec de l\'inscription')
      return false
    }
  }

  const logout = () => {
    tokens.clear()
    setUser(null)
  }

  /**
   * SSO login. Called from the OAuth callback page after the provider has
   * redirected back with a `code`. Backend swaps the code for tokens against
   * the provider, links/creates the User, returns a SimpleJWT pair.
   */
  const loginWithSocial = async (provider, code, redirect_uri) => {
    setError(null)
    try {
      const data = await auth.socialLogin(provider, code, redirect_uri)
      const access = data.access || data.access_token
      const refresh = data.refresh || data.refresh_token
      if (!access) throw new Error('No access token returned')
      tokens.set(access, refresh)
      const u = data.user || await auth.me()
      setUser(normalize(u))
      return true
    } catch (e) {
      setError(e.data?.detail || e.data?.error || e.message || 'Échec de la connexion sociale')
      return false
    }
  }

  /**
   * Quick login as a demo persona (uses seeded users from `seed_demo_users`).
   * Maps the old role keys (expert/chercheur/admin) to real demo accounts.
   */
  const loginAs = async (role) => {
    const presets = {
      expert: ['expert@patrimoine.dz', 'Expert12345!'],
      chercheur: ['chercheur@patrimoine.dz', 'Chercheur12345!'],
      admin: ['admin@patrimoine.dz', 'Admin12345!'],
    }
    const creds = presets[role] || presets.chercheur
    return login(creds[0], creds[1])
  }

  return (
    <AuthContext.Provider value={{ user, loading, error, login, loginAs, loginWithSocial, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
