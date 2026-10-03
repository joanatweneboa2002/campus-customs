import { Link, useLocation } from 'react-router-dom'
import ProductImage from './ProductImage'
import { formatPrice, type Product } from '../types'
import { sizeState, stockBadge } from '../stock'

export default function ProductCard({ product, index = 0 }: { product: Product; index?: number }) {
  const badge = stockBadge(product.total_stock, product.sizes)
  const soldOutSizes = (product.sizes ?? []).filter((s) => s.quantity === 0).map((s) => s.size)
  const location = useLocation()
  return (
    <Link
      to={`/products/${product.id}`}
      state={{ from: location.pathname + location.search }}
      className={`card tilt-${index % 3} ${badge?.kind === 'sold-out' ? 'is-sold-out' : ''}`}
    >
      <div className="card-img">
        {badge && (
          <span className={`stock-badge ${badge.kind}`} title={badge.detail}>
            {badge.kind === 'sold-out' ? '😢' : '⏳'} {badge.label}
          </span>
        )}
        <ProductImage src={product.image_url} alt={product.name} lazy />
      </div>
      <div className="card-body">
        <h3>{product.name}</h3>
        <p className="card-desc">{product.description}</p>
        {product.sizes && product.sizes.length > 0 && (
          <div
            className="size-strip"
            aria-label={soldOutSizes.length ? `Sold out in ${soldOutSizes.join(', ')}` : 'All sizes in stock'}
          >
            {product.sizes.map((s) => (
              <span key={s.size} className={`size-pip ${sizeState(s.quantity)}`} title={s.quantity === 0 ? `${s.size}: sold out` : `${s.size}: ${s.quantity} left`}>
                {s.size}
              </span>
            ))}
          </div>
        )}
        <div className="card-foot">
          <span className="price">{formatPrice(product.price)}</span>
          <span className="peek">Take a peek →</span>
        </div>
      </div>
    </Link>
  )
}
