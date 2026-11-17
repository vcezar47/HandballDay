import { Link } from 'react-router'
import { getClubs, getFixtures } from './api.js'
import Carousel from './Carousel.jsx'
import ClubBlocks from './ClubBlocks.jsx'
import Jersey from './Jersey.jsx'
import Seo from './Seo.jsx'
import useFetch from './useFetch.js'

export default function Home({ user }) {
  const { data: fixtures } = useFetch(() => getFixtures({ limit: 5 }), [])
  const { data: clubs } = useFetch(getClubs, [])
  const sample = fixtures?.[0]?.home // the jersey panel wears the colours of the next home team

  return (
    <main className="home">
      <Seo title="" />
      <section className="hero">
        <h1>
          Your seat on the <em>9-metre</em> line.
        </h1>
        <div>
          <p>
            {user && (
              <>
                Welcome back, <strong>{user.display_name}</strong>.{' '}
              </>
            )}
            Pick a Liga Florilor match, choose your stand, and get a QR ticket in minutes. Add a jersey in your club&apos;s colours and
            collect it at the hall.
          </p>
          <div className="hero-actions">
            <Link className="btn" to="/fixtures">
              Browse fixtures
            </Link>
            <Link className="ghost" to="/clubs">
              Pick a club
            </Link>
          </div>
        </div>
      </section>

      {fixtures && <Carousel fixtures={fixtures} />}

      <section aria-labelledby="clubs-heading">
        <h2 id="clubs-heading">14 clubs. 14 colours.</h2>
        {clubs && <ClubBlocks clubs={clubs} />}
      </section>

      <section className="split">
        <div className="panel dark">
          <h2>Buy once. Walk in with a QR.</h2>
          <ol className="steps">
            <li>
              <strong>Pick</strong>a match and a stand
            </li>
            <li>
              <strong>Pay</strong>once through Stripe
            </li>
            <li>
              <strong>Scan</strong>at the door, done
            </li>
          </ol>
        </div>
        <div className="panel orange">
          <div>
            <h2>Wear your club&apos;s number.</h2>
            <p>Design a jersey, preview it live, and add it to the same checkout. Pick it up at the match.</p>
          </div>
          {sample && <Jersey primary={sample.primary_color} secondary={sample.secondary_color} name="YOU" number="7" label={`${sample.name} jersey`} />}
        </div>
      </section>
    </main>
  )
}
