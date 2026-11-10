// Calls to the Disha backend (FastAPI). In development Vite forwards /api to
// http://localhost:8000 (see vite.config.js); set VITE_API_URL for a deployed backend.

const BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')
const KEY = 'disha.session'

let token = null
let onSignedOut = () => {}
// Last response and its ETag per path, for conditional GETs (see api.fresh).
const copies = new Map()

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

/** Store a refreshed copy of the signed-in user, keeping the token where it is. */
export function updateSessionUser(user) {
  try {
    for (const store of [localStorage, sessionStorage]) {
      const saved = JSON.parse(store.getItem(KEY) || 'null')
      if (saved?.token) store.setItem(KEY, JSON.stringify({ ...saved, user }))
    }
  } catch {
    /* storage unavailable: the new details last for this visit */
  }
}

export function clearSession() {
  token = null
  copies.clear()
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

async function request(method, path, { body, form, raw, conditional } = {}) {
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const copy = conditional ? copies.get(path) : null
  if (copy) headers['If-None-Match'] = copy.etag
  let res
  try {
    res = await fetch(BASE + path, {
      method, headers, body: form || (body !== undefined ? JSON.stringify(body) : undefined),
      // Conditional GETs manage their own copy, so skip the browser's HTTP cache.
      cache: conditional ? 'no-store' : 'default',
    })
  } catch {
    throw new ApiError('The server could not be reached. Check that the backend is running.', 0)
  }
  if (res.status === 401 && token && !path.startsWith('/auth/login')) {
    clearSession()
    onSignedOut()
  }
  if (res.status === 304 && copy) return { data: copy.data, changed: false }
  if (raw && res.ok) return res.text()
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text, revive) : null
  } catch {
    /* not JSON: handled below */
  }
  if (!res.ok) throw new ApiError(messageFrom(data?.detail, res.status), res.status, data?.detail)
  if (conditional) {
    const etag = res.headers.get('ETag')
    if (etag) copies.set(path, { etag, data })
    return { data, changed: true }
  }
  return data
}

export const api = {
  get: (path) => request('GET', path),
  /** GET that sends the last ETag: { data, changed }. Unchanged data costs a 304 with no body. */
  fresh: (path) => request('GET', path, { conditional: true }),
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
