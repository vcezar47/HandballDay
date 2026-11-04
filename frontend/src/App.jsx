import { useState } from 'react'
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router'
import AuthForm from './AuthForm.jsx'
import FlowBackground from './FlowBackground.jsx'
import Home from './Home.jsx'

const STORAGE_KEY = 'handballday-user'

function loadUser() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY))
  } catch {
    return null
  }
}

export default function App() {
  const [user, setUser] = useState(loadUser)
  const navigate = useNavigate()
  const { pathname } = useLocation()

  function handleLogin(u) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u))
    setUser(u)
    navigate('/')
  }

  function handleLogout() {
    localStorage.removeItem(STORAGE_KEY)
    setUser(null)
  }

  return (
    <>
      <FlowBackground />
      <div className="stage" key={pathname}>
        <Routes>
          <Route path="/" element={<Home user={user} onLogout={handleLogout} />} />
          <Route path="/login" element={user ? <Navigate to="/" replace /> : <AuthForm onLogin={handleLogin} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </>
  )
}
