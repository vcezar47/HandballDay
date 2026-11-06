import { useSearchParams } from 'react-router'
import { getClubs, getFixtures } from './api.js'
import FixtureTable from './FixtureTable.jsx'
import Seo from './Seo.jsx'
import Status from './Status.jsx'
import useFetch from './useFetch.js'

// The filters live in the URL, so a filtered list can be bookmarked and the back button works.
export default function Fixtures() {
  const [params, setParams] = useSearchParams()
  const club = params.get('club') || ''
  const dateFrom = params.get('date_from') || ''
  const dateTo = params.get('date_to') || ''

  const { data: clubs } = useFetch(getClubs, [])
  const { data: fixtures, error } = useFetch(
    () => getFixtures({ club, date_from: dateFrom, date_to: dateTo, limit: 200 }),
    [club, dateFrom, dateTo],
  )

  function setFilter(name, value) {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    setParams(next, { replace: true })
  }

  return (
    <main className="content">
      <Seo title="Fixtures" description="Upcoming Liga Florilor 2026/27 matches: dates, venues and tickets." />
      <h1>Fixtures</h1>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <label>
          Club
          <select value={club} onChange={(e) => setFilter('club', e.target.value)}>
            <option value="">All clubs</option>
            {clubs?.map((c) => (
              <option key={c.slug} value={c.slug}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          From
          <input type="date" value={dateFrom} max={dateTo || undefined} onChange={(e) => setFilter('date_from', e.target.value)} />
        </label>
        <label>
          To
          <input type="date" value={dateTo} min={dateFrom || undefined} onChange={(e) => setFilter('date_to', e.target.value)} />
        </label>
        {params.size > 0 && (
          <button type="button" className="ghost small" onClick={() => setParams({}, { replace: true })}>
            Clear
          </button>
        )}
      </form>
      <Status loading={!fixtures && !error} error={error} />
      {fixtures && <FixtureTable fixtures={fixtures} />}
    </main>
  )
}
