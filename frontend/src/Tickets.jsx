import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { QRCodeSVG } from 'qrcode.react'
import { getJerseys, getTickets } from './api.js'
import { formatDate, formatPrice } from './format.js'
import Jersey from './Jersey.jsx'
import Seo from './Seo.jsx'
import Status from './Status.jsx'
import Ticket from './Ticket.jsx'

const POLLS_AFTER_PAYMENT = 5
const POLL_MS = 2500

export default function Tickets() {
  const [params] = useSearchParams()
  const justPaid = params.get('paid') === '1'
  const [tickets, setTickets] = useState(null)
  const [jerseys, setJerseys] = useState([])
  const [error, setError] = useState('')
  const [polls, setPolls] = useState(0)

  // Stripe confirms the payment to our server a moment after redirecting the buyer here,
  // so right after paying we ask a few times before concluding that nothing arrived.
  useEffect(() => {
    let stale = false
    Promise.all([getTickets(), getJerseys()])
      .then(([t, j]) => {
        if (stale) return
        setTickets(t)
        setJerseys(j)
      })
      .catch((err) => !stale && setError(err.message))
    return () => {
      stale = true
    }
  }, [polls])

  useEffect(() => {
    if (!justPaid || polls >= POLLS_AFTER_PAYMENT) return
    const timer = setTimeout(() => setPolls((n) => n + 1), POLL_MS)
    return () => clearTimeout(timer)
  }, [justPaid, polls])

  return (
    <main className="content">
      <Seo title="My tickets" description="Your match tickets with their QR codes." />
      <h1>My tickets</h1>
      {justPaid && <p className="message success" role="status">Payment received. Thank you!</p>}
      <Status loading={!tickets && !error} error={error} />
      {tickets && tickets.length === 0 && (
        <p className="muted">
          {justPaid ? 'Your tickets are being issued, this page updates by itself.' : 'No tickets yet.'}{' '}
          <Link to="/fixtures">Browse fixtures</Link>
        </p>
      )}
      {jerseys.length > 0 && (
        <>
          <h2>My jerseys</h2>
          <ul className="tickets">
            {jerseys.map((j) => (
              <li key={j.id} className="jersey-card">
                <div className="jersey-thumb">
                  <Jersey
                    template={j.template}
                    primary={j.primary_color}
                    secondary={j.secondary_color}
                    name={j.name_text}
                    number={j.number}
                    logoUrl={j.logo_upload_id ? `/api/uploads/${j.logo_upload_id}` : undefined}
                  />
                </div>
                <div>
                  <h2>
                    {j.club.name} #{j.number} {j.name_text}
                  </h2>
                  <p>Size {j.size} &middot; {formatPrice(j.price_bani)}</p>
                  <p className="muted">
                    Pick up at {j.pickup.home.name} vs {j.pickup.away.name}, {formatDate(j.pickup.kickoff_at)}
                  </p>
                </div>
              </li>
            ))}
          </ul>
          <h2>Tickets</h2>
        </>
      )}
      {tickets && (
        <ul className="tickets">
          {tickets.map((t) => (
            <li key={t.id} className="ticket-item">
              <Ticket
                fixture={t.fixture}
                used={t.status === 'used'}
                details={[
                  ['Venue', t.fixture.venue],
                  ['Zone', t.zone],
                  ['Price', formatPrice(t.price_bani)],
                ]}
              >
                {/* white plate and quiet zone: scanners need dark-on-light with a margin */}
                <div className="qr">
                  <QRCodeSVG value={t.code} size={130} marginSize={0} title={`QR code for ticket ${t.id}`} />
                </div>
                <p className={t.status === 'used' ? 'chip used' : 'chip'}>{t.status === 'used' ? 'Used' : 'Valid'}</p>
              </Ticket>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}
