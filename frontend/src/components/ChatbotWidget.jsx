/**
 * Floating chatbot widget — anonymous, public-facing.
 *
 * Used on PublicLayout pages (Home / Explorer / project pages). Stores its
 * session id and anon key in localStorage so the visitor's history persists
 * across page reloads without an account.
 */
import { useEffect, useRef, useState } from 'react'
import { Bot, MessageCircle, Send, User as UserIcon, X } from 'lucide-react'
import { chat } from '../lib/api.js'

const ANON_KEY_STORAGE = 'pfe.chat.anon_key'
const SESSION_KEY_STORAGE = 'pfe.chat.session_id'

function getOrCreateAnonKey() {
  let k = localStorage.getItem(ANON_KEY_STORAGE)
  if (!k) {
    k = 'anon_' + Math.random().toString(36).slice(2, 10) + Date.now().toString(36)
    localStorage.setItem(ANON_KEY_STORAGE, k)
  }
  return k
}

const SUGGESTIONS = [
  "Sites UNESCO en Algérie ?",
  "Architecture du M'Zab",
  "Casbah d'Alger",
]

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Bonjour ! Posez-moi une question sur le patrimoine architectural algérien." },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const sessionIdRef = useRef(Number(localStorage.getItem(SESSION_KEY_STORAGE)) || null)
  const endRef = useRef(null)

  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending, open])

  const send = async (text) => {
    const q = (text ?? input).trim()
    if (!q || sending) return
    setError('')
    setMessages((m) => [...m, { role: 'user', content: q }])
    setInput('')
    setSending(true)
    try {
      const data = await chat.ask(q, {
        sessionId: sessionIdRef.current || undefined,
        anonKey: getOrCreateAnonKey(),
      })
      sessionIdRef.current = data.session_id
      localStorage.setItem(SESSION_KEY_STORAGE, String(data.session_id))
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: data.assistant_message.content,
          citations: data.assistant_message.citations || [],
        },
      ])
    } catch (e) {
      const msg = e.status === 429
        ? "Vous avez atteint la limite de questions par heure. Revenez un peu plus tard."
        : "Désolé, une erreur est survenue. Réessayez dans un instant."
      setError(msg)
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-5 right-5 z-40 bg-terracotta-600 hover:bg-terracotta-700 text-white rounded-full shadow-lg w-14 h-14 grid place-items-center transition"
        aria-label={open ? 'Fermer le chatbot' : 'Ouvrir le chatbot'}
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>

      {open && (
        <div className="fixed bottom-24 right-5 z-40 w-[360px] max-w-[calc(100vw-2rem)] h-[520px] max-h-[calc(100vh-7rem)] bg-white rounded-2xl shadow-2xl border border-sand-200 flex flex-col overflow-hidden">
          <div className="bg-terracotta-600 text-white px-4 py-3 flex items-center gap-2">
            <Bot size={18} />
            <div className="flex-1">
              <div className="font-semibold leading-tight">Assistant Patrimoine</div>
              <div className="text-xs text-terracotta-100">Réponses basées sur la base documentaire</div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3 scrollbar-thin">
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-2 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-7 h-7 rounded-full grid place-items-center text-white flex-shrink-0 ${m.role === 'user' ? 'bg-sand-700' : 'bg-terracotta-600'}`}>
                  {m.role === 'user' ? <UserIcon size={14} /> : <Bot size={14} />}
                </div>
                <div className={`max-w-[80%] px-3 py-2 rounded-2xl text-sm whitespace-pre-wrap ${m.role === 'user' ? 'bg-terracotta-600 text-white' : 'bg-sand-50 border border-sand-200'}`}>
                  {m.content}
                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-sand-200/70 text-xs space-y-1">
                      <div className="font-semibold text-sand-700">Sources :</div>
                      {m.citations.map((c) => (
                        <a
                          key={c.id}
                          href={c.url_path || '#'}
                          className="block text-terracotta-700 hover:underline truncate"
                          title={c.title}
                        >
                          • {c.title}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex gap-2">
                <div className="w-7 h-7 rounded-full bg-terracotta-600 grid place-items-center text-white"><Bot size={14} /></div>
                <div className="px-3 py-2 rounded-2xl bg-sand-50 border border-sand-200 flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-sand-400 animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-sand-400 animate-bounce [animation-delay:120ms]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-sand-400 animate-bounce [animation-delay:240ms]" />
                </div>
              </div>
            )}
            {error && <div className="text-xs text-red-600 px-1">{error}</div>}
            <div ref={endRef} />
          </div>

          <div className="border-t border-sand-200 p-2 space-y-2">
            {messages.length <= 1 && (
              <div className="flex flex-wrap gap-1.5">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="text-xs px-2 py-1 rounded-full bg-sand-100 hover:bg-sand-200 text-sand-700 transition"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
            <form onSubmit={(e) => { e.preventDefault(); send() }} className="flex gap-1.5">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={sending}
                className="input flex-1 text-sm"
                placeholder="Posez votre question..."
              />
              <button
                type="submit"
                disabled={sending || !input.trim()}
                className="btn-primary px-3 disabled:opacity-50"
                aria-label="Envoyer"
              >
                <Send size={14} />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
