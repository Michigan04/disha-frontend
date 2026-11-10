// Calls to the Disha backend (FastAPI). In development Vite forwards /api to
// http://localhost:8000 (see vite.config.js); set VITE_API_URL for a deployed backend.

const BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')
const KEY = 'disha.session'

let token = null
let onSignedOut = () => {}

export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

// ---------- Session (token and user), kept in this browser ----------

export function readSession() {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || sessionStorage.getItem(KEY) || 'null')
    if (saved?.token && saved?.user) {
      token = saved.token
      return saved.user
    }
  } catch {
    /* storage unavailable or an old value: start signed out */
  }
  return null
}

export function saveSession(newToken, user, remember) {
  token = newToken
  try {
    localStorage.removeItem(KEY)
    sessionStorage.removeItem(KEY)
    ;(remember ? localStorage : sessionStorage).setItem(KEY, JSON.stringify({ token, user }))
  } catch {
    /* storage unavailable: signed in for this visit only */
  }
}

export function clearSession() {
  token = null
  try {
    localStorage.removeItem(KEY)
    sessionStorage.removeItem(KEY)
  } catch {
    /* nothing to clear */
  }
}

/** Called when the server says the session is no longer valid. */
export function whenSignedOut(fn) {
  onSignedOut = fn
}

// ---------- Requests ----------

const ISO_DATE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/
// The pages work with Date objects, so timestamps are turned into Dates as they arrive.
const revive = (_, value) => (typeof value === 'string' && ISO_DATE.test(value) ? new Date(value) : value)

function messageFrom(detail, status) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => d.msg).filter(Boolean).join(' ') || 'The request was not valid.'
  if (detail?.message) return detail.message
  return status >= 500 ? 'The server had a problem. Try again in a minute.' : 'The request could not be completed.'
}

async function request(method, path, { body, form, raw } = {}) {
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  let res
  try {
    res = await fetch(BASE + path, { method, headers, body: form || (body !== undefined ? JSON.stringify(body) : undefined) })
  } catch {
    throw new ApiError('The server could not be reached. Check that the backend is running.', 0)
  }
  if (res.status === 401 && token && !path.startsWith('/auth/login')) {
    clearSession()
    onSignedOut()
  }
  if (raw && res.ok) return res.text()
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text, revive) : null
  } catch {
    /* not JSON: handled below */
  }
  if (!res.ok) throw new ApiError(messageFrom(data?.detail, res.status), res.status, data?.detail)
  return data
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, { body: body ?? {} }),
  put: (path, body) => request('PUT', path, { body }),
  patch: (path, body) => request('PATCH', path, { body }),
  upload: (path, fields) => {
    const form = new FormData()
    for (const [k, v] of Object.entries(fields)) form.append(k, v)
    return request('POST', path, { form })
  },
  text: (path) => request('GET', path, { raw: true }),
}
