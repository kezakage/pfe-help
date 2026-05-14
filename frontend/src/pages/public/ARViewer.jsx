// Public AR viewer — full-screen <model-viewer> for a single Media (model_3d).
// Designed to be opened from a phone by scanning the QR code shown in the
// project workspace. No auth required: the media endpoint is read-public
// (DRF IsAuthenticatedOrReadOnly).

import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, Box, AlertCircle, Loader2 } from 'lucide-react'
import Model3DViewer from '../../components/Model3DViewer.jsx'
import { media as mediaApi, mediaUrl } from '../../lib/api.js'

export default function ARViewer() {
  const { id } = useParams()
  const { t } = useTranslation()
  const [item, setItem] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    mediaApi.retrieve(id)
      .then((m) => {
        if (cancelled) return
        if (m?.media_type !== 'model_3d') {
          setError(t('ar.errorNotModel'))
        } else {
          setItem(m)
        }
      })
      .catch(() => { if (!cancelled) setError(t('ar.errorLoad')) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [id, t])

  return (
    <div className="fixed inset-0 bg-slate-900 text-white flex flex-col" data-testid="ar-viewer">
      <header className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <Link to="/" className="inline-flex items-center gap-2 text-sm text-white/80 hover:text-white">
          <ArrowLeft size={16} aria-hidden="true" />
          <span>{t('ar.back')}</span>
        </Link>
        <span className="inline-flex items-center gap-2 text-sm font-semibold">
          <Box size={16} aria-hidden="true" />
          {t('ar.title')}
        </span>
        <span className="w-16" aria-hidden="true" />
      </header>

      <main className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 grid place-items-center text-white/70">
            <Loader2 className="animate-spin" size={32} aria-label={t('ar.loading')} />
          </div>
        )}

        {!loading && error && (
          <div className="absolute inset-0 grid place-items-center p-6 text-center">
            <div>
              <AlertCircle size={40} className="mx-auto text-red-300" aria-hidden="true" />
              <p className="mt-3 text-base text-red-200" role="alert">{error}</p>
              <Link to="/" className="mt-4 inline-block underline text-white/80">
                {t('ar.back')}
              </Link>
            </div>
          </div>
        )}

        {!loading && !error && item && (
          <div className="absolute inset-0">
            <Model3DViewer
              src={mediaUrl(item.file_url)}
              alt={item.caption || t('ar.title')}
              className="!rounded-none"
            />
            <div className="absolute bottom-4 inset-x-4 text-center text-sm text-white/80 pointer-events-none">
              <p className="font-semibold text-white">{item.caption || `Modèle #${item.id}`}</p>
              <p className="mt-1">{t('ar.tapARButton')}</p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
