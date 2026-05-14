import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Search, Grid as GridIcon, List as ListIcon, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { projectToCard } from '../../data/projects.js'
import StatusBadge from '../../components/StatusBadge.jsx'
import ProjectCard from '../../components/ProjectCard.jsx'
import { heritage } from '../../lib/api.js'

export default function ProjectsList() {
  const { t } = useTranslation()
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')
  const [view, setView] = useState('grid')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    heritage.projects({
      search: q || undefined,
      status: status || undefined,
    })
      .then((data) => {
        if (cancelled) return
        const list = Array.isArray(data) ? data : (data.results || [])
        setItems(list.map(projectToCard))
      })
      .catch((e) => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [q, status])

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="section-title">{t('projects.title')}</h1>
          <p className="section-subtitle">{t('projects.subtitle')}</p>
        </div>
        <Link to="/app/projets/nouveau" className="btn-primary"><Plus size={16}/>{t('projects.newProject')}</Link>
      </div>

      <div className="card p-4 flex flex-wrap gap-3 items-end">
        <div className="flex-1 min-w-[240px]">
          <label className="label">{t('projects.searchLabel')}</label>
          <div className="relative">
            <Search size={16} className="absolute start-3 top-1/2 -translate-y-1/2 text-sand-400"/>
            <input value={q} onChange={e=>setQ(e.target.value)} className="input ps-9" placeholder={t('projects.searchPlaceholder')}/>
          </div>
        </div>
        <div>
          <label className="label">{t('projects.status')}</label>
          <select value={status} onChange={e=>setStatus(e.target.value)} className="input min-w-[160px]">
            <option value="">{t('projects.statusAll')}</option>
            <option value="draft">{t('projects.statusDraft')}</option>
            <option value="in_progress">{t('projects.statusInProgress')}</option>
            <option value="published">{t('projects.statusPublished')}</option>
            <option value="archived">{t('projects.statusArchived')}</option>
          </select>
        </div>
        <div className="inline-flex bg-sand-50 rounded-lg border border-sand-200 p-1">
          <button onClick={()=>setView('grid')} className={`btn ${view==='grid'?'bg-white shadow':'text-sand-600'}`}><GridIcon size={16}/></button>
          <button onClick={()=>setView('list')} className={`btn ${view==='list'?'bg-white shadow':'text-sand-600'}`}><ListIcon size={16}/></button>
        </div>
      </div>

      {loading && (
        <div className="text-sand-600 inline-flex items-center gap-2">
          <Loader2 size={14} className="animate-spin"/>{t('projects.loading')}
        </div>
      )}
      {error && <div className="card p-4 text-red-700 bg-red-50">{t('projects.errorPrefix')} {error}</div>}

      {!loading && !error && items.length === 0 && (
        <div className="card p-10 text-center text-sand-600">
          {t('projects.emptyHint')}
        </div>
      )}

      {view === 'grid' ? (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">
          {items.map(p => <ProjectCard key={p.id} project={p} to={`/app/projets/${p.id}`}/>)}
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-sand-50 text-sand-700">
              <tr>
                <th className="text-start px-4 py-3">{t('projects.table.project')}</th>
                <th className="text-start px-4 py-3">{t('projects.table.region')}</th>
                <th className="text-start px-4 py-3">{t('projects.table.period')}</th>
                <th className="text-start px-4 py-3">{t('projects.table.type')}</th>
                <th className="text-start px-4 py-3">{t('projects.table.status')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map(p => (
                <tr key={p.id} className="border-t border-sand-100 hover:bg-sand-50">
                  <td className="px-4 py-3">
                    <Link to={`/app/projets/${p.id}`} className="font-medium hover:text-terracotta-700">{p.name}</Link>
                  </td>
                  <td className="px-4 py-3">{p.region}</td>
                  <td className="px-4 py-3">{p.period}</td>
                  <td className="px-4 py-3">{p.type}</td>
                  <td className="px-4 py-3"><StatusBadge status={p.status}/></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
