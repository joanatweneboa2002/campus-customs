import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Bulldog from '../components/Bulldog'
import { useAuth } from '../auth'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="section">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-mascot"><Bulldog size={80} /></div>
        <h1>Welcome back, Bulldog!</h1>
        <p className="hand accent center">Buddy missed you. (he won't admit it)</p>
        <label>Email<input type="email" placeholder="you@yale.edu" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
        <label>Password<input type="password" placeholder="shh, it's a secret" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
        {error && <p className="form-error">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>{busy ? 'Sniffing…' : 'Let me in 🐾'}</button>
        <p className="muted center">
          New here? <Link to="/signup" className="accent">Join the pack</Link>
        </p>
      </form>
    </section>
  )
}
