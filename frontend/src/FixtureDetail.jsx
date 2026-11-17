import { useCallback, useState } from 'react'
import { Link, useParams } from 'react-router'
import { checkout, getFixture, getSeatMap } from './api.js'
import ArenaMap from './ArenaMap.jsx'
import ClubBadge from './ClubBadge.jsx'
import JerseyStudio from './JerseyStudio.jsx'
import { formatDate, formatPrice, formatSeat, formatTime } from './format.js'
import Seo from './Seo.jsx'
import Status from './Status.jsx'
import useFetch from './useFetch.js'

export default function FixtureDetail({ user }) {
  const { id } = useParams()
  const { data: f, error } = useFetch(() => getFixture(id), [id])

  return (
    <main className="content">
      <Link className="back" to="/fixtures">&larr; All fixtures</Link>
      <Status loading={!f && !error} error={error} />
      {f && (
        <>
          <Seo
            title={`${f.home.name} vs ${f.away.name}`}
            description={`${f.home.name} vs ${f.away.name} on ${formatDate(f.kickoff_at)} at ${f.venue}. Zones, prices and seats left.`}
          />
          <h1 className="sr-only">
            {f.home.name} vs {f.away.name}
          </h1>
          <div className="match-head">
            <Link to={`/clubs/${f.home.slug}`} className="team">
              <ClubBadge club={f.home} size={88} />
              {f.home.name}
            </Link>
            <span className="vs">vs</span>
            <Link to={`/clubs/${f.away.slug}`} className="team">
              <ClubBadge club={f.away} size={88} />
              {f.away.name}
            </Link>
          </div>
          <p className="match-when">
            {formatDate(f.kickoff_at)} &middot; {formatTime(f.kickoff_at)} &middot; {f.venue}
          </p>

          <h2>Tickets</h2>
          <div className="table-wrap">
            <table>
              <caption className="sr-only">Zones, prices and seats left</caption>
              <thead>
                <tr>
                  <th scope="col">Zone</th>
                  <th scope="col">Price</th>
                  <th scope="col">Seats left</th>
                </tr>
              </thead>
              <tbody>
                {f.zones.map((z) => (
                  <tr key={z.zone_id}>
                    <th scope="row">{z.name}</th>
                    <td>{formatPrice(z.price_bani)}</td>
                    <td>{z.seats_left > 0 ? `${z.seats_left} of ${z.quota}` : 'Sold out'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {f.status !== 'scheduled' ? (
            <p className="message error">Tickets for this match are no longer on sale.</p>
          ) : user ? (
            <BuyForm fixture={f} />
          ) : (
            <p>
              <Link to="/login">Log in</Link> to buy tickets.
            </p>
          )}
        </>
      )}
    </main>
  )
}

const MAX_PER_ORDER = 6 // same cap as the server

function BuyForm({ fixture }) {
  const [round, setRound] = useState(0) // bumped to reload the seat map after a seat was taken by someone else
  const { data: seatMap, error: mapError } = useFetch(() => getSeatMap(fixture.id), [fixture.id, round])
  const [seats, setSeats] = useState([]) // codes of the chosen seats, all in one zone
  const [zoneId, setZoneId] = useState(null)
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [wantJersey, setWantJersey] = useState(false)
  const [jersey, setJersey] = useState(null) // payload from the studio, null while incomplete
  const [jerseyPrice, setJerseyPrice] = useState(0)
  // stable identity: the studio calls it from an effect
  const handleJersey = useCallback((body, price) => {
    setJersey(body)
    setJerseyPrice(price)
  }, [])

  function toggle(code, zone) {
    setNote('')
    if (seats.includes(code)) return setSeats(seats.filter((c) => c !== code))
    if (seats.length > 0 && zone !== zoneId) {
      setNote('One order covers one zone, so your earlier seats were cleared.')
      setZoneId(zone)
      return setSeats([code])
    }
    if (seats.length >= MAX_PER_ORDER) return setNote(`You can buy ${MAX_PER_ORDER} seats at a time.`)
    setZoneId(zone)
    setSeats([...seats, code])
  }

  const zone = fixture.zones.find((z) => z.zone_id === zoneId)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const { checkout_url } = await checkout(fixture.id, zoneId, seats, wantJersey ? jersey : undefined)
      window.location.assign(checkout_url) // Stripe's hosted page; it sends the buyer back to /tickets
    } catch (err) {
      setError(err.message)
      setBusy(false)
      setSeats([]) // a seat may have just been taken: show the fresh map and let the buyer choose again
      setRound((n) => n + 1)
    }
  }

  return (
    <form className="buy" onSubmit={handleSubmit}>
      <h2>Choose your seats</h2>
      <Status loading={!seatMap && !mapError} error={mapError} />
      {seatMap && <ArenaMap seatMap={seatMap} zones={fixture.zones} selected={seats} onToggle={toggle} />}
      {note && <p className="message" role="status">{note}</p>}
      <div aria-live="polite">
        {seats.length > 0 ? (
          <ul className="picked-seats">
            {seats.map((c) => (
              <li key={c}>
                {formatSeat(c)}
                <button type="button" className="link-btn" aria-label={`Remove ${formatSeat(c)}`} onClick={() => setSeats(seats.filter((x) => x !== c))}>
                  &times;
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No seats chosen yet. Pick a sector on the plan, then a seat.</p>
        )}
      </div>
      <label className="check">
        <input type="checkbox" checked={wantJersey} onChange={(e) => setWantJersey(e.target.checked)} />
        Add the {fixture.home.name} jersey, picked up at this match
      </label>
      {wantJersey && <JerseyStudio homeSlug={fixture.home.slug} onChange={handleJersey} />}
      <p className="total">
        Total <strong>{formatPrice((zone ? zone.price_bani * seats.length : 0) + (wantJersey ? jerseyPrice : 0))}</strong>
      </p>
      {error && <p className="message error" role="alert">{error}</p>}
      <button type="submit" className="primary" disabled={busy || seats.length === 0 || (wantJersey && !jersey)}>
        {busy ? 'Opening payment...' : 'Pay with card'}
      </button>
      <p className="muted small">Test mode: use card 4242 4242 4242 4242, any future date and any CVC.</p>
    </form>
  )
}
