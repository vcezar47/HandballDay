import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { createFixture, getClubs, getFixture, getStaffZones, updateFixture } from './api.js'
import Seo from './Seo.jsx'
import Status from './Status.jsx'

// shortcut: the kickoff is typed in the browser's own timezone; fine for staff in Romania, wrong for anyone elsewhere.
const toInput = (iso) => {
  const d = new Date(iso)
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

// Create (/staff/fixtures/new) and edit (/staff/fixtures/:id) share this form.
export default function StaffFixtureForm() {
  const { id } = useParams()
  const editing = Boolean(id)
  const navigate = useNavigate()
  const [clubs, setClubs] = useState([])
  const [away, setAway] = useState('')
  const [kickoff, setKickoff] = useState('')
  const [status, setStatus] = useState('scheduled')
  const [zones, setZones] = useState(null) // [{ zone_id, name, capacity, price (lei), quota }]
  const [error, setError] = useState('')
  const [loadError, setLoadError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let stale = false
    const load = editing
      ? getFixture(id).then((f) => {
          setKickoff(toInput(f.kickoff_at))
          setStatus(f.status)
          return f.zones.map((z) => ({ zone_id: z.zone_id, name: z.name, capacity: 100000, price: z.price_bani / 100, quota: z.quota }))
        })
      : Promise.all([getClubs(), getStaffZones()]).then(([c, z]) => {
          setClubs(c)
          return z.map((v) => ({ zone_id: v.id, name: v.name, capacity: v.capacity, price: 50, quota: v.capacity }))
        })
    load.then((rows) => !stale && setZones(rows)).catch((err) => !stale && setLoadError(err.message))
    return () => {
      stale = true
    }
  }, [id, editing])

  function setZone(i, field, value) {
    setZones(zones.map((z, j) => (i === j ? { ...z, [field]: value } : z)))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    const body = {
      kickoff_at: new Date(kickoff).toISOString(),
      zones: zones.map((z) => ({ zone_id: z.zone_id, price_bani: Math.round(Number(z.price) * 100), quota: Number(z.quota) })),
    }
    try {
      if (editing) await updateFixture(id, { ...body, status })
      else await createFixture({ ...body, away_club: away })
      navigate('/staff')
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <main className="content narrow">
      <Seo title={editing ? 'Staff: edit fixture' : 'Staff: new fixture'} description="Set kickoff, prices and quotas." />
      <Link className="back" to="/staff">&larr; Your fixtures</Link>
      <h1>{editing ? 'Edit fixture' : 'New fixture'}</h1>
      <Status loading={!zones && !loadError} error={loadError} />
      {zones && (
        <form onSubmit={handleSubmit}>
          {!editing && (
            <label>
              Away club
              <select value={away} onChange={(e) => setAway(e.target.value)} required>
                <option value="">Choose...</option>
                {clubs.map((c) => (
                  <option key={c.slug} value={c.slug}>{c.name}</option>
                ))}
              </select>
            </label>
          )}
          <label>
            Kickoff
            <input type="datetime-local" value={kickoff} onChange={(e) => setKickoff(e.target.value)} required />
          </label>
          {editing && (
            <label>
              Status
              <select value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="scheduled">Scheduled</option>
                <option value="finished">Finished</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </label>
          )}
          <fieldset>
            <legend>Zones</legend>
            {zones.map((z, i) => (
              <div className="zone-row" key={z.zone_id}>
                <strong>{z.name}</strong>
                <label>
                  Price (lei)
                  <input type="number" min="0" max="10000" step="0.5" value={z.price} onChange={(e) => setZone(i, 'price', e.target.value)} required />
                </label>
                <label>
                  Seats on sale
                  <input type="number" min="0" max={z.capacity} step="1" value={z.quota} onChange={(e) => setZone(i, 'quota', e.target.value)} required />
                </label>
              </div>
            ))}
          </fieldset>
          {error && <p className="message error" role="alert">{error}</p>}
          <button type="submit" className="primary" disabled={busy}>
            {busy ? 'Saving...' : 'Save'}
          </button>
        </form>
      )}
    </main>
  )
}
