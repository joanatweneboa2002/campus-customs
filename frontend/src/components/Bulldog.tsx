// Buddy, the Campus Customs mascot: a bulldog drawn entirely in HTML/CSS.
// `size` is the face width in px; everything scales from it.
export default function Bulldog({ size = 160, wink = false }: { size?: number; wink?: boolean }) {
  return (
    <div className="bulldog" style={{ ['--s' as string]: `${size}px` }} aria-hidden="true">
      <div className="bd-ear left" />
      <div className="bd-ear right" />
      <div className="bd-head">
        <div className="bd-brow left" />
        <div className="bd-brow right" />
        <div className="bd-eye left" />
        <div className={`bd-eye right ${wink ? 'wink' : ''}`} />
        <div className="bd-patch" />
        <div className="bd-muzzle">
          <div className="bd-nose" />
          <div className="bd-jowl left" />
          <div className="bd-jowl right" />
          <div className="bd-tongue" />
        </div>
      </div>
      <div className="bd-collar"><span className="bd-tag">Y</span></div>
    </div>
  )
}
