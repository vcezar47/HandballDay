import { Link } from 'react-router'
import { getClubs } from './api.js'
import ClubBadge from './ClubBadge.jsx'
import Seo from './Seo.jsx'
import Status from './Status.jsx'
import useFetch from './useFetch.js'

export default function Clubs() {
  const { data: clubs, error } = useFetch(getClubs, [])

  return (
    <main className="content">
      <Seo title="Clubs" description="The 14 clubs of the Romanian Liga Florilor 2026/27: history, arena and upcoming matches." />
      <h1>Clubs</h1>
      <p className="muted">The 14 clubs of the Liga Florilor 2026/27.</p>
      <Status loading={!clubs && !error} error={error} />
      {clubs && (
        <ul className="grid">
          {clubs.map((c) => (
            <li key={c.slug}>
              <Link className="club-card" to={`/clubs/${c.slug}`} style={{ '--club': c.primary_color }}>
                <ClubBadge club={c} size={48} />
                <span>
                  <strong>{c.name}</strong>
                  <span className="sub">{c.city}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}
