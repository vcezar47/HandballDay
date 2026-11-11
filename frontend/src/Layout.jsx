import { Link, NavLink } from 'react-router'

export default function Layout({ user, onLogout, children }) {
  return (
    <div className="stage">
      <header className="site-header">
        <Link className="brand" to="/">
          <img src="/logo.svg" alt="" width="28" height="28" />
          HandballDay
        </Link>
        <nav aria-label="Main">
          <NavLink to="/clubs">Clubs</NavLink>
          <NavLink to="/fixtures">Fixtures</NavLink>
          {user && <NavLink to="/tickets">My tickets</NavLink>}
          {user?.role === 'staff' && <NavLink to="/staff">Staff</NavLink>}
          {user?.role === 'admin' && <NavLink to="/admin">Admin</NavLink>}
          {user?.role === 'admin' && <NavLink to="/staff/scan">Scan</NavLink>}
          {user && (
            <button type="button" className="link-btn" onClick={onLogout}>
              Leave ({user.display_name})
            </button>
          )}
          {user === null && <NavLink to="/login">Log in</NavLink>}
        </nav>
      </header>
      {children}
      <footer className="site-footer">
        <p>Unofficial student project. Payments run in Stripe test mode and no real tickets are sold.</p>
        <p>
          <Link to="/clubs">Clubs</Link> &middot; <Link to="/fixtures">Fixtures</Link> &middot;{' '}
          <a href="/sitemap.xml">Sitemap</a>
        </p>
      </footer>
    </div>
  )
}
