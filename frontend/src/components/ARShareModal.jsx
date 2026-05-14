// Modal showing a QR code that points to the public AR viewer for a given
// 3D media. Lets a desktop visitor scan with their phone to launch
// Scene Viewer (Android) / WebXR / AR Quick Look — no install required.
//
// Pure presentational: parent owns open/close state.

import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import { QRCodeSVG } from 'qrcode.react'
import { X, Smartphone, Copy, CheckCircle2 } from 'lucide-react'
import { useState } from 'react'

export default function ARShareModal({ open, onClose, mediaId, caption }) {
  const [copied, setCopied] = useState(false)

  // ESC closes the modal — standard a11y for dismissible dialogs.
  useEffect(() => {
    if (!open) return
    const onKey = (e) => { if (e.key === 'Escape') onClose?.() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open || typeof document === 'undefined' || !mediaId) return null

  // Build the absolute URL — must be reachable from the phone, so we use the
  // current origin. In dev that's localhost (only same-LAN devices work);
  // in prod it's the real domain served behind nginx.
  const url = `${window.location.origin}/ar/model/${mediaId}`

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch (_) { /* clipboard not available — ignore */ }
  }

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="ar-share-title"
      className="fixed inset-0 z-[1100] grid place-items-center bg-black/60 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-sm rounded-xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <h3 id="ar-share-title" className="font-semibold inline-flex items-center gap-2">
            <Smartphone size={18} aria-hidden="true" />
            <span>Voir en réalité augmentée</span>
          </h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fermer"
            className="rounded p-1 text-sand-500 hover:bg-sand-100"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-4 space-y-3 text-center">
          <p className="text-sm text-sand-600">
            Scannez ce QR code avec votre téléphone pour ouvrir le modèle 3D
            et lancer l’aperçu en RA (Android / iOS récents).
          </p>

          <div className="mx-auto inline-block rounded-lg bg-white p-3 ring-1 ring-sand-200">
            {/* level=M offers a good size/error-correction balance for screens */}
            <QRCodeSVG value={url} size={196} level="M" includeMargin={false} />
          </div>

          {caption && (
            <p className="text-xs text-sand-500 truncate" title={caption}>{caption}</p>
          )}

          <div className="flex items-center gap-2 rounded border border-sand-200 bg-sand-50 px-2 py-1.5">
            <code className="flex-1 truncate text-xs text-sand-700 text-left" title={url}>{url}</code>
            <button
              type="button"
              onClick={copy}
              className="shrink-0 inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-terracotta-700 hover:bg-terracotta-50"
              aria-label="Copier le lien"
            >
              {copied ? <CheckCircle2 size={14} /> : <Copy size={14} />}
              {copied ? 'Copié' : 'Copier'}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}
