import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, Activity, Loader2 } from 'lucide-react'
import { projectToCard } from '../../data/projects.js'
import StatusBadge from '../../components/StatusBadge.jsx'
import { heritage } from '../../lib/api.js'

export default function AdminProjects() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [busyId, setBusyId] = useState(null)

  const load = () => {
    setLoading(true)
    heritage.projects()
      .then((data) => {
        const list = Array.isArray(data) ? data : (data.results || [])
        setItems(list.map(projectToCard))
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const publish = async (id) => {
    setBusyId(id)
    try { await heritage.publish(id); load() }
    catch (e) { alert(e.message) }
    finally { setBusyId(null) }
  }

  const stats = {
    total: items.length,
    published: items.filter(p => p.status === 'published').length,
    in_progress: items.filter(p => p.status === 'in_progress').length,
    draft: items.filter(p => p.status === 'draft').length,
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="section-title">Gestion des projets</h1>
        <p className="section-subtitle">Validez les contenus, suivez l'activité.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { l:'Total', v: stats.total },
          { l:'Publiés', v: stats.published, c:'text-emerald-600' },
          { l:'En cours', v: stats.in_progress, c:'text-amber-600' },
          { l:'Brouillons', v: stats.draft, c:'text-sand-600' },
        ].map((s,i) => (
          <div key={i} className="card p-5">
            <div className="text-xs uppercase tracking-widest text-sand-500">{s.l}</div>
            <div className={`text-3xl font-semibold mt-1 ${s.c||''}`}>{s.v}</div>
          </div>
        ))}
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
                <th className="text-left px-4 py-3">Projet</th>
                <th className="text-left px-4 py-3">Région</th>
                <th className="text-left px-4 py-3">Période</th>
                <th className="text-left px-4 py-3">Contributeurs</th>
                <th className="text-left px-4 py-3">MAJ</th>
                <th className="text-left px-4 py-3">Statut</th>
                <th className="text-right px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map(p => (
                <tr key={p.id} className="border-t border-sand-100 hover:bg-sand-50/60">
                  <td className="px-4 py-3">
                    <Link to={`/app/projets/${p.id}`} className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg" style={{background:`linear-gradient(135deg, ${p.coverColor}, #3e2417)`}}/>
                      <div>
                        <div className="font-medium">{p.name}</div>
                        <div className="text-xs text-sand-500">{p.type}</div>
                      </div>
                    </Link>
                  </td>
                  <td className="px-4 py-3">{p.region}</td>
                  <td className="px-4 py-3">{p.period}</td>
                  <td className="px-4 py-3">{p.contributors?.length ?? 0}</td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-1 text-sand-600 text-xs">
                      <Activity size={14}/>{p.updatedAt ? new Date(p.updatedAt).toLocaleDateString('fr-FR') : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={p.status}/></td>
                  <td className="px-4 py-3 text-right">
                    <div className="inline-flex gap-1">
                      {p.status !== 'published' && (
                        <button title="Publier" disabled={busyId===p.id}
                                onClick={()=>publish(p.id)}
                                className="p-1.5 rounded hover:bg-emerald-100 text-emerald-700 disabled:opacity-50">
                          <CheckCircle2 size={16}/>
                        </button>
                      )}
                      {busyId===p.id && <Loader2 size={14} className="animate-spin text-sand-500"/>}
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-sand-500">Aucun projet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
