import { useState } from 'react'
import {
  deleteUpload, getActivity, getAdminUploads, getAdminUsers, getClub, getClubs, setUserRole, updateClub,
} from './api.js'
import Seo from './Seo.jsx'
import Status from './Status.jsx'
import useFetch from './useFetch.js'

const TABS = ['Users', 'Clubs', 'Uploads', 'Activity']

// Everything here is plain React text. The server is the one that decides who may call these routes.
export default function Admin() {
  const [tab, setTab] = useState('Users')
  return (
    <main className="content">
      <Seo title="Admin" description="Manage users, clubs and uploads." />
      <h1>Admin</h1>
      <div className="tabs" role="tablist">
        {TABS.map((t) => (
          <button key={t} type="button" role="tab" aria-selected={tab === t} className={tab === t ? 'tab active' : 'tab'} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>
      {tab === 'Users' && <Users />}
      {tab === 'Clubs' && <Clubs />}
      {tab === 'Uploads' && <Uploads />}
      {tab === 'Activity' && <Activity />}
    </main>
  )
}

function Users() {
  const [reload, setReload] = useState(0)
  const { data: users, error } = useFetch(getAdminUsers, [reload])
  const { data: clubs } = useFetch(getClubs, [])
  return (
    <>
      <Status loading={!users && !error} error={error} />
      {users && clubs && (
        <div className="table-wrap">
          <table>
            <caption className="sr-only">Users and their roles</caption>
            <thead>
              <tr>
                <th scope="col">User</th>
                <th scope="col">Role</th>
                <th scope="col">Club (staff)</th>
                <th scope="col"><span className="sr-only">Save</span></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <UserRow key={`${u.id}-${u.role}-${u.club}`} user={u} clubs={clubs} onSaved={() => setReload((n) => n + 1)} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

function UserRow({ user, clubs, onSaved }) {
  const [role, setRole] = useState(user.role)
  const [club, setClub] = useState(user.club ?? '')
  const [state, setState] = useState('') // '', 'saving' or an error message
  const changed = role !== user.role || (role === 'staff' && club !== (user.club ?? ''))

  async function save() {
    setState('saving')
    try {
      await setUserRole(user.id, role, role === 'staff' ? club : null)
      onSaved()
    } catch (err) {
      setState(err.message)
    }
  }

  return (
    <tr>
      <td>
        {user.display_name}
        <span className="sub">{user.email}</span>
      </td>
      <td>
        <select aria-label={`Role of ${user.email}`} value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="fan">fan</option>
          <option value="staff">staff</option>
          <option value="admin">admin</option>
        </select>
      </td>
      <td>
        <select aria-label={`Club of ${user.email}`} value={club} disabled={role !== 'staff'} onChange={(e) => setClub(e.target.value)}>
          <option value="">none</option>
          {clubs.map((c) => (
            <option key={c.slug} value={c.slug}>{c.name}</option>
          ))}
        </select>
      </td>
      <td>
        <button type="button" className="pill" disabled={!changed || state === 'saving'} onClick={save}>Save</button>
        {state && state !== 'saving' && <span className="sub error-text">{state}</span>}
      </td>
    </tr>
  )
}

function Clubs() {
  const { data: clubs } = useFetch(getClubs, [])
  const [slug, setSlug] = useState('')
  return (
    <>
      <label>
        Club
        <select value={slug} onChange={(e) => setSlug(e.target.value)}>
          <option value="">Choose...</option>
          {clubs?.map((c) => (
            <option key={c.slug} value={c.slug}>{c.name}</option>
          ))}
        </select>
      </label>
      {slug && <ClubForm key={slug} slug={slug} />}
    </>
  )
}

function ClubForm({ slug }) {
  const { data: club, error } = useFetch(() => getClub(slug), [slug])
  const [form, setForm] = useState(null)
  const [message, setMessage] = useState(null) // { ok, text }
  const values = form ?? (club && { description: club.description, primary: club.primary_color, secondary: club.secondary_color, year: club.founded_year })

  async function handleSubmit(e) {
    e.preventDefault()
    setMessage(null)
    try {
      await updateClub(slug, { description: values.description, primary_color: values.primary, secondary_color: values.secondary, founded_year: Number(values.year) })
      setMessage({ ok: true, text: 'Saved.' })
    } catch (err) {
      setMessage({ ok: false, text: err.message })
    }
  }
  const set = (field) => (e) => setForm({ ...values, [field]: e.target.value })

  if (error) return <p className="message error">{error}</p>
  if (!values) return <Status loading />
  return (
    <form onSubmit={handleSubmit} className="club-form">
      <label>
        Description
        <textarea rows={6} maxLength={2000} value={values.description} onChange={set('description')} required />
      </label>
      <div className="colour-row">
        <label>
          Main colour
          <input type="color" value={values.primary} onChange={set('primary')} />
        </label>
        <label>
          Trim colour
          <input type="color" value={values.secondary} onChange={set('secondary')} />
        </label>
      </div>
      <label>
        Founded
        <input type="number" min="1800" max="2100" value={values.year} onChange={set('year')} required />
      </label>
      {message && <p className={message.ok ? 'message success' : 'message error'} role="status">{message.text}</p>}
      <button type="submit" className="primary">Save club</button>
    </form>
  )
}

function Uploads() {
  const [reload, setReload] = useState(0)
  const [error, setError] = useState('')
  const { data: uploads, error: loadError } = useFetch(getAdminUploads, [reload])

  async function remove(id) {
    if (!window.confirm('Delete this upload? Jerseys that use it will lose their logo.')) return
    setError('')
    try {
      await deleteUpload(id)
      setReload((n) => n + 1)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <Status loading={!uploads && !loadError} error={loadError || error} />
      {uploads?.length === 0 && <p className="muted">No uploads.</p>}
      <ul className="grid uploads">
        {uploads?.map((u) => (
          <li key={u.id} className="upload-card">
            <img src={`/api/uploads/${u.id}`} alt={`Upload ${u.id} by ${u.owner_email}`} width="120" height="120" />
            <p>
              #{u.id} &middot; {Math.max(1, Math.round(u.size_bytes / 1024))} KB
              <span className="sub">{u.owner_email}</span>
              <span className="sub">{u.in_use ? 'used on a jersey' : 'not used'}</span>
            </p>
            <button type="button" className="pill" onClick={() => remove(u.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </>
  )
}

const EVENTS = [
  'login', 'login_failed', 'logout', 'register', 'forbidden', 'csrf_failed', 'captcha_failed', 'checkout_started',
  'payment_succeeded', 'payment_rejected', 'payment_expired', 'scan_ok', 'scan_rejected', 'upload_ok',
  'upload_rejected', 'upload_removed', 'role_changed', 'club_updated', 'fixture_created', 'fixture_updated',
]

function Activity() {
  const [event, setEvent] = useState('')
  const [reload, setReload] = useState(0)
  const { data: entries, error } = useFetch(() => getActivity(event), [event, reload])
  return (
    <>
      <div className="filters">
        <label>
          Event
          <select value={event} onChange={(e) => setEvent(e.target.value)}>
            <option value="">All events</option>
            {EVENTS.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
        <button type="button" className="ghost small" onClick={() => setReload((n) => n + 1)}>Refresh</button>
      </div>
      <Status loading={!entries && !error} error={error} />
      {entries?.length === 0 && <p className="muted">Nothing logged yet.</p>}
      {entries?.length > 0 && (
        <div className="table-wrap">
          <table>
            <caption className="sr-only">Newest activity first</caption>
            <thead>
              <tr>
                <th scope="col">Time</th>
                <th scope="col">Event</th>
                <th scope="col">Details</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e, i) => (
                <tr key={`${e.time}-${i}`}>
                  <td className="when">{e.time}</td>
                  <td>{e.event}</td>
                  <td className="details">{JSON.stringify(e.fields)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
