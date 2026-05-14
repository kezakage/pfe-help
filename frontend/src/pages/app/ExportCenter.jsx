import { useEffect, useState } from 'react'
import { FileText, Download, Printer, FileImage, Settings2, Loader2 } from 'lucide-react'
import { heritage, exports_, mediaUrl } from '../../lib/api.js'
import { projectToCard } from '../../data/projects.js'

export default function ExportCenter() {
  const [projects, setProjects] = useState([])
  const [recent, setRecent] = useState([])
  const [project, setProject] = useState('')
  const [format, setFormat] = useState('pdf')
  const [opts, setOpts] = useState({ images: true, annotations: true, sources: true, history: false })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const set = (k) => () => setOpts({ ...opts, [k]: !opts[k] })

  const loadRecent = () => {
    exports_.list()
      .then((data) => setRecent(Array.isArray(data) ? data : (data.results || [])))
      .catch(() => {})
  }

  useEffect(() => {
    heritage.projects()
      .then((data) => {
        const list = (Array.isArray(data) ? data : (data.results || [])).map(projectToCard)
        setProjects(list)
        if (list.length > 0) setProject(list[0].id)
      })
      .catch((e) => setError(e.message))
    loadRecent()
  }, [])

  const p = projects.find(x => x.id === project)

  const generate = async () => {
    if (!project) return
    setSubmitting(true)
    setError(null)
    try {
      await exports_.create({
        project,
        format,
        options: opts,
      })
      loadRecent()
    } catch (e) {
      setError(e.data ? JSON.stringify(e.data) : e.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="section-title flex items-center gap-2"><Download/>Export & impression</h1>
        <p className="section-subtitle">Générez des documents scientifiques téléchargeables.</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 card p-6 space-y-5">
          <div>
            <label className="label">Projet à exporter</label>
            <select className="input" value={project} onChange={e=>setProject(e.target.value)}>
              {projects.length === 0 && <option value="">Aucun projet disponible</option>}
              {projects.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}
            </select>
          </div>

          <div>
            <label className="label">Format</label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { k:'pdf', l:'PDF scientifique', i: FileText },
                { k:'print', l:'Version imprimable', i: Printer },
                { k:'archive', l:'Archive (ZIP)', i: FileImage },
              ].map(o => (
                <button key={o.k} onClick={()=>setFormat(o.k)}
                        className={`p-4 rounded-lg border ${format===o.k?'border-terracotta-500 bg-terracotta-50':'border-sand-200 hover:border-sand-300'}`}>
                  <o.i className="mx-auto text-terracotta-700" size={22}/>
                  <div className="text-sm font-medium mt-1">{o.l}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="label flex items-center gap-1"><Settings2 size={14}/>Contenu inclus</label>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {[
                { k:'images', l:"Galerie d'images" },
                { k:'annotations', l:'Annotations' },
                { k:'sources', l:'Sources & bibliographie' },
                { k:'history', l:'Historique des versions' },
              ].map(o => (
                <label key={o.k} className="flex items-center gap-2 p-3 rounded-lg border border-sand-200 cursor-pointer hover:bg-sand-50">
                  <input type="checkbox" checked={opts[o.k]} onChange={set(o.k)}/>
                  <span className="text-sm">{o.l}</span>
                </label>
              ))}
            </div>
          </div>

          {error && <div className="card p-3 text-red-700 bg-red-50 text-sm">{error}</div>}

          <button onClick={generate} disabled={submitting || !project} className="btn-primary w-full">
            {submitting ? <Loader2 size={16} className="animate-spin"/> : <Download size={16}/>} Générer le document
          </button>
        </div>

        <aside className="card p-5">
          <h3 className="font-semibold">Aperçu</h3>
          <div className="mt-3 aspect-[3/4] rounded-lg bg-white border border-sand-200 p-4 text-xs text-sand-700 overflow-hidden">
            {p ? (
              <>
                <div className="border-b border-sand-200 pb-2 mb-2">
                  <div className="text-[10px] uppercase tracking-widest text-sand-500">Patrimoine.dz</div>
                  <div className="font-display text-base font-semibold">{p.name}</div>
                  <div className="text-[10px]">{p.region} • {p.period} • {p.type}</div>
                </div>
                <div className="space-y-1">
                  <div className="font-medium">Description</div>
                  <p className="line-clamp-6">{p.description || p.summary || '—'}</p>
                </div>
              </>
            ) : (
              <div className="text-sand-400 text-center mt-10">Sélectionnez un projet</div>
            )}
          </div>
        </aside>
      </div>

      <section className="card p-5">
        <h3 className="font-semibold mb-3">Exports récents</h3>
        {recent.length === 0 && <div className="text-sand-500 text-sm">Aucun export pour le moment.</div>}
        <ul className="divide-y divide-sand-100">
          {recent.map((f) => (
            <li key={f.id} className="py-3 flex items-center gap-3">
              <FileText size={18} className="text-terracotta-700"/>
              <div className="flex-1">
                <div className="font-medium text-sm">{f.filename || `export_${f.id}.${f.format || 'pdf'}`}</div>
                <div className="text-xs text-sand-500">
                  {f.created_at ? new Date(f.created_at).toLocaleString('fr-FR') : ''} • {f.status || ''}
                </div>
              </div>
              {f.file && (
                <a href={mediaUrl(f.file)} target="_blank" rel="noreferrer" className="btn-secondary text-sm">
                  <Download size={14}/>
                </a>
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
