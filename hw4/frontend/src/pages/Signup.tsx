import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Bulldog from '../components/Bulldog'
import { useAuth } from '../auth'

export default function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', confirm_password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value })

  const mismatch = form.confirm_password.length > 0 && form.confirm_password !== form.password

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (form.password !== form.confirm_password) {
      setError("Passwords don't match. Try typing them again 🐾")
      return
    }
    setBusy(true)
    setError('')
    try {
      await signup(form)
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
        <div className="auth-mascot"><Bulldog size={80} wink /></div>
        <h1>Join the pack</h1>
        <p className="hand accent center">no tryouts required</p>
        <div className="row">
          <label>First name<input placeholder="Handsome" value={form.first_name} onChange={set('first_name')} required /></label>
          <label>Last name<input placeholder="Dan" value={form.last_name} onChange={set('last_name')} required /></label>
        </div>
        <label>Email<input type="email" placeholder="you@yale.edu" value={form.email} onChange={set('email')} required /></label>
        <label>
          Password
          <input type="password" placeholder="8+ characters" minLength={8} value={form.password} onChange={set('password')} required autoComplete="new-password" />
        </label>
        <label>
          Confirm password
          <input
            type="password"
            placeholder="type it again"
            value={form.confirm_password}
            onChange={set('confirm_password')}
            aria-invalid={mismatch}
            className={mismatch ? 'mismatch' : ''}
            required
            autoComplete="new-password"
          />
          {mismatch && <span className="field-hint">Passwords don't match yet</span>}
        </label>
        {error && <p className="form-error">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>{busy ? 'Making your account…' : 'Create my account ✨'}</button>
        <p className="muted center">
          Already one of us? <Link to="/login" className="accent">Log in</Link>
        </p>
      </form>
    </section>
  )
}
