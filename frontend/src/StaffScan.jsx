import { useRef, useState } from 'react'
import { Link } from 'react-router'
import { scanTicket } from './api.js'
import { formatDate, formatTime } from './format.js'
import Seo from './Seo.jsx'

// A code field first: a handheld scanner "types" the code and presses Enter, so it works here as is.
// shortcut: no camera scanning yet; add it with the BarcodeDetector API or a QR library if phones are needed at the door.
export default function StaffScan() {
  const [code, setCode] = useState('')
  const [result, setResult] = useState(null) // { ok, text }
  const [busy, setBusy] = useState(false)
  const input = useRef(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!code.trim()) return
    setBusy(true)
    try {
      const t = await scanTicket(code.trim())
      setResult({
        ok: true,
        text: `Valid: ${t.fixture.home.name} vs ${t.fixture.away.name}, ${t.zone}, ${formatDate(t.fixture.kickoff_at)} ${formatTime(t.fixture.kickoff_at)}. Checked in.`,
      })
    } catch (err) {
      setResult({ ok: false, text: err.message })
    } finally {
      setBusy(false)
      setCode('')
      input.current?.focus()
    }
  }

  return (
    <main className="content narrow">
      <Seo title="Staff: scan tickets" description="Validate tickets at the door." />
      <Link className="back" to="/staff">&larr; Your fixtures</Link>
      <h1>Scan tickets</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Ticket code
          <input ref={input} value={code} onChange={(e) => setCode(e.target.value)} maxLength={64} autoFocus autoComplete="off" spellCheck={false} />
        </label>
        <button type="submit" className="primary" disabled={busy}>Check ticket</button>
      </form>
      {result && (
        <p className={result.ok ? 'message success scan-result' : 'message error scan-result'} role="status">
          {result.text}
        </p>
      )}
    </main>
  )
}
