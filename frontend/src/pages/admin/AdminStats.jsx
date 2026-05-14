import { useEffect, useMemo, useState } from 'react'
import { TrendingUp, Users as UsersIcon, FolderKanban, FileCheck2, Loader2 } from 'lucide-react'
import { adminApi, heritage } from '../../lib/api.js'

export default function AdminStats() {
  const [users, setUsers] = useState([])
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([adminApi.users(), heritage.projects()])
      .then(([u, p]) => {
        setUsers(Array.isArray(u) ? u : (u.results || []))
        setProjects(Array.isArray(p) ? p : (p.results || []))
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const counters = useMemo(() => ({
    projects: projects.length,
    users: users.length,
    experts: users.filter(u => u.role === 'expert').length,
    pending: users.filter(u => (u.role === 'expert' && !u.is_validated) || u.account_status === 'pending').length,
    published: projects.filter(p => p.status === 'published').length,
  }), [users, projects])

  const byRegion = useMemo(() => {
    const m = {}
    projects.forEach(p => {
      const w = p.resource?.wilaya || '—'
      m[w] = (m[w] || 0) + 1
    })
    return Object.entries(m).sort((a,b) => b[1]-a[1]).slice(0, 8)
  }, [projects])

  const byStatus = useMemo(() => {
    const labels = { draft:'Brouillon', in_progress:'En cours', published:'Publié', archived:'Archivé' }
    const colors = { draft:'#3e2417', in_progress:'#bd7d3d', published:'#cd5028', archived:'#824c2b' }
    const m = {}
    projects.forEach(p => { m[p.status] = (m[p.status] || 0) + 1 })
    const total = projects.length || 1
    return Object.entries(m).map(([k,v]) => ({
      l: labels[k] || k, v: Math.round((v/total)*100), n: v, c: colors[k] || '#3e2417'
    }))
  }, [projects])

  if (loading) {
    return (
      <div className="text-sand-600 inline-flex items-center gap-2">
        <Loader2 size={14} className="animate-spin"/>Chargement...
      </div>
    )
  }
  if (error) return <div className="card p-3 text-red-700 bg-red-50 text-sm">{error}</div>

  return (
    <div className="space-y-6">
      <div>
        <h1 className="section-title">Statistiques globales</h1>
        <p className="section-subtitle">Suivi de la performance et de l'activité de la plateforme.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { l:'Projets', v: counters.projects, i: FolderKanban },
          { l:'Utilisateurs', v: counters.users, i: UsersIcon },
          { l:'Experts validés', v: counters.experts, i: FileCheck2 },
          { l:'Validations en attente', v: counters.pending, i: TrendingUp },
        ].map((s,i) => (
          <div key={i} className="card p-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-terracotta-50 text-terracotta-700 grid place-items-center"><s.i size={20}/></div>
              <div>
                <div className="text-xs uppercase tracking-widest text-sand-500">{s.l}</div>
                <div className="text-2xl font-semibold">{s.v}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        <section className="card p-5 lg:col-span-2">
          <h3 className="font-semibold">Projets par statut</h3>
          <ul className="mt-4 space-y-3">
            {byStatus.length === 0 && <li className="text-sand-500 text-sm">Aucune donnée.</li>}
            {byStatus.map(d => (
              <li key={d.l}>
                <div className="flex justify-between text-sm">
                  <span>{d.l}</span><span className="font-medium">{d.n} ({d.v}%)</span>
                </div>
                <div className="h-2 mt-1 bg-sand-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width:`${d.v}%`, background:d.c }}/>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="card p-5">
          <h3 className="font-semibold">Top régions</h3>
          <ul className="mt-4 space-y-2">
            {byRegion.length === 0 && <li className="text-sand-500 text-sm">Aucune donnée.</li>}
            {byRegion.map(([r, n]) => (
              <li key={r} className="flex justify-between text-sm border-b border-sand-100 py-1">
                <span>{r}</span><span className="font-medium">{n}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
