import { useEffect, useRef, useState } from 'react'
import { Send, Bot, User as UserIcon, Sparkles, Plus, Trash2, MessageSquare } from 'lucide-react'
import { chat } from '../../lib/api.js'

const SUGGESTIONS = [
  "Quels sont les monuments ottomans documentés sur la plateforme ?",
  "Donne-moi les caractéristiques de la Qalâa des Béni Hammad",
  "Liste les sites UNESCO en Algérie",
  "Quelles sont les caractéristiques du M'Zab ?",
]

const WELCOME = {
  role: 'assistant',
  content: "Bonjour ! Je suis votre assistant documentaire. Posez-moi une question sur le patrimoine architectural algérien.",
}

export default function Chatbot() {
  const [sessions, setSessions] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const endRef = useRef(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, sending])

  const loadSessions = async () => {
    try {
      const data = await chat.sessions()
      setSessions(data?.results || data || [])
    } catch { /* ignore */ }
  }

  useEffect(() => { loadSessions() }, [])

  const openSession = async (id) => {
    try {
      const s = await chat.session(id)
      setActiveId(id)
      const msgs = (s.messages || []).map(m => ({
        role: m.role,
        content: m.content,
        citations: m.citations || [],
      }))
      setMessages(msgs.length ? msgs : [WELCOME])
    } catch {
      setError("Impossible de charger cette conversation.")
    }
  }

  const newChat = () => {
    setActiveId(null)
    setMessages([WELCOME])
    setError('')
  }

  const removeSession = async (id, e) => {
    e.stopPropagation()
    if (!confirm("Supprimer cette conversation ?")) return
    try {
      await chat.deleteSession(id)
      if (activeId === id) newChat()
      loadSessions()
    } catch {
      setError("Suppression impossible.")
    }
  }

  const send = async (text) => {
    const q = (text ?? input).trim()
    if (!q || sending) return
    setError('')
    setMessages(m => [...m, { role: 'user', content: q }])
    setInput('')
    setSending(true)
    try {
      const data = await chat.ask(q, { sessionId: activeId || undefined })
      if (!activeId) {
        setActiveId(data.session_id)
        loadSessions()
      }
      setMessages(m => [...m, {
        role: 'assistant',
        content: data.assistant_message.content,
        citations: data.assistant_message.citations || [],
      }])
    } catch (e) {
      const msg = e.status === 429
        ? "Vous avez atteint la limite de questions par heure."
        : "Une erreur est survenue. Réessayez."
      setError(msg)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="section-title flex items-center gap-2"><Bot/>Chatbot documentaire</h1>
        <p className="section-subtitle">Posez vos questions ; les réponses sont basées sur les contenus de la plateforme.</p>
      </div>

      <div className="grid md:grid-cols-[260px_1fr] gap-4 h-[70vh]">
        <aside className="card flex flex-col overflow-hidden">
          <div className="p-3 border-b border-sand-200">
            <button onClick={newChat} className="btn-primary w-full"><Plus size={14}/>Nouvelle conversation</button>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-thin">
            {sessions.length === 0 && (
              <div className="p-3 text-xs text-sand-500">Aucune conversation enregistrée.</div>
            )}
            {sessions.map(s => (
              <button
                key={s.id}
                onClick={() => openSession(s.id)}
                className={`w-full text-left px-3 py-2 border-b border-sand-100 hover:bg-sand-50 flex items-start gap-2 group ${activeId === s.id ? 'bg-sand-100' : ''}`}
              >
                <MessageSquare size={14} className="mt-0.5 text-sand-500 flex-shrink-0"/>
                <span className="flex-1 text-sm truncate">{s.title || 'Conversation'}</span>
                <span
                  onClick={(e) => removeSession(s.id, e)}
                  className="opacity-0 group-hover:opacity-100 text-sand-400 hover:text-red-600"
                  role="button"
                  aria-label="Supprimer"
                >
                  <Trash2 size={14}/>
                </span>
              </button>
            ))}
          </div>
        </aside>

        <div className="card flex flex-col">
          <div className="flex-1 overflow-y-auto p-5 space-y-4 scrollbar-thin">
            {messages.map((m,i) => (
              <div key={i} className={`flex gap-3 ${m.role==='user'?'flex-row-reverse':''}`}>
                <div className={`w-8 h-8 rounded-full grid place-items-center text-white flex-shrink-0 ${m.role==='user'?'bg-sand-700':'bg-terracotta-600'}`}>
                  {m.role==='user' ? <UserIcon size={16}/> : <Bot size={16}/>}
                </div>
                <div className={`max-w-[75%] px-4 py-2.5 rounded-2xl whitespace-pre-wrap ${m.role==='user'?'bg-terracotta-600 text-white':'bg-sand-50 border border-sand-200'}`}>
                  {m.content}
                  {m.citations && m.citations.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-sand-200/70 text-xs space-y-1">
                      <div className="font-semibold text-sand-700">Sources :</div>
                      {m.citations.map(c => (
                        <a key={c.id} href={c.url_path || '#'} className="block text-terracotta-700 hover:underline truncate" title={c.title}>
                          • {c.title}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-terracotta-600 grid place-items-center text-white"><Bot size={16}/></div>
                <div className="px-4 py-2.5 rounded-2xl bg-sand-50 border border-sand-200 flex gap-1">
                  <span className="w-2 h-2 rounded-full bg-sand-400 animate-bounce"/>
                  <span className="w-2 h-2 rounded-full bg-sand-400 animate-bounce [animation-delay:120ms]"/>
                  <span className="w-2 h-2 rounded-full bg-sand-400 animate-bounce [animation-delay:240ms]"/>
                </div>
              </div>
            )}
            {error && <div className="text-sm text-red-600">{error}</div>}
            <div ref={endRef}/>
          </div>

          <div className="p-3 border-t border-sand-200 space-y-2">
            {messages.length <= 1 && (
              <div className="flex flex-wrap gap-2">
                {SUGGESTIONS.map(s => (
                  <button key={s} onClick={()=>send(s)} className="chip bg-sand-100 hover:bg-sand-200 text-sand-700 cursor-pointer">
                    <Sparkles size={12}/>{s}
                  </button>
                ))}
              </div>
            )}
            <form onSubmit={(e)=>{e.preventDefault(); send()}} className="flex gap-2">
              <input
                value={input}
                onChange={e=>setInput(e.target.value)}
                disabled={sending}
                className="input flex-1"
                placeholder="Posez votre question..."
              />
              <button type="submit" disabled={sending || !input.trim()} className="btn-primary disabled:opacity-50">
                <Send size={16}/>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
