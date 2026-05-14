import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search as SearchIcon, Folder, Loader2, X } from 'lucide-react'
import { heritage } from '../../lib/api.js'
import { PERIODS, TYPES } from '../../data/projects.js'

// Maps for translating facet keys (raw enum values) to French labels.
const PERIOD_LABEL = Object.fromEntries(PERIODS.map(p => [p.value, p.label]))
const TYPE_LABEL = Object.fromEntries(TYPES.map(t => [t.value, t.label]))
const CLASSIF_LABEL = {
  unesco: 'UNESCO',
  national: 'National',
  regional: 'Régional',
  unclassified: 'Non classé',
}

// Render an array of highlight HTML fragments (already wrapped in <mark>).
// Safe because the backend controls the markup (only <mark>...</mark> + text).
function Highlight({ fragments }) {
  if (!fragments || fragments.length === 0) return null
  return (
    <div
      className="text-sm text-sand-700 mt-1 line-clamp-2"
      dangerouslySetInnerHTML={{ __html: fragments.join(' … ') }}
    />
  )
}

function FacetGroup({ title, name, buckets, selected, onToggle, labelMap }) {
  if (!buckets || buckets.length === 0) return null
  return (
    <div className="border-t border-sand-200 pt-3 first:border-t-0 first:pt-0">
      <div className="text-xs font-semibold uppercase tracking-wide text-sand-500 mb-2">{title}</div>
      <ul className="space-y-1">
        {buckets.map(b => {
          const isSel = selected.includes(b.key)
          return (
            <li key={b.key}>
              <button
                type="button"
                onClick={() => onToggle(name, b.key)}
                className={`w-full flex items-center justify-between text-left px-2 py-1 rounded text-sm hover:bg-sand-100 ${isSel ? 'bg-clay-100 text-clay-900 font-medium' : 'text-sand-700'}`}
              >
                <span className="flex items-center gap-2">
                  {isSel && <X size={12} />}
                  {labelMap?.[b.key] || b.key}
                </span>
                <span className="text-xs text-sand-500">{b.count}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default function AdvancedSearch() {
  const [q, setQ] = useState('')
  const [filters, setFilters] = useState({
    period: [], architectural_type: [], classification_level: [], wilaya: [],
  })
  const [data, setData] = useState({ total: 0, results: [], facets: {} })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Suggest (autocomplete)
  const [suggestions, setSuggestions] = useState([])
  const [showSuggest, setShowSuggest] = useState(false)
  const suggestTimer = useRef(null)

  const params = useMemo(() => ({ q, ...filters, size: 30 }), [q, filters])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    const t = setTimeout(() => {
      heritage.search(params)
        .then((res) => { if (!cancelled) setData(res) })
        .catch((e) => { if (!cancelled) setError(e.message) })
        .finally(() => { if (!cancelled) setLoading(false) })
    }, 250)
    return () => { cancelled = true; clearTimeout(t) }
  }, [params])

  // Autocomplete: debounced suggest on input change (only while typing in the field)
  function onQueryChange(value) {
    setQ(value)
    if (suggestTimer.current) clearTimeout(suggestTimer.current)
    if (!value || value.length < 2) { setSuggestions([]); return }
    suggestTimer.current = setTimeout(() => {
      heritage.suggest(value, 8)
        .then(setSuggestions)
        .catch(() => setSuggestions([]))
    }, 150)
  }

  function toggleFacet(name, value) {
    setFilters(prev => {
      const cur = prev[name] || []
      return { ...prev, [name]: cur.includes(value) ? cur.filter(v => v !== value) : [...cur, value] }
    })
  }

  function clearFilters() {
    setFilters({ period: [], architectural_type: [], classification_level: [], wilaya: [] })
  }

  const activeCount = Object.values(filters).reduce((s, v) => s + v.length, 0)

  return (
    <div className="space-y-5">
      <div>
        <h1 className="section-title">Recherche avancée</h1>
        <p className="section-subtitle">
          Recherche plein texte multilingue (FR + AR) avec facettes — propulsée par Elasticsearch.
        </p>
      </div>

      {/* Search bar with autocomplete */}
      <div className="card p-5 relative">
        <label className="label">Recherche</label>
        <div className="relative">
          <SearchIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-sand-400" />
          <input
            value={q}
            onChange={e => onQueryChange(e.target.value)}
            onFocus={() => setShowSuggest(true)}
            onBlur={() => setTimeout(() => setShowSuggest(false), 150)}
            className="input pl-9"
            placeholder="Mots-clés... (Casbah, mosquée, قصبة, ...)"
          />
        </div>
        {showSuggest && suggestions.length > 0 && (
          <ul className="absolute left-5 right-5 top-[88px] z-10 bg-white border border-sand-200 rounded-lg shadow-lg max-h-64 overflow-auto">
            {suggestions.map(s => (
              <li key={s.id}>
                <button
                  type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => { setQ(s.text); setSuggestions([]); setShowSuggest(false) }}
                  className="w-full text-left px-3 py-2 hover:bg-sand-50 text-sm flex items-center gap-2"
                >
                  <SearchIcon size={12} className="text-sand-400" />
                  {s.text}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="grid lg:grid-cols-12 gap-5">
        {/* Facets sidebar */}
        <aside className="lg:col-span-3 card p-4 h-fit space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-sm">Filtres</h3>
            {activeCount > 0 && (
              <button onClick={clearFilters} className="text-xs text-clay-700 hover:underline">
                Réinitialiser ({activeCount})
              </button>
            )}
          </div>
          <FacetGroup title="Période" name="period" buckets={data.facets?.period}
                      selected={filters.period} onToggle={toggleFacet} labelMap={PERIOD_LABEL} />
          <FacetGroup title="Type" name="architectural_type" buckets={data.facets?.architectural_type}
                      selected={filters.architectural_type} onToggle={toggleFacet} labelMap={TYPE_LABEL} />
          <FacetGroup title="Classement" name="classification_level" buckets={data.facets?.classification_level}
                      selected={filters.classification_level} onToggle={toggleFacet} labelMap={CLASSIF_LABEL} />
          <FacetGroup title="Wilaya" name="wilaya" buckets={data.facets?.wilaya}
                      selected={filters.wilaya} onToggle={toggleFacet} />
        </aside>

        {/* Results */}
        <section className="lg:col-span-9 card p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2">
              <Folder size={18} />Ressources <span className="text-sand-500 font-normal">({data.total ?? 0})</span>
            </h3>
            {loading && <Loader2 size={14} className="animate-spin text-sand-500" />}
          </div>

          {error && <div className="mt-3 p-3 rounded bg-red-50 text-red-700 text-sm">{error}</div>}

          {!loading && data.total === 0 && (
            <div className="text-sand-500 text-sm mt-4">Aucun résultat.</div>
          )}

          <ul className="mt-3 divide-y divide-sand-100">
            {data.results.map(r => (
              <li key={r.id}>
                <Link to={`/explorer/${r.id}`} className="block py-3 px-2 rounded-lg hover:bg-sand-50">
                  <div className="font-medium"
                       dangerouslySetInnerHTML={{
                         __html: r.highlight?.name_fr?.[0] || r.name_fr || '',
                       }} />
                  {r.name_ar && (
                    <div className="text-sm text-sand-500" dir="rtl"
                         dangerouslySetInnerHTML={{ __html: r.highlight?.name_ar?.[0] || r.name_ar }} />
                  )}
                  <div className="text-xs text-sand-500 mt-0.5">
                    {r.wilaya}{r.commune ? ` · ${r.commune}` : ''}
                    {r.period ? ` · ${PERIOD_LABEL[r.period] || r.period}` : ''}
                    {r.architectural_type ? ` · ${TYPE_LABEL[r.architectural_type] || r.architectural_type}` : ''}
                  </div>
                  <Highlight fragments={r.highlight?.description} />
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
