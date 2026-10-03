import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Bulldog from '../components/Bulldog'
import ProductCard from '../components/ProductCard'
import { categories } from '../categories'
import type { Product } from '../types'
import { openBuddy } from '../buddyEvents'

// Only colleges/schools we actually carry (checked against the catalogue).
const colleges = ['Benjamin Franklin', 'Berkeley', 'Branford', 'Davenport', 'Grace Hopper', 'Jonathan Edwards', 'Morse', 'Pierson', 'Saybrook', 'Timothy Dwight', 'Trumbull']
const schools = ['Architecture', 'School of Art', 'Divinity', 'Engineering', 'Forest School', 'Law School', 'Management', 'Medicine', 'Music', 'Nursing', 'Public Health']

const reasons = [
  { emoji: '🐶', title: 'Ask Buddy anything', text: 'Our bulldog knows every size, color and price on the shelf, and finds you something similar when your size is gone.' },
  { emoji: '🏈', title: 'Bleacher-proof', text: 'Thick, warm layers for freezing afternoons at the Bowl and loud nights at Ingalls.' },
  { emoji: '👵', title: 'The whole family', text: 'Mom, Dad, Grandpa, that one cousin. Everyone gets to be a Bulldog here.' },
]

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([])

  useEffect(() => {
    fetch('/api/products')
      .then((r) => r.json())
      .then((items: Product[]) =>
        setFeatured(items.filter((p) => /hood|crew/i.test(p.garment_type)).sort((a, b) => b.price - a.price).slice(0, 4)),
      )
      .catch(() => setFeatured([]))
  }, [])

  return (
    <>
      <section className="hero">
        <div className="blob blob-a" />
        <div className="blob blob-b" />
        <div className="hero-text">
          <span className="sticker-tag">New Haven's coziest corner 🐾</span>
          <h1>
            Cozy fits for <span className="squiggle">Bulldogs</span> of every breed.
          </h1>
          <p className="hand">(yes, even your grandpa)</p>
          <p className="hero-sub">
            Hoodies, crewnecks, tees and quarter-zips for students, alumni, proud parents and
            anyone who has ever yelled "Boola boola" a little too loud.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn">Go shopping 🛍️</Link>
            <button className="btn btn-ghost" onClick={openBuddy}>Ask Buddy 🐾</button>
          </div>
          <ul className="perks">
            <li>📏 XS–XXL in every style</li>
            <li>🏛️ All your colleges &amp; schools</li>
            <li>📍 Right on Broadway</li>
          </ul>
        </div>
        <div className="hero-mascot">
          <div className="bubble">Psst… the hoodies are <b>really</b> soft.</div>
          <Bulldog size={200} wink />
          <p className="hand mascot-name">↑ this is Buddy. he works here.</p>
        </div>
      </section>

      <section className="section">
        <h2 className="center">What's your vibe today?</h2>
        <div className="vibes">
          {categories.map((c, i) => (
            <Link key={c.key} to={`/products?cat=${c.key}`} className={`vibe vibe-${i}`}>
              <span className="vibe-emoji">{c.emoji}</span>
              {c.label}
            </Link>
          ))}
        </div>
      </section>

      {featured.length > 0 && (
        <section className="section">
          <div className="section-head">
            <h2>
              Fan faves <span className="hand accent">aka the comfiest ones</span>
            </h2>
            <Link to="/products" className="link-arrow">See all 102 →</Link>
          </div>
          <div className="grid">
            {featured.map((p, i) => <ProductCard key={p.id} product={p} index={i} />)}
          </div>
        </section>
      )}

      <section className="section college-shop">
        <div className="section-head">
          <h2>
            Shop by college &amp; school <span className="hand accent">rep your crest</span>
          </h2>
        </div>
        <h3 className="college-group">Residential colleges</h3>
        <div className="crest-row">
          {colleges.map((c) => (
            <Link key={c} to={`/products?q=${encodeURIComponent(c)}`} className="crest-chip">
              <span className="crest" aria-hidden="true">{c.split(' ').map((w) => w[0]).join('')}</span>
              {c}
            </Link>
          ))}
        </div>
        <h3 className="college-group">Graduate &amp; professional schools</h3>
        <div className="crest-row">
          {schools.map((c) => (
            <Link key={c} to={`/products?q=${encodeURIComponent(c)}`} className="crest-chip school">
              <span className="crest" aria-hidden="true">{c.replace('School of ', '').split(' ').map((w) => w[0]).join('')}</span>
              {c.replace('School of ', '')}
            </Link>
          ))}
        </div>
      </section>

      <section className="section reasons">
        {reasons.map((r, i) => (
          <div key={r.title} className={`reason reason-${i}`}>
            <span className="reason-emoji">{r.emoji}</span>
            <h3>{r.title}</h3>
            <p>{r.text}</p>
          </div>
        ))}
      </section>
    </>
  )
}
