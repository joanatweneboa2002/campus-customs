import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import ProductImage from '../components/ProductImage'
import { categories, categoryOf } from '../categories'
import { formatPrice, type Product, type SizeStock } from '../types'

const getJson = <T,>(url: string): Promise<T> =>
  fetch(url).then((r) => {
    if (!r.ok) throw new Error(`${r.status} ${url}`)
    return r.json()
  })

const tips = [
  'Bulldog tip: size up for maximum hoodie-burrito energy.',
  'Pairs well with hot cider and a long walk around Old Campus.',
  'Certified cozy by Buddy (he napped on it, sorry).',
  'Warning: may cause spontaneous school spirit.',
]

function stockNote(q: number) {
  if (q === 0) return 'Sold out 😢'
  if (q <= 3) return `Only ${q} left. Run!`
  if (q <= 8) return `${q} left`
  return `${q} in stock`
}

// Keyed by product id, so moving between products (e.g. via "You might also like")
// starts each page fresh instead of showing the previous product's size picks.
export default function ProductDetailPage() {
  const { id = '' } = useParams()
  return <ProductDetail key={id} id={id} />
}

/** Up to 4 in-stock products of the same kind, preferring shared colors. */
function RelatedProducts({ product }: { product: Product }) {
  const [all, setAll] = useState<Product[]>([])
  useEffect(() => {
    getJson<Product[]>('/api/products').then(setAll).catch(() => setAll([]))
  }, [])
  const kind = categoryOf(product)
  const colors = new Set(product.colors.map((c) => c.toLowerCase()))
  const related = all
    .filter((p) => p.id !== product.id && categoryOf(p) === kind && (p.total_stock ?? 0) > 0)
    .map((p) => ({ p, score: p.colors.filter((c) => colors.has(c.toLowerCase())).length - Math.abs(p.price - product.price) / 50 }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 4)
    .map((x) => x.p)
  if (related.length === 0) return null
  return (
    <section className="related">
      <h2>
        You might also like <span className="hand accent">Buddy approved</span>
      </h2>
      <div className="grid">
        {related.map((p, i) => <ProductCard key={p.id} product={p} index={i} />)}
      </div>
    </section>
  )
}

function ProductDetail({ id }: { id: string }) {
  // Back goes to wherever the card was clicked (e.g. Buddy's picks), else the full closet.
  const from: string = (useLocation().state as { from?: string } | null)?.from ?? '/products'
  const [product, setProduct] = useState<Product | null>(null)
  const [sizes, setSizes] = useState<SizeStock[] | null>(null)
  const [error, setError] = useState(false)
  const [stockError, setStockError] = useState(false)
  const [picked, setPicked] = useState<string | null>(null)
  const [toast, setToast] = useState('')

  useEffect(() => {
    const pid = encodeURIComponent(id)
    getJson<Product>(`/api/products/${pid}`).then(setProduct).catch(() => setError(true))
    // Sizes and stock come straight from the inventory table.
    getJson<SizeStock[]>(`/api/products/${pid}/inventory`).then(setSizes).catch(() => setStockError(true))
  }, [id])

  if (error) {
    return (
      <section className="section empty">
        <h2>Hmm, that one ran away 🐾</h2>
        <Link to="/products" className="btn">Back to the closet</Link>
      </section>
    )
  }
  if (!product) return <section className="section"><p className="muted">Unfolding this one…</p></section>

  const totalStock = sizes?.reduce((sum, s) => sum + s.quantity, 0) ?? 0
  const tip = tips[product.name.length % tips.length]

  const addToBag = () => {
    setToast(picked ? `Size ${picked}, great taste! Checkout is coming soon 🛍️` : 'Pick a size first, bestie 👆')
    setTimeout(() => setToast(''), 2800)
  }

  const kind = categories.find((c) => c.key === categoryOf(product))
  return (
    <section className="section">
      <div className="crumbs">
        <nav aria-label="Breadcrumb">
          <Link to="/products">Shop</Link>
          {kind && (
            <>
              <span>›</span>
              <Link to={`/products?cat=${kind.key}`}>{kind.label}</Link>
            </>
          )}
          <span>›</span>
          <span aria-current="page">{product.name}</span>
        </nav>
        <Link to={from} className="back">
          {from.includes('view=buddy') ? "← Back to Buddy's picks" : '← Back to the closet'}
        </Link>
      </div>
      <div className="detail">
        <div className="detail-img">
          <ProductImage key={product.image_url} src={product.image_url} alt={product.name} />
        </div>
        <div className="detail-info">
          <span className="sticker-tag">{product.garment_type}</span>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>
          <p className="detail-desc">{product.description}</p>

          <h3>Colors</h3>
          <div className="chips">
            {product.colors.map((c) => <span key={c} className="chip">{c}</span>)}
          </div>

          <h3>
            Pick your size <span className="hand accent">bestie</span>
          </h3>
          {stockError && <p className="error">Couldn't load stock right now. Please refresh.</p>}
          {!stockError && sizes === null && <p className="muted">Counting what's on the shelf…</p>}
          {sizes && sizes.length === 0 && <p className="muted">No sizes listed for this item yet.</p>}
          {sizes && sizes.length > 0 && (
            <>
              <div className="sizes">
                {sizes.map((s) => (
                  <button
                    key={s.size}
                    disabled={s.quantity === 0}
                    onClick={() => setPicked(s.size)}
                    className={`size ${s.quantity === 0 ? 'out' : s.quantity <= 3 ? 'low' : ''} ${picked === s.size ? 'picked' : ''}`}
                  >
                    <strong>{s.size}</strong>
                    <span>{stockNote(s.quantity)}</span>
                  </button>
                ))}
              </div>
              <p className="muted">
                {totalStock > 0 ? `${totalStock} total on the shelf across all sizes` : 'Sold out everywhere. Buddy is sad.'}
              </p>
            </>
          )}

          <button className="btn add" onClick={addToBag} disabled={totalStock === 0}>
            Add to bag 🛍️
          </button>
          {toast && <div className="toast">{toast}</div>}
          <p className="tip">🐶 {tip}</p>
        </div>
      </div>
      <RelatedProducts product={product} />
    </section>
  )
}
