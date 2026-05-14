import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Check, X, Trash2, Sparkles } from 'lucide-react'

/**
 * Click-and-drag rectangle annotator over an image.
 *
 * Geometry storage: every rectangle is saved as
 *   geometry_json = { type: "rect", x, y, w, h }
 * with all four numbers normalized to [0..1] of the natural image size.
 * That way zooming, responsive resize, and high-DPI screens never shift
 * an annotation off its anchor.
 *
 * Annotations are color-coded by the author's discipline (`color_hex`),
 * matching the same scheme used in the editor sidebar legend.
 *
 * The component is read+write: existing AI annotations show a small
 * "✨ IA" pill and validate/reject buttons; the author of a manual
 * annotation can also delete it.
 */
export default function MediaAnnotator({
  mediaId,
  src,
  annotations,
  onCreate,        // ({ geometry_json, body_text }) => Promise
  onValidate,      // (annotationId) => Promise
  onReject,        // (annotationId) => Promise — AI rejection (deletes)
  onDelete,        // (annotationId) => Promise — manual delete
  currentUserId,
}) {
  const { t } = useTranslation()
  const wrapRef = useRef(null)
  const [drag, setDrag] = useState(null)        // { x0, y0, x1, y1 } in normalized [0..1]
  const [pending, setPending] = useState(null)  // { x, y, w, h } awaiting label

  // Keep selection cleared whenever the underlying media changes — otherwise a
  // half-drawn rectangle from media A would leak onto media B.
  useEffect(() => { setDrag(null); setPending(null) }, [mediaId, src])

  const toNorm = (e) => {
    const rect = wrapRef.current.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    return {
      x: Math.max(0, Math.min(1, x)),
      y: Math.max(0, Math.min(1, y)),
    }
  }

  const onDown = (e) => {
    if (pending) return
    e.preventDefault()
    const p = toNorm(e)
    setDrag({ x0: p.x, y0: p.y, x1: p.x, y1: p.y })
  }

  const onMove = (e) => {
    if (!drag) return
    const p = toNorm(e)
    setDrag({ ...drag, x1: p.x, y1: p.y })
  }

  const onUp = () => {
    if (!drag) return
    const x = Math.min(drag.x0, drag.x1)
    const y = Math.min(drag.y0, drag.y1)
    const w = Math.abs(drag.x1 - drag.x0)
    const h = Math.abs(drag.y1 - drag.y0)
    setDrag(null)
    // Reject ghost rectangles (a single click without a real drag).
    if (w < 0.01 || h < 0.01) return
    setPending({ x, y, w, h })
  }

  const submitPending = async (text) => {
    if (!pending) return
    const trimmed = (text || '').trim()
    if (!trimmed) { setPending(null); return }
    try {
      await onCreate({
        geometry_json: { type: 'rect', x: pending.x, y: pending.y, w: pending.w, h: pending.h },
        body_text: trimmed,
      })
    } finally {
      setPending(null)
    }
  }

  const dragRect = drag
    ? rectStyleFromCorners(drag.x0, drag.y0, drag.x1, drag.y1)
    : null

  return (
    <div className="space-y-3">
      <div
        ref={wrapRef}
        onMouseDown={onDown}
        onMouseMove={onMove}
        onMouseUp={onUp}
        onMouseLeave={onUp}
        className="relative inline-block w-full select-none cursor-crosshair bg-sand-100 rounded-lg overflow-hidden"
      >
        <img
          src={src}
          alt=""
          className="block w-full h-auto pointer-events-none"
          draggable={false}
        />
        {/* live drag rectangle */}
        {dragRect && (
          <div
            className="absolute border-2 border-terracotta-600 bg-terracotta-600/15 pointer-events-none"
            style={dragRect}
          />
        )}
        {/* persisted annotations */}
        {(annotations || []).map((a) => {
          const g = a.geometry_json || {}
          if (g.type !== 'rect') return null
          const color = a.discipline?.color_hex || '#cd5028'
          const validated = a.is_validated
          const ai = a.is_ai_generated
          return (
            <div
              key={a.id}
              title={a.body_text}
              className={`absolute group/box ${validated ? '' : 'animate-pulse'}`}
              style={{
                left: `${g.x * 100}%`,
                top: `${g.y * 100}%`,
                width: `${g.w * 100}%`,
                height: `${g.h * 100}%`,
                border: `2px solid ${color}`,
                background: `${color}22`,
              }}
            >
              <span
                className="absolute top-0 -translate-y-full text-[10px] px-1.5 py-0.5 rounded text-white whitespace-nowrap inline-flex items-center gap-1"
                style={{ background: color, insetInlineStart: 0 }}
              >
                {ai && <Sparkles size={10}/>}
                {a.body_text || '—'}
              </span>
            </div>
          )
        })}
      </div>

      {/* label prompt for the rectangle just drawn */}
      {pending && (
        <PendingForm
          onSubmit={submitPending}
          onCancel={() => setPending(null)}
          placeholder={t('annotator.labelPlaceholder')}
        />
      )}

      {/* annotations side list with validate / reject / delete */}
      <ul className="space-y-1.5">
        {(annotations || []).length === 0 && (
          <li className="text-sm text-sand-500">{t('annotator.empty')}</li>
        )}
        {(annotations || []).map((a) => {
          const color = a.discipline?.color_hex || '#cd5028'
          const isOwn = a.author?.id === currentUserId
          return (
            <li key={a.id} className="flex items-center gap-2 text-sm bg-sand-50 border border-sand-100 rounded px-2 py-1.5">
              <span
                className="inline-block w-3 h-3 rounded-sm flex-shrink-0"
                style={{ background: color }}
              />
              <span className="flex-1 truncate">
                {a.body_text || '—'}
                <span className="text-xs text-sand-500 ms-2">
                  {a.author?.full_name || a.author?.email || '—'}
                  {a.is_ai_generated && (
                    <span className="ms-2 text-amber-700 inline-flex items-center gap-1">
                      <Sparkles size={10}/>IA
                    </span>
                  )}
                  {!a.is_validated && (
                    <span className="ms-2 text-amber-700">{t('annotator.toValidate')}</span>
                  )}
                </span>
              </span>
              {a.is_ai_generated && !a.is_validated && (
                <>
                  <button onClick={() => onValidate(a.id)} className="btn-ghost text-emerald-700" title={t('annotator.validate')}>
                    <Check size={14}/>
                  </button>
                  <button onClick={() => onReject(a.id)} className="btn-ghost text-red-700" title={t('annotator.reject')}>
                    <X size={14}/>
                  </button>
                </>
              )}
              {!a.is_ai_generated && isOwn && (
                <button onClick={() => onDelete(a.id)} className="btn-ghost text-red-700" title={t('common.delete')}>
                  <Trash2 size={14}/>
                </button>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function rectStyleFromCorners(x0, y0, x1, y1) {
  const left = Math.min(x0, x1) * 100
  const top = Math.min(y0, y1) * 100
  const width = Math.abs(x1 - x0) * 100
  const height = Math.abs(y1 - y0) * 100
  return {
    left: `${left}%`,
    top: `${top}%`,
    width: `${width}%`,
    height: `${height}%`,
  }
}

function PendingForm({ onSubmit, onCancel, placeholder }) {
  const { t } = useTranslation()
  const [text, setText] = useState('')
  return (
    <form
      onSubmit={(e) => { e.preventDefault(); onSubmit(text) }}
      className="flex items-center gap-2"
    >
      <input
        autoFocus
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        className="input flex-1"
      />
      <button type="submit" className="btn-primary text-sm">{t('common.save')}</button>
      <button type="button" onClick={onCancel} className="btn-ghost text-sm">{t('common.cancel')}</button>
    </form>
  )
}
