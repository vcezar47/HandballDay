import ClubBadge from './ClubBadge.jsx'
import { formatDay, formatTime } from './format.js'

// A match ticket: club-colour band, kick-off, both teams, detail lines, and a stub on the right
// (the QR code, or a link) passed in as children. `details` is a list of [label, value].
export default function Ticket({ fixture: f, details = [], used = false, children }) {
  return (
    <div className={used ? 'ticket used' : 'ticket'}>
      <div className="ticket-main">
        <div className="band" aria-hidden="true">
          <span style={{ background: f.home.primary_color }} />
          <span style={{ background: f.away.primary_color }} />
        </div>
        <p className="kick">
          <strong>{formatDay(f.kickoff_at)}</strong>
          <span>Kick-off {formatTime(f.kickoff_at)}</span>
        </p>
        <h2 className="ticket-teams">
          <span className="team-line">
            <ClubBadge club={f.home} size={46} />
            <span>{f.home.name}</span>
          </span>
          <span className="sr-only">vs</span>
          <span className="team-line">
            <ClubBadge club={f.away} size={46} />
            <span>{f.away.name}</span>
          </span>
        </h2>
        <dl className="meta">
          {details.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </div>
      <div className="stub">{children}</div>
    </div>
  )
}
