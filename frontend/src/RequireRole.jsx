import { Navigate } from 'react-router'

// UX only: it hides pages from people who cannot use them. The server checks every request itself.
export default function RequireRole({ user, roles, children }) {
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />
  return children
}
