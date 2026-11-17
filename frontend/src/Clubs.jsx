import { getClubs } from './api.js'
import ClubBlocks from './ClubBlocks.jsx'
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
      {clubs && <ClubBlocks clubs={clubs} />}
    </main>
  )
}
