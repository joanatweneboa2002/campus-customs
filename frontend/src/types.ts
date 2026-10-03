export interface Product {
  id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  tags: string[]
  image_url: string
  price: number
  total_stock?: number
  sizes?: SizeStock[]
}

export interface SizeStock {
  size: string
  quantity: number
}

export const formatPrice = (price: number) => `$${price.toFixed(2)}`
