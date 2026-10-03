import type { SizeStock } from './types'

// One place for stock rules, so cards, badges and the detail page agree.
export const LOW_SIZE_MAX = 3 // 1–3 left in a size = low (same as backend models.LOW_STOCK_MAX)
export const LOW_TOTAL_MAX = 30 // 30 or fewer units across all sizes = low stock

export type SizeState = 'in' | 'low' | 'out'

export function sizeState(quantity: number): SizeState {
  if (quantity === 0) return 'out'
  return quantity <= LOW_SIZE_MAX ? 'low' : 'in'
}

export interface StockBadge {
  kind: 'sold-out' | 'low-stock'
  label: string
  detail: string
}

/** Product-level badge: "Sold out" (nothing in any size) or "Low stock" (running out overall). */
export function stockBadge(total: number | undefined, sizes: SizeStock[] = []): StockBadge | null {
  if (total === undefined) return null
  if (total === 0) return { kind: 'sold-out', label: 'Sold out', detail: 'Gone in every size' }
  const inStock = sizes.filter((s) => s.quantity > 0)
  const halfGone = sizes.length > 0 && inStock.length <= sizes.length / 2
  if (total <= LOW_TOTAL_MAX || halfGone) {
    const detail = halfGone ? `Only ${inStock.map((s) => s.size).join(', ')} left` : `Only ${total} left`
    return { kind: 'low-stock', label: 'Low stock', detail }
  }
  return null
}
