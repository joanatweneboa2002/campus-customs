import { Link, NavLink, useNavigate } from 'react-router-dom'
import Bulldog from './Bulldog'
import { useAuth } from '../auth'

const ticker = [
  'Free pickup on Broadway',
  'Bulldog-approved fits',
  'Boola boola!',
  'Finals week = hoodie week',
  'Grandparents welcome',
  'Cozy level: maximum',
]

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  return (
    <>
      <div className="ticker" aria-label="Announcements">
        <div className="ticker-track">
          {[...ticker, ...ticker].map((t, i) => (
            <span key={i}>{t} <b>🐾</b></span>
          ))}
        </div>
      </div>
      <header className="nav">
        <Link to="/" className="brand">
          <Bulldog size={38} />
          <span>
            Campus <em>Customs</em>
          </span>
        </Link>
        <nav className="nav-links">
          <NavLink to="/" end>Home</NavLink>
          <NavLink to="/products">Products</NavLink>
          <NavLink to="/about">About Us</NavLink>
          {user ? (
            <>
              <span className="nav-hello">Hi, {user.first_name} 🐾</span>
              <button
                className="nav-cta nav-logout"
                onClick={async () => {
                  await logout()
                  navigate('/')
                }}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">Log in</NavLink>
              <NavLink to="/signup" className="nav-cta">Create account</NavLink>
            </>
          )}
        </nav>
      </header>
    </>
  )
}
