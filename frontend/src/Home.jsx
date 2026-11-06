import { Link } from 'react-router'
import { getFixtures } from './api.js'
import Carousel from './Carousel.jsx'
import Seo from './Seo.jsx'
import useFetch from './useFetch.js'

export default function Home({ user }) {
  const { data: fixtures } = useFetch(() => getFixtures({ limit: 5 }), [])

  return (
    <main className="home">
      <Seo title="" />
      <p className="eyebrow">HandballDay</p>
      <h1 className="mystery">Something is taking shape</h1>

      {user ? (
        <p className="lede">
          Welcome back, <strong>{user.display_name}</strong>. The door is open.
        </p>
      ) : (
        <>
          <p className="lede">Not everything is ready to be seen. Step inside.</p>
          <Link className="enter" to="/login">
            Enter
          </Link>
        </>
      )}

      {fixtures && <Carousel fixtures={fixtures} />}
    </main>
  )
}
