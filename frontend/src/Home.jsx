export default function Home({ user, onLogout }) {
  return (
    <main className="home">
      <p className="eyebrow">DAW &middot; Project</p>
      <h1 className="mystery">Something is taking shape</h1>

      {user ? (
        <>
          <p className="lede">
            Welcome back, <strong>{user.username}</strong>. The door is open.
          </p>
          <button type="button" className="ghost" onClick={onLogout}>
            Leave
          </button>
        </>
      ) : (
        <>
          <p className="lede">Not everything is ready to be seen. Step inside.</p>
          <a className="enter" href="#/login">
            Enter
          </a>
        </>
      )}
    </main>
  )
}
