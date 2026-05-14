import { useEffect, useState } from 'react'
import { Loader2, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { pages as pagesApi } from '../lib/api.js'

/**
 * Visual unified diff between two PageVersions.
 *
 * Calls the existing `/pages/versions/diff/?a=&b=` endpoint, which returns a
 * `unified_diff` line-by-line. We classify lines (`+` add / `-` remove /
 * ` ` context / `@@` hunk) and render them in a code-style block with the
 * usual red/green coloring. This is a lightweight diff — sufficient for the
 * MFE "Git-like visual diff" deliverable; a future version could swap in
 * `diff-match-patch` semantic chunks.
 */
function classify(line) {
  if (!line) return 'ctx'
  if (line.startsWith('+++') || line.startsWith('---')) return 'meta'
  if (line.startsWith('@@')) return 'hunk'
  if (line.startsWith('+')) return 'add'
  if (line.startsWith('-')) return 'del'
  return 'ctx'
}

export default function VersionDiff({ a, b, onClose }) {
  const { t } = useTranslation()
  const [lines, setLines] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLines(null); setError(null)
    pagesApi.diff(a, b)
      .then((res) => { if (!cancelled) setLines(res?.diff || []) })
      .catch((e) => { if (!cancelled) setError(e.message) })
    return () => { cancelled = true }
  }, [a, b])

  return (
    <div className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4" onClick={onClose}>
      <div className="card max-w-3xl w-full max-h-[80vh] flex flex-col overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="px-5 py-3 border-b border-sand-200 flex items-center justify-between">
          <h3 className="font-semibold">{t('projects.diff.title')}</h3>
          <button onClick={onClose} className="btn-ghost"><X size={16}/></button>
        </div>
        <div className="flex-1 overflow-auto bg-sand-50">
          {!lines && !error && (
            <div className="p-6 text-sand-600 inline-flex items-center gap-2">
              <Loader2 className="animate-spin" size={14}/>{t('common.loading')}
            </div>
          )}
          {error && <div className="p-5 text-red-700">{error}</div>}
          {lines && lines.length === 0 && (
            <div className="p-6 text-sand-500 text-sm">{t('projects.diff.identical')}</div>
          )}
          {lines && lines.length > 0 && (
            <pre className="text-xs leading-5 font-mono">
              {lines.map((ln, i) => {
                const k = classify(ln)
                const cls =
                  k === 'add' ? 'bg-emerald-50 text-emerald-900' :
                  k === 'del' ? 'bg-red-50 text-red-900' :
                  k === 'hunk' ? 'bg-sand-200 text-sand-700' :
                  k === 'meta' ? 'bg-sand-100 text-sand-600' :
                  'text-sand-700'
                return (
                  <div key={i} className={`px-4 py-0.5 ${cls}`}>{ln || ' '}</div>
                )
              })}
            </pre>
          )}
        </div>
      </div>
    </div>
  )
}
