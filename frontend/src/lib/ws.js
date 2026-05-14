/**
 * WebSocket client for /ws/notifications/.
 * Reconnects with backoff. Token is sent in the URL query string
 * because browsers don't support custom WS headers.
 */
import { tokens } from './api'

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export function openNotificationsSocket(onMessage) {
  let ws = null
  let stopped = false
  let backoff = 1000

  function connect() {
    if (stopped) return
    const token = tokens.access
    const url = `${WS_BASE}/ws/notifications/${token ? `?token=${encodeURIComponent(token)}` : ''}`
    ws = new WebSocket(url)

    ws.onopen = () => { backoff = 1000 }
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data)
        if (data.type === 'notification' && onMessage) onMessage(data.data)
      } catch (_) { /* ignore */ }
    }
    ws.onclose = () => {
      if (stopped) return
      setTimeout(connect, backoff)
      backoff = Math.min(backoff * 2, 15000)
    }
    ws.onerror = () => { try { ws.close() } catch (_) {} }
  }

  connect()

  return () => {
    stopped = true
    try { ws?.close() } catch (_) {}
  }
}
