import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { notifications as notifApi } from '../lib/api.js'
import { openNotificationsSocket } from '../lib/ws.js'
import { useAuth } from './AuthContext.jsx'
import { ToastContainer } from '../components/Toast.jsx'

const Ctx = createContext(null)

function normalize(n) {
  return {
    id: n.id,
    type: n.kind || n.type || 'systeme',
    title: n.title || 'Notification',
    body: n.body || n.message || '',
    date: n.created_at || n.date || new Date().toISOString(),
    read: n.is_read ?? n.read ?? false,
    payload: n.payload || null,
  }
}

// Map a backend Notification.Type to a toast visual variant.
function toastVariant(notifType) {
  switch (notifType) {
    case 'expert_validated':
    case 'version_published':
    case 'annotation_validated':
    case 'export_ready':
      return 'success'
    case 'expert_rejected':
      return 'error'
    default:
      return 'info'
  }
}

export function NotificationsProvider({ children }) {
  const { user } = useAuth() || {}
  const [items, setItems] = useState([])
  const [toasts, setToasts] = useState([])
  const toastSeq = useRef(0)
  const unread = items.filter(n => !n.read).length

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const addToast = useCallback((payload) => {
    const id = `t-${Date.now()}-${++toastSeq.current}`
    setToasts((prev) => [
      ...prev,
      {
        id,
        type: toastVariant(payload?.type || payload?.kind),
        title: payload?.title || 'Notification',
        body: payload?.body || payload?.message || '',
      },
    ])
  }, [])

  useEffect(() => {
    if (!user) { setItems([]); setToasts([]); return }
    let cancelled = false
    notifApi.list()
      .then((data) => {
        if (cancelled) return
        const list = Array.isArray(data) ? data : (data.results || [])
        setItems(list.map(normalize))
      })
      .catch(() => {})

    const close = openNotificationsSocket((payload) => {
      setItems((prev) => [normalize(payload), ...prev])
      addToast(payload)
    })

    return () => { cancelled = true; close() }
  }, [user?.id, addToast])

  const markAllRead = async () => {
    setItems((prev) => prev.map(n => ({ ...n, read: true })))
    try { await notifApi.markAllRead() } catch (_) {}
  }

  const markRead = async (id) => {
    setItems((prev) => prev.map(n => n.id === id ? { ...n, read: true } : n))
    try { await notifApi.markRead(id) } catch (_) {}
  }

  const push = (n) => setItems(prev => [normalize({ id: 'local-' + Date.now(), ...n }), ...prev])

  return (
    <Ctx.Provider value={{ items, unread, markAllRead, markRead, push, addToast }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </Ctx.Provider>
  )
}

export const useNotifications = () => useContext(Ctx)
