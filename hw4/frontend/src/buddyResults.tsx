import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'

// Mirrors backend/models.py ProductCard / PageResults
export interface ChatProductCard {
  id: string
  name: string
  price: number
  garment_type: string
  description: string
  colors: string[]
  image_url: string
  url: string
  total_stock: number
  sizes?: { size: string; quantity: number }[]
}

export interface PageResults {
  heading: string
  query: string
  products: ChatProductCard[]
}

interface BuddyResultsState {
  results: (PageResults & { id: number }) | null
  show: (r: PageResults) => void
  clear: () => void
}

const STORAGE_KEY = 'buddy-page-results'
const BuddyResultsContext = createContext<BuddyResultsState | null>(null)

function load() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

// Shared between the chat box (writes) and the Products page (reads).
// Kept in sessionStorage so a refresh doesn't lose Buddy's picks.
export function BuddyResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<BuddyResultsState['results']>(load)

  const show = useCallback((r: PageResults) => {
    const next = { ...r, id: Date.now() } // new id re-triggers the "pop in" animation
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    setResults(next)
  }, [])

  const clear = useCallback(() => {
    sessionStorage.removeItem(STORAGE_KEY)
    setResults(null)
  }, [])

  return <BuddyResultsContext.Provider value={{ results, show, clear }}>{children}</BuddyResultsContext.Provider>
}

// Hook lives next to its provider on purpose; fast refresh just reloads this file.
// eslint-disable-next-line react/only-export-components
export function useBuddyResults() {
  const ctx = useContext(BuddyResultsContext)
  if (!ctx) throw new Error('useBuddyResults must be used inside BuddyResultsProvider')
  return ctx
}

export const BUDDY_RESULTS_PATH = '/products?view=buddy'
