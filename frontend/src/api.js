// The session lives in an HttpOnly cookie the browser sends by itself; JS never sees it.
// Writes also need the CSRF token (see backend/app/security/csrf.py), fetched once and cached.
let csrfToken = null

async function loadCsrf() {
  const res = await fetch('/api/csrf')
  csrfToken = (await res.json()).csrf_token
}

async function request(method, path, body, headers = {}, retried = false) {
  const write = method !== 'GET'
  const raw = body instanceof Blob // a file goes up as the raw body; everything else is JSON
  let res
  try {
    if (write && !csrfToken) await loadCsrf()
    res = await fetch(`/api${path}`, {
      method,
      headers: {
        ...(raw && { 'Content-Type': 'application/octet-stream', 'X-Filename': encodeURIComponent(body.name) }),
        ...(body && !raw && { 'Content-Type': 'application/json' }),
        ...(write && { 'X-CSRF-Token': csrfToken }),
        ...headers,
      },
      body: body && (raw ? body : JSON.stringify(body)),
    })
  } catch {
    throw new Error('Cannot reach the server. Is the backend running?')
  }

  const data = await res.json().catch(() => ({}))
  if (res.status === 403 && data.code === 'csrf_failed' && !retried) {
    csrfToken = null // cookie expired or was cleared: get a fresh token and try once more
    return request(method, path, body, headers, true)
  }
  if (!res.ok) {
    // FastAPI sends a string for HTTP errors and a list for validation errors.
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail
    throw new Error(detail || 'Something went wrong')
  }
  return data
}

export const register = (email, displayName, password, captchaToken) =>
  request('POST', '/auth/register', { email, display_name: displayName, password, captcha_token: captchaToken })
export const login = (email, password, captchaToken) =>
  request('POST', '/auth/login', { email, password, captcha_token: captchaToken })
export const logout = () => request('POST', '/auth/logout')
export const me = () => request('GET', '/auth/me')

export const checkout = (fixtureId, zoneId, quantity, jersey) =>
  request('POST', '/checkout', { fixture_id: fixtureId, zone_id: zoneId, quantity, jersey })
export const getJerseyCatalog = () => request('GET', '/jersey-templates')
export const getJerseys = () => request('GET', '/jerseys')
export const uploadLogo = (file, captchaToken) =>
  request('POST', '/uploads', file, captchaToken ? { 'X-Captcha-Token': captchaToken } : {})

// The Turnstile site key (empty = no CAPTCHA). Asked once; a failure means "off", and is asked again next time.
let configPromise
export const getConfig = () =>
  (configPromise ??= request('GET', '/config').catch(() => {
    configPromise = undefined
    return { turnstile_site_key: '' }
  }))

export const getAdminUsers = () => request('GET', '/admin/users')
export const setUserRole = (id, role, club) => request('PATCH', `/admin/users/${id}`, { role, club })
export const updateClub = (slug, body) => request('PATCH', `/admin/clubs/${encodeURIComponent(slug)}`, body)
export const getAdminUploads = () => request('GET', '/admin/uploads')
export const deleteUpload = (id) => request('DELETE', `/admin/uploads/${id}`)
export const getActivity = (event) => request('GET', `/admin/activity?limit=200${event ? `&event=${encodeURIComponent(event)}` : ''}`)
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
