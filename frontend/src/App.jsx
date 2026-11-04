import { useEffect, useState } from 'react'
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router'
import { logout, me } from './api.js'
import AuthForm from './AuthForm.jsx'
import FlowBackground from './FlowBackground.jsx'
import Home from './Home.jsx'

export default function App() {
  // undefined = still asking the server, null = nobody logged in
  const [user, setUser] = useState(undefined)
  const navigate = useNavigate()
  const { pathname } = useLocation()

  useEffect(() => {
    me()
      .then(setUser)
      .catch(() => setUser(null))
  }, [])

  function handleLogin(u) {
    setUser(u)
    navigate('/')
  }

  async function handleLogout() {
    await logout().catch(() => {}) // the cookie is cleared server-side; if the call fails we still show logged out
    setUser(null)
  }

  return (
    <>
      <FlowBackground />
      <div className="stage" key={pathname}>
        {user !== undefined && (
          <Routes>
            <Route path="/" element={<Home user={user} onLogout={handleLogout} />} />
            <Route path="/login" element={user ? <Navigate to="/" replace /> : <AuthForm onLogin={handleLogin} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        )}
      </div>
    </>
  )
}
