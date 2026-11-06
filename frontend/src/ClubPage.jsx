import { Link, useParams } from 'react-router'
import { getClub, getFixtures } from './api.js'
import ClubBadge from './ClubBadge.jsx'
import FixtureTable from './FixtureTable.jsx'
import Seo from './Seo.jsx'
import Status from './Status.jsx'
import useFetch from './useFetch.js'

export default function ClubPage() {
  const { slug } = useParams()
  const { data: club, error } = useFetch(() => getClub(slug), [slug])
  const { data: fixtures } = useFetch(() => getFixtures({ club: slug, limit: 8 }), [slug])

  return (
    <main className="content">
      <Link className="back" to="/clubs">&larr; All clubs</Link>
      <Status loading={!club && !error} error={error} />
      {club && (
        <>
          <Seo title={club.name} description={`${club.name} from ${club.city}: club history, arena and upcoming matches.`} />
          <header className="club-head">
            <ClubBadge club={club} size={84} />
            <div>
              <h1>{club.name}</h1>
              <p className="muted">
                {club.city} &middot; founded {club.founded_year}
              </p>
            </div>
          </header>
          <p className="prose">{club.description}</p>
          <dl className="facts">
            <div>
              <dt>Arena</dt>
              <dd>{club.venue}</dd>
            </div>
            <div>
              <dt>Capacity</dt>
              <dd>{club.capacity.toLocaleString('en-GB')}</dd>
            </div>
            <div>
              <dt>Colours</dt>
              <dd>
                <span className="swatch" style={{ background: club.primary_color }} title={club.primary_color} />
                <span className="swatch" style={{ background: club.secondary_color }} title={club.secondary_color} />
              </dd>
            </div>
          </dl>
          <h2>Next matches</h2>
          {fixtures && <FixtureTable fixtures={fixtures} />}
          <p>
            <Link to={`/fixtures?club=${club.slug}`}>All matches of {club.name} &rarr;</Link>
          </p>
        </>
      )}
    </main>
  )
}
