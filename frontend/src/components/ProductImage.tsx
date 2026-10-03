import { useState } from 'react'

// Product photo with a friendly placeholder if the image fails to load.
export default function ProductImage({ src, alt, lazy = false }: { src: string; alt: string; lazy?: boolean }) {
  const [failed, setFailed] = useState(false)

  if (failed) return <div className="img-fallback">Photo coming soon</div>
  return <img src={src} alt={alt} loading={lazy ? 'lazy' : undefined} onError={() => setFailed(true)} />
}
