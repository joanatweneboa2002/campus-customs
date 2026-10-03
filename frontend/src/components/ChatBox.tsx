import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import Bulldog from './Bulldog'
import { formatPrice } from '../types'
import { BUDDY_RESULTS_PATH, useBuddyResults, type ChatProductCard, type PageResults } from '../buddyResults'
import { useAuth, type User } from '../auth'
import { stockBadge } from '../stock'
import { OPEN_BUDDY_EVENT } from '../buddyEvents'

interface Message {
  role: 'user' | 'assistant'
  content: string
  products?: ChatProductCard[]
  page?: PageResults // set when this reply put results on the page
}

// Mirrors backend/models.py ChatReply
interface ChatReply {
  reply: string
  products: ChatProductCard[]
  page_results: PageResults | null
}

function greeting(user: User | null): Message {
  return {
    role: 'assistant',
    content: user
      ? `Welcome back, ${user.first_name}! 🐾 Our chats are saved to your account, so pick up right where we left off.`
      : "Woof! 🐾 I'm Buddy. Tell me what you're hunting for and I'll sniff it out.",
  }
}
// Suggested questions change with the page, so they're always relevant to what's on screen.
// (Nothing in the shop is under $25 — the cheapest item is $32 — so the budget example uses $40.)
function suggestionsFor(path: string, user: User | null): string[] {
  if (/^\/products\/[^/]+$/.test(path)) {
    return ['Is this in stock in M?', 'What colors does this come in?', 'Show me something similar', 'Is this a good gift?']
  }
  if (path.includes('view=buddy')) {
    return ['Only the ones under $60', 'Which of these come in L?', 'Show me these in gray', 'Something cheaper?']
  }
  const base = ["What's under $40?", 'Navy hoodie in size M', 'Gift for my grandpa', 'Anything for Branford?', 'What do you sell?']
  return user ? ['What did we talk about last time?', ...base] : base
}
const HISTORY_TURNS = 10 // guests only: how many earlier messages the backend gets for context

// A fresh chat per person: logging in or out remounts the chat with that person's greeting/history.
export default function ChatBox() {
  const { user, token, ready } = useAuth()
  if (!ready) return null
  return <Chat key={user?.id ?? 'guest'} user={user} token={token} />
}

function Chat({ user, token }: { user: User | null; token: string | null }) {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([greeting(user)])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const location = useLocation()
  const buddyResults = useBuddyResults()

  // "Ask Buddy" buttons elsewhere on the site open the chat.
  useEffect(() => {
    const show = () => setOpen(true)
    window.addEventListener(OPEN_BUDDY_EVENT, show)
    return () => window.removeEventListener(OPEN_BUDDY_EVENT, show)
  }, [])

  // Logged in: load the saved conversation from the customer_chat_history table.
  useEffect(() => {
    if (!user || !token) return
    fetch('/api/chat/history', { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : []))
      .then((saved: (Message & { page_results: PageResults | null })[]) =>
        setMessages([
          greeting(user),
          ...saved.map((m) => ({ role: m.role, content: m.content, products: m.products, page: m.page_results ?? undefined })),
        ]),
      )
      .catch(() => {})
  }, [user, token])

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, thinking, open])

  async function send(text: string) {
    const message = text.trim()
    if (!message || thinking) return
    // Guests: send recent turns (skipping the greeting) as context. Logged-in customers:
    // the server loads their saved history itself, so nothing needs to be sent.
    const history = user
      ? []
      : messages
          .slice(1)
          .slice(-HISTORY_TURNS)
          .map(({ role, content }) => ({ role, content }))
    // Where the shopper is, so "do you have this in pink?" means the product on screen.
    const productId = location.pathname.match(/^\/products\/([^/]+)$/)?.[1]
    const page = { path: location.pathname + location.search, product_id: productId ? decodeURIComponent(productId) : null }

    setMessages((m) => [...m, { role: 'user', content: message }])
    setInput('')
    setThinking(true)
    try {
      const r = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ message: message.slice(0, 1000), history, page }),
      })
      if (!r.ok) throw new Error(String(r.status))
      const data: ChatReply = await r.json()
      const results = data.page_results
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: data.reply,
          products: data.products,
          page: results ?? undefined,
        },
      ])
      // Search results go to the actual page: the Products page shows them as big cards.
      if (results && results.products.length > 0) {
        buddyResults.show(results)
        navigate(BUDDY_RESULTS_PATH)
      }
    } catch {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: "Hmm, I can't reach my brain right now. Is the backend running? 🐾" },
      ])
    } finally {
      setThinking(false)
    }
  }

  if (!open) {
    return (
      <button className="chat-toggle" onClick={() => setOpen(true)} aria-label="Open chat">
        <Bulldog size={34} />
        <span>Ask Buddy!</span>
      </button>
    )
  }

  return (
    <div className="chat-box">
      <div className="chat-header">
        <Bulldog size={30} />
        <div>
          <strong>Buddy the Bulldog</strong>
          <small>
            {thinking ? 'typing…' : user ? `💾 Saved to ${user.first_name}'s account` : 'Guest · log in to save this chat'}
          </small>
        </div>
        <button onClick={() => setOpen(false)} aria-label="Close chat">✕</button>
      </div>

      <div className="chat-body" ref={bodyRef}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-row ${m.role}`}>
            <div className={`chat-msg ${m.role === 'user' ? 'me' : 'bot'}`}>{m.content}</div>
            {m.page && (
              <button
                className="chat-page-link"
                onClick={() => {
                  buddyResults.show(m.page!)
                  navigate(BUDDY_RESULTS_PATH)
                }}
              >
                🐾 See all {m.page.products.length} on the page →
              </button>
            )}
            {m.products && m.products.length > 0 && (
              <div className="chat-cards">
                {m.products.map((p) => (
                  <Link key={p.id} to={p.url} className="chat-card">
                    <img src={p.image_url} alt={p.name} />
                    <div>
                      <strong>{p.name}</strong>
                      <span>
                        {formatPrice(p.price)} · {stockBadge(p.total_stock, p.sizes)?.label ?? 'In stock'}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
        {thinking && (
          <div className="chat-row assistant">
            <div className="chat-msg bot typing">
              <span /><span /><span />
            </div>
          </div>
        )}
      </div>

      {!thinking && (
        <div className="chat-suggestions" aria-label="Suggested questions">
          <span className="chat-suggestions-label">Try:</span>
          {suggestionsFor(location.pathname + location.search, user).map((q) => (
            <button key={q} onClick={() => send(q)}>{q}</button>
          ))}
        </div>
      )}

      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
      >
        <input
          placeholder={/^\/products\/[^/]+$/.test(location.pathname) ? 'Ask about this item…' : 'Ask about sizes, colors, gifts…'}
          value={input}
          maxLength={1000}
          onChange={(e) => setInput(e.target.value)}
          autoFocus
        />
        <button type="submit" disabled={thinking || !input.trim()}>Send</button>
      </form>
    </div>
  )
}
