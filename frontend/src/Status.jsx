// Loading / error line shared by every page that fetches.
export default function Status({ loading, error }) {
  if (error) return <p className="message error" role="alert">{error}</p>
  if (loading) return <p className="muted" aria-live="polite">Loading...</p>
  return null
}
