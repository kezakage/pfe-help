import { useEffect, useMemo, useState } from 'react'
import { Search, ShieldCheck, ShieldX, Pause, Loader2 } from 'lucide-react'
import { adminApi } from '../../lib/api.js'

const STATUS_CHIP = {
  active: 'bg-emerald-100 text-emerald-800',
  pending: 'bg-amber-100 text-amber-800',
  suspended: 'bg-red-100 text-red-800',
  rejected: 'bg-sand-200 text-sand-700',
}
const STATUS_LABEL = {
  active: 'Actif',
  pending: 'En attente',
  suspended: 'Suspendu',
  rejected: 'Refusé',
}

function statusOf(u) {
  if (u.is_suspended) return 'suspended'
  if (u.account_status === 'rejected') return 'rejected'
  if (u.role === 'expert' && !u.is_validated) return 'pending'
  if (u.account_status === 'pending') return 'pending'
  return 'active'
}

export default function AdminUsers() {
  const [tab, setTab] = useState('tous')
  const [q, setQ] = useState('')
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [busyId, setBusyId] = useState(null)

  const load = () => {
    setLoading(true)
    adminApi.users()
      .then((data) => setUsers(Array.isArray(data) ? data : (data.results || [])))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const list = useMemo(() => {
    return users
      .map((u) => ({ ...u, _status: statusOf(u) }))
      .filter((u) => {
        if (tab === 'attente' && u._status !== 'pending') return false
        if (tab === 'experts' && u.role !== 'expert') return false
        if (q) {
          const hay = (u.full_name || u.email || '').toLowerCase()
          if (!hay.includes(q.toLowerCase())) return false
        }
        return true
      })
  }, [users, tab, q])

  const act = async (id, fn) => {
    setBusyId(id)
    try { await fn(); load() }
    catch (e) { alert(e.message) }
    finally { setBusyId(null) }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="section-title">Gestion des utilisateurs</h1>
        <p className="section-subtitle">Validez les profils experts, gérez les rôles et l'accès.</p>
      </div>

      <div className="flex flex-wrap gap-2 items-center">
        {[
          { k:'tous', l:'Tous' }, { k:'attente', l:'En attente de validation' }, { k:'experts', l:'Experts' }
        ].map(t => (
          <button key={t.k} onClick={()=>setTab(t.k)}
                  className={`chip ${tab===t.k?'bg-terracotta-600 text-white':'bg-sand-100 text-sand-700'} cursor-pointer`}>{t.l}</button>
        ))}
        <div className="ml-auto relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-sand-400"/>
          <input value={q} onChange={e=>setQ(e.target.value)} className="input pl-9" placeholder="Rechercher..."/>
        </div>
      </div>

      {loading && (
        <div className="text-sand-600 inline-flex items-center gap-2">
          <Loader2 size={14} className="animate-spin"/>Chargement...
        </div>
      )}
      {error && <div className="card p-3 text-red-700 bg-red-50 text-sm">{error}</div>}

      {!loading && !error && (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-sand-50">
              <tr>
                <th className="text-left px-4 py-3">Utilisateur</th>
                <th className="text-left px-4 py-3">Rôle</th>
                <th className="text-left px-4 py-3">Discipline</th>
                <th className="text-left px-4 py-3">Institution</th>
                <th className="text-left px-4 py-3">Statut</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {list.map(u => {
                const name = u.full_name || `${u.first_name||''} ${u.last_name||''}`.trim() || u.email
                const initials = name.split(' ').map(s=>s[0]).filter(Boolean).slice(0,2).join('').toUpperCase()
                const disciplines = (u.disciplines || []).map(d => d.name_fr || d.name).join(', ')
                return (
                  <tr key={u.id} className="border-t border-sand-100 hover:bg-sand-50/60">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-terracotta-600 text-white grid place-items-center text-xs font-semibold">{initials}</div>
                        <div>
                          <div className="font-medium">{name}</div>
                          <div className="text-xs text-sand-500">{u.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 capitalize">{u.role}</td>
                    <td className="px-4 py-3">{disciplines || '—'}</td>
                    <td className="px-4 py-3">{u.institution_name || '—'}</td>
                    <td className="px-4 py-3">
                      <span className={`chip ${STATUS_CHIP[u._status]}`}>{STATUS_LABEL[u._status]}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="inline-flex gap-1">
                        {u._status === 'pending' && (
                          <>
                            <button title="Valider" disabled={busyId===u.id}
                                    onClick={()=>act(u.id, ()=>adminApi.validateUser(u.id, 'approve'))}
                                    className="p-1.5 rounded hover:bg-emerald-100 text-emerald-700 disabled:opacity-50">
                              <ShieldCheck size={16}/>
                            </button>
                            <button title="Refuser" disabled={busyId===u.id}
                                    onClick={()=>act(u.id, ()=>adminApi.validateUser(u.id, 'reject'))}
                                    className="p-1.5 rounded hover:bg-red-100 text-red-700 disabled:opacity-50">
                              <ShieldX size={16}/>
                            </button>
                          </>
                        )}
                        {u._status === 'active' && (
                          <button title="Suspendre" disabled={busyId===u.id}
                                  onClick={()=>act(u.id, ()=>adminApi.suspend(u.id))}
                                  className="p-1.5 rounded hover:bg-amber-100 text-amber-700 disabled:opacity-50">
                            <Pause size={16}/>
                          </button>
                        )}
                        {busyId===u.id && <Loader2 size={14} className="animate-spin text-sand-500"/>}
                      </div>
                    </td>
                  </tr>
                )
              })}
              {list.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-sand-500">Aucun utilisateur.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
