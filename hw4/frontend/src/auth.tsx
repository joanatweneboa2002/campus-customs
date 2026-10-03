import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'

// Mirrors backend/models.py PublicUser
export interface User {
  id: number
  name: string
  first_name: string
  email: string
}

interface AuthState {
  user: User | null
  token: string | null
  ready: boolean // false until a saved session has been checked
  login: (email: string, password: string) => Promise<User>
  signup: (form: { first_name: string; last_name: string; email: string; password: string; confirm_password: string }) => Promise<User>
  logout: () => Promise<void>
}

const TOKEN_KEY = 'cc-session'
const AuthContext = createContext<AuthState | null>(null)

async function postJson(url: string, body: unknown) {
  const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) {
    // FastAPI sends {detail: "..."} or, for validation errors, {detail: [{msg}]}
    const d = data.detail
    throw new Error(typeof d === 'string' ? d : Array.isArray(d) ? d.map((e) => String(e.msg).replace(/^Value error, /, '')).join(', ') : 'Something went wrong')
  }
  return data as { token: string; user: User }
}

// Session token lives in localStorage; the server only stores its hash.
export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(() => !localStorage.getItem(TOKEN_KEY))

  // Coming back to the site: check the saved session is still valid.
  useEffect(() => {
    if (!token || user) return
    fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY)
        setToken(null)
      })
      .finally(() => setReady(true))
  }, [token, user])

  const start = useCallback((data: { token: string; user: User }) => {
    localStorage.setItem(TOKEN_KEY, data.token)
    setToken(data.token)
    setUser(data.user)
    setReady(true)
    return data.user
  }, [])

  const login = useCallback(
    async (email: string, password: string) => start(await postJson('/api/auth/login', { email, password })),
    [start],
  )
  const signup = useCallback(
    async (form: { first_name: string; last_name: string; email: string; password: string; confirm_password: string }) =>
      start(await postJson('/api/auth/signup', form)),
    [start],
  )
  const logout = useCallback(async () => {
    if (token) await fetch('/api/auth/logout', { method: 'POST', headers: { Authorization: `Bearer ${token}` } }).catch(() => {})
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }, [token])

  return <AuthContext.Provider value={{ user, token, ready, login, signup, logout }}>{children}</AuthContext.Provider>
}

// Hook lives next to its provider on purpose; fast refresh just reloads this file.
// eslint-disable-next-line react/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
