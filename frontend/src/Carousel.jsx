import { useEffect, useState } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import { Link } from 'react-router'
import Court from './Court.jsx'
import Ticket from './Ticket.jsx'

const INTERVAL_MS = 5000
const SWIPE_PX = 40

// Carousel of upcoming matches, one ticket per slide on a court: autoplay, pause button, arrows, dots, swipe and arrow keys.
// Autoplay stops while hovered or focused, and never starts for people who ask for less motion.
export default function Carousel({ fixtures }) {
  const count = fixtures.length
  const [index, setIndex] = useState(0)
  const [hovered, setHovered] = useState(false)
  const [stopped, setStopped] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  const [swipeStart, setSwipeStart] = useState(null)
  const playing = !stopped && !hovered && count > 1

  const go = (n) => setIndex((n + count) % count)

  useEffect(() => {
    if (!playing) return
    const timer = setInterval(() => setIndex((i) => (i + 1) % count), INTERVAL_MS)
    return () => clearInterval(timer)
  }, [playing, count])

  function onKeyDown(e) {
    if (e.key === 'ArrowLeft') go(index - 1)
    if (e.key === 'ArrowRight') go(index + 1)
  }

  function onPointerUp(e) {
    if (swipeStart === null) return
    const dx = e.clientX - swipeStart
    if (Math.abs(dx) > SWIPE_PX) go(index + (dx < 0 ? 1 : -1))
    setSwipeStart(null)
  }

  if (count === 0) return null

  return (
    <section
      className="carousel"
      aria-roledescription="carousel"
      aria-label="Upcoming matches"
      tabIndex={0}
      onKeyDown={onKeyDown}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => setHovered(true)}
      onBlur={() => setHovered(false)}
    >
      <Court />
      <div
        className="carousel-viewport"
        onPointerDown={(e) => setSwipeStart(e.clientX)}
        onPointerUp={onPointerUp}
        onPointerCancel={() => setSwipeStart(null)}
      >
        <div
          className="carousel-track"
          style={{ transform: `translateX(-${index * 100}%)` }}
          aria-live={playing ? 'off' : 'polite'}
        >
          {fixtures.map((f, i) => (
            <article
              key={f.id}
              className="slide"
              role="group"
              aria-roledescription="slide"
              aria-label={`${i + 1} of ${count}`}
              inert={i === index ? undefined : ''} // off-screen slides must not take focus
            >
              <Ticket fixture={f} details={[['Venue', f.venue]]}>
                {/* the QR opens this match's page, so a phone camera works as a shortcut */}
                <div className="qr">
                  <QRCodeSVG value={`${window.location.origin}/fixtures/${f.id}`} size={96} marginSize={0} title="QR code for this match" />
                </div>
                <Link className="pill" to={`/fixtures/${f.id}`}>
                  See tickets
                </Link>
              </Ticket>
            </article>
          ))}
        </div>
      </div>

      {count > 1 && (
        <div className="carousel-controls">
          <button type="button" className="icon-btn" onClick={() => go(index - 1)} aria-label="Previous match">
            &lsaquo;
          </button>
          <div className="dots">
            {fixtures.map((f, i) => (
              <button
                key={f.id}
                type="button"
                className={i === index ? 'dot active' : 'dot'}
                onClick={() => go(i)}
                aria-label={`Go to match ${i + 1}`}
                aria-current={i === index}
              />
            ))}
          </div>
          <button type="button" className="icon-btn" onClick={() => setStopped(!stopped)} aria-pressed={stopped}>
            {stopped ? 'Play' : 'Pause'}
          </button>
          <button type="button" className="icon-btn" onClick={() => go(index + 1)} aria-label="Next match">
            &rsaquo;
          </button>
        </div>
      )}
    </section>
  )
}
