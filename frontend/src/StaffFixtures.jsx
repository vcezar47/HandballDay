import { Link } from 'react-router'
import { getStaffFixtures } from './api.js'
import { formatDate, formatTime } from './format.js'
import Seo from './Seo.jsx'
import Status from './Status.jsx'
import useFetch from './useFetch.js'

export default function StaffFixtures() {
  const { data: fixtures, error } = useFetch(getStaffFixtures, [])

  return (
    <main className="content">
      <Seo title="Staff: fixtures" description="Manage your club's fixtures." />
      <h1>Your fixtures</h1>
      <p className="actions">
        <Link className="pill" to="/staff/fixtures/new">New fixture</Link>
        <Link className="pill" to="/staff/scan">Scan tickets</Link>
      </p>
      <Status loading={!fixtures && !error} error={error} />
      {fixtures && (
        <div className="table-wrap">
          <table>
            <caption className="sr-only">Fixtures hosted by your club</caption>
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Match</th>
                <th scope="col">Status</th>
                <th scope="col">Seats taken</th>
                <th scope="col"><span className="sr-only">Edit</span></th>
              </tr>
            </thead>
            <tbody>
              {fixtures.map((f) => {
                const quota = f.zones.reduce((n, z) => n + z.quota, 0)
                const left = f.zones.reduce((n, z) => n + z.seats_left, 0)
                return (
                  <tr key={f.id}>
                    <td className="when">
                      {formatDate(f.kickoff_at)}
                      <span className="sub">{formatTime(f.kickoff_at)}</span>
                    </td>
                    <td>{f.home.name} <span className="vs">vs</span> {f.away.name}</td>
                    <td>{f.status}</td>
                    <td>{quota - left} / {quota}</td>
                    <td>
                      <Link className="pill" to={`/staff/fixtures/${f.id}`}>Edit</Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  )
}
