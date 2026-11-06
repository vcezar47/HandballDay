import { Link, useParams } from 'react-router'
import { getFixture } from './api.js'
import ClubBadge from './ClubBadge.jsx'
import { formatDate, formatPrice, formatTime } from './format.js'
import Seo from './Seo.jsx'
import Status from './Status.jsx'
import useFetch from './useFetch.js'

export default function FixtureDetail() {
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
          <p className="muted">Online ticket sales open soon.</p>
        </>
      )}
    </main>
  )
}
