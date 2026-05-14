import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'

const VARIANTS = {
  success: {
    icon: CheckCircle2,
    ring: 'border-emerald-200',
    bg: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
    title: 'text-emerald-900',
  },
  error: {
    icon: AlertCircle,
    ring: 'border-red-200',
    bg: 'bg-red-50',
    iconColor: 'text-red-600',
    title: 'text-red-900',
  },
  info: {
    icon: Info,
    ring: 'border-sand-200',
    bg: 'bg-white',
    iconColor: 'text-sand-600',
    title: 'text-sand-900',
  },
}

const AUTO_DISMISS_MS = 5000

/**
 * Single toast card. Slides in from the inline-end edge, auto-dismisses after 5s.
 * Variant: success | error | info (defaults to info).
 */
export function Toast({ id, type = 'info', title, body, onDismiss }) {
  const [entered, setEntered] = useState(false)
  const variant = VARIANTS[type] || VARIANTS.info
  const Icon = variant.icon

  useEffect(() => {
    // Trigger slide-in on next tick so the transition runs.
    const raf = requestAnimationFrame(() => setEntered(true))
    const t = setTimeout(() => onDismiss?.(id), AUTO_DISMISS_MS)
    return () => { cancelAnimationFrame(raf); clearTimeout(t) }
  }, [id, onDismiss])

  return (
    <div
      role="status"
      aria-live="polite"
      className={[
        'pointer-events-auto w-80 max-w-[92vw] rounded-lg border shadow-lg',
        variant.bg,
        variant.ring,
        'transform transition-all duration-300 ease-out',
        entered ? 'translate-x-0 opacity-100' : 'rtl:-translate-x-4 ltr:translate-x-4 opacity-0',
      ].join(' ')}
    >
      <div className="flex items-start gap-3 p-3">
        <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${variant.iconColor}`} aria-hidden="true" />
        <div className="min-w-0 flex-1">
          {title && <p className={`text-sm font-semibold ${variant.title}`}>{title}</p>}
          {body && <p className="mt-0.5 text-sm text-slate-700 break-words">{body}</p>}
        </div>
        <button
          type="button"
          onClick={() => onDismiss?.(id)}
          className="shrink-0 rounded p-1 text-slate-400 hover:bg-black/5 hover:text-slate-700"
          aria-label="Fermer"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}

/**
 * Container that renders a stack of toasts into document.body via portal.
 * Positioned with `end-4` (RTL-aware) so it sits on the inline-end edge.
 */
export function ToastContainer({ toasts, onDismiss }) {
  if (typeof document === 'undefined') return null
  return createPortal(
    <div
      className="pointer-events-none fixed top-4 end-4 z-[1000] flex flex-col gap-2"
      aria-label="Notifications"
    >
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onDismiss={onDismiss} />
      ))}
    </div>,
    document.body,
  )
}

export default Toast
