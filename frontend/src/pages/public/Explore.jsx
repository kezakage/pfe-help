import { useEffect, useState } from 'react'
import { Search, List, Map as MapIcon, X, Loader2 } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { PERIODS, TYPES, REGIONS, resourceToCard } from '../../data/projects.js'
import ProjectCard from '../../components/ProjectCard.jsx'
import MapView from '../../components/MapView.jsx'
import { heritage } from '../../lib/api.js'

export default function Explore() {
  const { t } = useTranslation()
  const [q, setQ] = useState('')
  const [period, setPeriod] = useState('')
  const [region, setRegion] = useState('')
  const [type, setType] = useState('')
  const [view, setView] = useState('list')

  const [items, setItems] = useState([])
  const [features, setFeatures] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    const filters = {
      search: q || undefined,
      period: period || undefined,
      wilaya: region || undefined,
      architectural_type: type || undefined,
    }
    Promise.all([
      heritage.resources(filters),
      heritage.geojson(filters),
    ])
      .then(([data, geo]) => {
        if (cancelled) return
        const list = Array.isArray(data) ? data : (data.results || [])
        setItems(list.map(resourceToCard))
        setFeatures(geo?.features || [])
      })
      .catch((e) => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [q, period, region, type])

  const reset = () => { setQ(''); setPeriod(''); setRegion(''); setType('') }

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="section-title">{t('explore.title')}</h1>
          <p className="section-subtitle">{t('explore.subtitle')}</p>
        </div>
        <div className="inline-flex bg-white rounded-lg border border-sand-200 p-1">
          <button onClick={() => setView('list')} className={`btn ${view==='list'?'bg-terracotta-600 text-white':'text-sand-700'}`}><List size={16}/>{t('explore.viewList')}</button>
          <button onClick={() => setView('map')} className={`btn ${view==='map'?'bg-terracotta-600 text-white':'text-sand-700'}`}><MapIcon size={16}/>{t('explore.viewMap')}</button>
        </div>
      </div>

      <div className="card p-4 mt-6 grid md:grid-cols-12 gap-3 items-end">
        <div className="md:col-span-4">
          <label className="label">{t('explore.searchLabel')}</label>
          <div className="relative">
            <Search size={16} className="absolute start-3 top-1/2 -translate-y-1/2 text-sand-400"/>
            <input value={q} onChange={e=>setQ(e.target.value)} className="input ps-9" placeholder={t('explore.searchPlaceholder')}/>
          </div>
        </div>
        <div className="md:col-span-2">
          <label className="label">{t('explore.period')}</label>
          <select value={period} onChange={e=>setPeriod(e.target.value)} className="input">
            <option value="">{t('explore.allFem')}</option>
            {PERIODS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
        </div>
        <div className="md:col-span-2">
          <label className="label">{t('explore.region')}</label>
          <select value={region} onChange={e=>setRegion(e.target.value)} className="input">
            <option value="">{t('explore.allFem')}</option>
            {REGIONS.map(r => <option key={r}>{r}</option>)}
          </select>
        </div>
        <div className="md:col-span-3">
          <label className="label">{t('explore.architecturalType')}</label>
          <select value={type} onChange={e=>setType(e.target.value)} className="input">
            <option value="">{t('explore.allMasc')}</option>
            {TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>
        <div className="md:col-span-1">
          <button onClick={reset} className="btn-secondary w-full"><X size={16}/></button>
        </div>
      </div>

      <div className="mt-4 text-sm text-sand-600">
        {loading
          ? <span className="inline-flex items-center gap-2"><Loader2 size={14} className="animate-spin"/>{t('explore.loading')}</span>
          : t('explore.resultsFound', { count: items.length })}
      </div>

      {error && <div className="mt-3 card p-4 text-red-700 bg-red-50">{t('explore.errorPrefix')} {error}</div>}

      <div className="mt-4">
        {view === 'list' ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {items.map(p => <ProjectCard key={p.id} project={p}/>)}
            {!loading && items.length === 0 && (
              <div className="col-span-full card p-10 text-center text-sand-600">
                {t('explore.noResults')}
              </div>
            )}
          </div>
        ) : (
          <MapView features={features}/>
        )}
      </div>
    </div>
  )
}
