async function post(path, body) {
  let res
  try {
    res = await fetch(`/api${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new Error('Cannot reach the server. Is the backend running?')
  }

  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    // FastAPI sends a string for HTTP errors and a list for validation errors.
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail
    throw new Error(detail || 'Something went wrong')
  }
  return data
}

export const register = (email, displayName, password) =>
  post('/auth/register', { email, display_name: displayName, password })
export const login = (email, password) => post('/auth/login', { email, password })
