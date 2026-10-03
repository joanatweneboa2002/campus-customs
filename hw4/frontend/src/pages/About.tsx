import Bulldog from '../components/Bulldog'

const facts = [
  { big: '102', small: 'cozy things on our shelves' },
  { big: '14', small: 'residential colleges, all repped' },
  { big: '∞', small: 'cups of coffee, honestly too many' },
  { big: '1', small: 'very good boy (Buddy)' },
]

export default function About() {
  return (
    <section className="section narrow about">
      <span className="sticker-tag">About Us</span>
      <h1>
        A tiny shop with a <span className="squiggle">big</span> Bulldog heart.
      </h1>
      <p className="lead">
        Campus Customs began with one very serious belief: Yale gear should be <em>soft</em>.
        Like, "accidentally fall asleep in the library" soft.
      </p>
      <p>
        We live on Broadway in New Haven, a short stroll from Old Campus, and we've spent years
        dressing students for move-in day, parents for Family Weekend and alumni for reunions
        where they swear they haven't changed a bit.
      </p>
      <p>
        You'll find a lot more than the classic big-letter hoodie here. We stock pieces for every
        residential college, the grad and professional schools, and the teams that keep the
        stands loud all year. Our rule is simple: if we wouldn't wear it on a cold Tuesday, it
        doesn't go on the shelf.
      </p>

      <div className="facts">
        {facts.map((f, i) => (
          <div key={f.small} className={`fact fact-${i}`}>
            <strong>{f.big}</strong>
            <span>{f.small}</span>
          </div>
        ))}
      </div>

      <div className="meet">
        <Bulldog size={130} />
        <div>
          <h3>Meet Buddy, Head of Vibes</h3>
          <p>
            Buddy greets every customer, tests every hoodie for nap quality, and is currently
            learning to answer your questions in the chat box. He's a fast learner. Mostly.
          </p>
        </div>
      </div>
    </section>
  )
}
