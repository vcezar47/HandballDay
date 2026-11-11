import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { getConfig, login, register } from './api.js'
import PasswordInput from './PasswordInput.jsx'
import Turnstile from './Turnstile.jsx'

export default function AuthForm({ onLogin }) {
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [siteKey, setSiteKey] = useState('') // empty: no CAPTCHA on this server
  const [captcha, setCaptcha] = useState('')
  const [captchaRound, setCaptchaRound] = useState(0) // a token works once, so each attempt needs a fresh widget

  useEffect(() => {
    getConfig().then((c) => setSiteKey(c.turnstile_site_key))
  }, [])

  const isLogin = mode === 'login'

  function switchMode(next) {
    setMode(next)
    setError('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { user } = isLogin ? await login(email, password, captcha) : await register(email, displayName, password, captcha)
      onLogin(user)
    } catch (err) {
      setError(err.message)
      setCaptcha('')
      setCaptchaRound((n) => n + 1)
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

        {siteKey && <Turnstile key={captchaRound} siteKey={siteKey} onToken={setCaptcha} />}

        {error && <p className="message error">{error}</p>}

        <button type="submit" className="primary" disabled={loading || (siteKey && !captcha)}>
          {loading ? 'Please wait...' : isLogin ? 'Log in' : 'Sign up'}
        </button>
      </form>
    </div>
  )
}
