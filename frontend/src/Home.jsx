import { Link } from 'react-router'

export default function Home({ user, onLogout }) {
  return (
    <main className="home">
      <p className="eyebrow">HandballDay</p>
      <h1 className="mystery">Something is taking shape</h1>

      {user ? (
        <>
          <p className="lede">
            Welcome back, <strong>{user.display_name}</strong>. The door is open.
          </p>
          <button type="button" className="ghost" onClick={onLogout}>
            Leave
          </button>
        </>
      ) : (
        <>
          <p className="lede">Not everything is ready to be seen. Step inside.</p>
          <Link className="enter" to="/login">
            Enter
          </Link>
        </>
      )}
    </main>
  )
}
