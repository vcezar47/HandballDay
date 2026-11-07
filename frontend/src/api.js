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

export const checkout = (fixtureId, zoneId, quantity) =>
  request('POST', '/checkout', { fixture_id: fixtureId, zone_id: zoneId, quantity })
export const getTickets = () => request('GET', '/tickets')

export const getStaffFixtures = () => request('GET', '/staff/fixtures')
export const getStaffZones = () => request('GET', '/staff/zones')
export const createFixture = (body) => request('POST', '/staff/fixtures', body)
export const updateFixture = (id, body) => request('PATCH', `/staff/fixtures/${id}`, body)
export const scanTicket = (code) => request('POST', '/staff/scan', { code })

export const getClubs = () => request('GET', '/clubs')
export const getClub = (slug) => request('GET', `/clubs/${encodeURIComponent(slug)}`)
export const getFixture = (id) => request('GET', `/fixtures/${encodeURIComponent(id)}`)
// params: { club, date_from, date_to, limit }; empty values are left out
export const getFixtures = (params = {}) => {
  const query = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString()
  return request('GET', `/fixtures${query ? `?${query}` : ''}`)
}
