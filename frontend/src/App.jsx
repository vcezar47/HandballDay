import { useEffect, useState } from 'react'
import AuthForm from './AuthForm.jsx'
import FlowBackground from './FlowBackground.jsx'
import Home from './Home.jsx'

const STORAGE_KEY = 'daw-user'

function loadUser() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY))
  } catch {
    return null
  }
}

const currentRoute = () => window.location.hash.replace(/^#/, '') || '/'

function useRoute() {
  const [route, setRoute] = useState(currentRoute)
  useEffect(() => {
    const onChange = () => setRoute(currentRoute())
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return route
}

export default function App() {
  const [user, setUser] = useState(loadUser)
  const route = useRoute()

  function handleLogin(u) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u))
    setUser(u)
    window.location.hash = '/'
  }

  function handleLogout() {
    localStorage.removeItem(STORAGE_KEY)
    setUser(null)
  }

  const showAuth = route === '/login' && !user

  return (
    <>
      <FlowBackground />
      <div className="stage" key={showAuth ? 'auth' : 'home'}>
        {showAuth ? <AuthForm onLogin={handleLogin} /> : <Home user={user} onLogout={handleLogout} />}
      </div>
    </>
  )
}
