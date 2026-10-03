import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Bulldog from '../components/Bulldog'
import ProductCard from '../components/ProductCard'
import { categories, categoryOf } from '../categories'
import { useBuddyResults } from '../buddyResults'
import type { Product } from '../types'

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(true)
  const [params, setParams] = useSearchParams()
  // ?q= lets other pages link to a search (e.g. "Shop by college" on Home)
  const [query, setQuery] = useState(() => params.get('q') ?? '')
  const [sort, setSort] = useState<'featured' | 'price-asc' | 'price-desc' | 'name'>('featured')
  const cat = params.get('cat') ?? 'all'
  const { results: buddy, clear: clearBuddy } = useBuddyResults()
  const showBuddy = params.get('view') === 'buddy' && buddy !== null

  useEffect(() => {
    fetch('/api/products')
      .then((r) => {
        if (!r.ok) throw new Error()
        return r.json()
      })
      .then(setProducts)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  const shown = useMemo(() => {
    // every word must match the START of a word somewhere, so "navy hoodie" finds navy
    // hoodies and "art" finds the School of Art, not every "quarter-zip"
    const esc = (w: string) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean).map((w) => new RegExp(`\\b${esc(w)}`))
    const list = products.filter((p) => {
      if (cat !== 'all' && categoryOf(p) !== cat) return false
      const text = [p.name, p.garment_type, p.description, ...p.tags, ...p.colors].join(' ').toLowerCase()
      return words.every((w) => w.test(text))
    })
    const by = {
      featured: () => 0,
      'price-asc': (a: Product, b: Product) => a.price - b.price,
      'price-desc': (a: Product, b: Product) => b.price - a.price,
      name: (a: Product, b: Product) => a.name.localeCompare(b.name),
    }[sort]
    return sort === 'featured' ? list : [...list].sort(by)
  }, [products, cat, query, sort])

  if (showBuddy) {
    // Results the chat agent found; same cards and detail pages as the normal listing.
    const picks: Product[] = buddy.products.map((p) => ({ ...p, tags: [] }))
    return (
      <section className="section">
        <div className="buddy-banner" key={buddy.id}>
          <Bulldog size={90} wink />
          <div>
            <span className="sticker-tag">Buddy's picks</span>
            <h1>{buddy.heading}</h1>
            <p className="muted">
              You asked: <em>"{buddy.query}"</em> · {picks.length} {picks.length === 1 ? 'item' : 'items'} fetched
            </p>
          </div>
          <button
            className="btn btn-ghost"
            onClick={() => {
              clearBuddy()
              setParams({})
            }}
          >
            Browse everything
          </button>
        </div>
        <div className="grid buddy-grid" key={`grid-${buddy.id}`}>
          {picks.map((p, i) => <ProductCard key={p.id} product={p} index={i} />)}
        </div>
      </section>
    )
  }

  return (
    <section className="section">
      <div className="shop-head">
        <div>
          <h1>The Whole Closet</h1>
          <p className="hand accent">every single thing we've got, no gatekeeping</p>
        </div>
        <input
          className="search"
          placeholder="🔍  Try 'navy hoodie' or 'Branford'"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="filters">
        <button className={cat === 'all' ? 'on' : ''} onClick={() => setParams({})}>✨ Everything</button>
        {categories.map((c) => (
          <button key={c.key} className={cat === c.key ? 'on' : ''} onClick={() => setParams({ cat: c.key })}>
            {c.emoji} {c.label}
          </button>
        ))}
      </div>

      {loading && <p className="muted">Fetching the goods…</p>}
      {error && <p className="error">Couldn't load products. Is the backend running on port 8000?</p>}
      {!loading && !error && (
        <div className="list-bar">
          <p className="muted count">
            {shown.length} {shown.length === 1 ? 'item' : 'items'}
            {query.trim() && <> for "<strong>{query.trim()}</strong>"</>}
          </p>
          <label className="sort">
            Sort
            <select value={sort} onChange={(e) => setSort(e.target.value as typeof sort)}>
              <option value="featured">Featured</option>
              <option value="price-asc">Price: low to high</option>
              <option value="price-desc">Price: high to low</option>
              <option value="name">Name A–Z</option>
            </select>
          </label>
        </div>
      )}
      {!loading && !error && shown.length === 0 && (
        <div className="empty">
          <Bulldog size={110} />
          <p>Buddy sniffed everywhere and found nothing. Try another search?</p>
        </div>
      )}
      <div className="grid">
        {shown.map((p, i) => <ProductCard key={p.id} product={p} index={i} />)}
      </div>
    </section>
  )
}
