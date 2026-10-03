import type { Product } from './types'

// Friendly shopping categories, derived from the catalogue's garment_type.
export const categories = [
  { key: 'hoodies', label: 'Hoodie season', emoji: '🧸', test: /hood/i },
  { key: 'crewnecks', label: 'Crewneck crew', emoji: '☕', test: /crew|mockneck|sweatshirt/i },
  { key: 'tees', label: 'Tee time', emoji: '☀️', test: /t-shirt|shirt/i },
  { key: 'zips', label: 'Quarter-zip energy', emoji: '📚', test: /quarter-zip|1-4-zip/i },
  { key: 'jackets', label: 'Fleece & jackets', emoji: '🍂', test: /jacket|fleece/i },
] as const

// Checked in order, so a "hooded sweatshirt" lands in hoodies, not crewnecks.
export function categoryOf(p: Product): string {
  const text = `${p.garment_type} ${p.id}`
  for (const c of [categories[3], categories[4], categories[0], categories[1], categories[2]]) {
    if (c.test.test(text)) return c.key
  }
  return 'other'
}
