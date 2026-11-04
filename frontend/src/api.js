// The session lives in an HttpOnly cookie the browser sends by itself; JS never sees it.
// Writes also need the CSRF token (see backend/app/security/csrf.py), fetched once and cached.
let csrfToken = null

async function loadCsrf() {
  const res = await fetch('/api/csrf')
  csrfToken = (await res.json()).csrf_token
}

async function request(method, path, body, retried = false) {
  const write = method !== 'GET'
  let res
  try {
    if (write && !csrfToken) await loadCsrf()
    res = await fetch(`/api${path}`, {
      method,
      headers: {
        ...(body && { 'Content-Type': 'application/json' }),
        ...(write && { 'X-CSRF-Token': csrfToken }),
      },
      body: body && JSON.stringify(body),
    })
  } catch {
    throw new Error('Cannot reach the server. Is the backend running?')
  }

  const data = await res.json().catch(() => ({}))
  if (res.status === 403 && data.code === 'csrf_failed' && !retried) {
    csrfToken = null // cookie expired or was cleared: get a fresh token and try once more
    return request(method, path, body, true)
  }
  if (!res.ok) {
    // FastAPI sends a string for HTTP errors and a list for validation errors.
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail
    throw new Error(detail || 'Something went wrong')
  }
  return data
}

export const register = (email, displayName, password) =>
  request('POST', '/auth/register', { email, display_name: displayName, password })
export const login = (email, password) => request('POST', '/auth/login', { email, password })
export const logout = () => request('POST', '/auth/logout')
export const me = () => request('GET', '/auth/me')
