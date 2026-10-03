import { Link } from 'react-router-dom'
import Bulldog from './Bulldog'
import { categories } from '../categories'
import { openBuddy } from '../buddyEvents'

const YEAR = new Date().getFullYear()

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <div className="footer-logo">
            <Bulldog size={44} />
            <span>
              Campus <em>Customs</em>
            </span>
          </div>
          <p>Yale apparel for students, alumni and every Bulldog's family.</p>
          <p className="footer-address">57 Broadway · New Haven, CT</p>
        </div>
        <div>
          <h4>Shop</h4>
          {categories.map((c) => (
            <Link key={c.key} to={`/products?cat=${c.key}`}>{c.label}</Link>
          ))}
          <Link to="/products">Everything</Link>
        </div>
        <div>
          <h4>Help</h4>
          <button className="footer-link" onClick={openBuddy}>Ask Buddy 🐾</button>
          <Link to="/about">About us</Link>
          <Link to="/login">Log in</Link>
          <Link to="/signup">Create account</Link>
        </div>
      </div>
      <div className="footer-bottom">
        <span className="footer-big">Stay cozy, Bulldogs.</span>
        <span>© {YEAR} Campus Customs · Made with 💛 and too much coffee</span>
      </div>
    </footer>
  )
}
