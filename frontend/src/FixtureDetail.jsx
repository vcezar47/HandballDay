import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { checkout, getFixture } from './api.js'
import ClubBadge from './ClubBadge.jsx'
import { formatDate, formatPrice, formatTime } from './format.js'
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
  const available = fixture.zones.filter((z) => z.seats_left > 0)
  const [zoneId, setZoneId] = useState(available[0]?.zone_id ?? '')
  const [quantity, setQuantity] = useState(1)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const zone = available.find((z) => z.zone_id === Number(zoneId))
  if (!zone) return <p className="muted">Sold out.</p>
  const most = Math.min(MAX_PER_ORDER, zone.seats_left)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const { checkout_url } = await checkout(fixture.id, zone.zone_id, Math.min(quantity, most))
      window.location.assign(checkout_url) // Stripe's hosted page; it sends the buyer back to /tickets
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <form className="buy" onSubmit={handleSubmit}>
      <label>
        Zone
        <select value={zone.zone_id} onChange={(e) => setZoneId(e.target.value)}>
          {available.map((z) => (
            <option key={z.zone_id} value={z.zone_id}>
              {z.name}: {formatPrice(z.price_bani)}
            </option>
          ))}
        </select>
      </label>
      <label>
        Tickets
        <select value={Math.min(quantity, most)} onChange={(e) => setQuantity(Number(e.target.value))}>
          {Array.from({ length: most }, (_, i) => i + 1).map((n) => (
            <option key={n}>{n}</option>
          ))}
        </select>
      </label>
      <p className="total">
        Total <strong>{formatPrice(zone.price_bani * Math.min(quantity, most))}</strong>
      </p>
      {error && <p className="message error" role="alert">{error}</p>}
      <button type="submit" className="primary" disabled={busy}>
        {busy ? 'Opening payment...' : 'Pay with card'}
      </button>
      <p className="muted small">Test mode: use card 4242 4242 4242 4242, any future date and any CVC.</p>
    </form>
  )
}
