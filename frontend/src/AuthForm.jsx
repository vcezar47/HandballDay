import { useState } from 'react'
import { Link } from 'react-router'
import { login, register } from './api.js'
import PasswordInput from './PasswordInput.jsx'

export default function AuthForm({ onLogin }) {
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [loading, setLoading] = useState(false)

  const isLogin = mode === 'login'

  function switchMode(next) {
    setMode(next)
    setError('')
    setInfo('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setInfo('')
    setLoading(true)
    try {
      if (isLogin) {
        const { user } = await login(email, password)
        onLogin(user)
      } else {
        await register(email, displayName, password)
        setMode('login')
        setPassword('')
        setInfo('Account created. You can log in now.')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <Link className="back" to="/">
        &larr; Back
      </Link>
      <h1>{isLogin ? 'Welcome back' : 'Create an account'}</h1>

      <div className="tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={isLogin}
          className={isLogin ? 'tab active' : 'tab'}
          onClick={() => switchMode('login')}
        >
          Log in
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={!isLogin}
          className={!isLogin ? 'tab active' : 'tab'}
          onClick={() => switchMode('signup')}
        >
          Sign up
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            maxLength={254}
            autoComplete="email"
            required
          />
        </label>

        {!isLogin && (
          <label>
            Display name
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              minLength={2}
              maxLength={50}
              autoComplete="nickname"
              required
            />
          </label>
        )}

        <label>
          Password
          <PasswordInput
            key={mode}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={isLogin ? 1 : 8}
            maxLength={100}
            autoComplete={isLogin ? 'current-password' : 'new-password'}
            required
          />
        </label>

        {error && <p className="message error">{error}</p>}
        {info && <p className="message success">{info}</p>}

        <button type="submit" className="primary" disabled={loading}>
          {loading ? 'Please wait...' : isLogin ? 'Log in' : 'Sign up'}
        </button>
      </form>
    </div>
  )
}
