import { Link } from 'react-router'
import ClubBadge from './ClubBadge.jsx'
import { formatDate, formatTime } from './format.js'

export default function FixtureTable({ fixtures }) {
  if (fixtures.length === 0) return <p className="muted">No upcoming matches found.</p>
  return (
    <div className="table-wrap">
      <table>
        <caption className="sr-only">Upcoming matches</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Match</th>
            <th scope="col" className="wide-only">Venue</th>
            <th scope="col"><span className="sr-only">Tickets</span></th>
          </tr>
        </thead>
        <tbody>
          {fixtures.map((f) => (
            <tr key={f.id}>
              <td className="when">
                {formatDate(f.kickoff_at)}
                <span className="sub">{formatTime(f.kickoff_at)}</span>
              </td>
              <td>
                <span className="teams">
                  <span className="side">
                    <ClubBadge club={f.home} size={26} />
                    <Link to={`/clubs/${f.home.slug}`}>{f.home.name}</Link>
                  </span>
                  <span className="vs">vs</span>
                  <span className="side">
                    <ClubBadge club={f.away} size={26} />
                    <Link to={`/clubs/${f.away.slug}`}>{f.away.name}</Link>
                  </span>
                </span>
              </td>
              <td className="wide-only">{f.venue}</td>
              <td>
                <Link className="pill" to={`/fixtures/${f.id}`}>
                  Details<span className="sr-only"> for {f.home.name} vs {f.away.name}</span>
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
