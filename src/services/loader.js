// Loads everything a signed-in user's pages need from the API, and keeps it live.
//
// On the first navigation after sign-in (or a page reload):
//   1. GET /auth/me checks the session against the database, so a deactivated
//      account or a changed role takes effect at once.
//   2. In parallel: reference data (courses, rules, staff directory, content), and
//      the student's own record or the staff dashboard, plus today's meetings.
// Afterwards it refreshes every 30 seconds while the tab is visible, and when the
// tab comes back into view. Each refresh sends the last ETag, so when nothing has
// changed the server answers 304 Not Modified and the page is not re-rendered.

import { reactive } from 'vue'
import { api, updateSessionUser } from './api'
import { applyReference } from '../data/reference'
import { STAFF_EVENTS } from '../data/staff'
import { useAuthStore } from '../stores/auth'
import { useStaffStore } from '../stores/staff'
import { useStudentStore } from '../stores/student'

const REFRESH_MS = 30_000

export const boot = reactive({ ready: false, loading: false, error: '' })
let verified = false
let timer = null
let inflight = null

async function pull(path, apply, onlyIfChanged) {
  const { data, changed } = await api.fresh(path)
  if (changed || !onlyIfChanged) apply(data)
}

function tasks(onlyIfChanged) {
  const auth = useAuthStore()
  const list = [pull('/reference', applyReference, onlyIfChanged)]
  if (auth.role === 'student') {
    const store = useStudentStore()
    list.push(pull('/me/student', (d) => store.apply(d), onlyIfChanged))
  } else {
    const staff = useStaffStore()
    list.push(pull('/staff/bootstrap', (d) => staff.apply(d), onlyIfChanged))
    list.push(pull('/me/meetings', (d) => { STAFF_EVENTS[auth.user.staffId] = d }, onlyIfChanged))
  }
  return list
}

async function verifySession() {
  const auth = useAuthStore()
  const me = await api.get('/auth/me')
  if (JSON.stringify(me) !== JSON.stringify(auth.user)) {
    auth.user = me
    updateSessionUser(me)
  }
  verified = true
}

/** Load the signed-in user's data (once per page load). Safe to call repeatedly. */
export function ensureData() {
  const auth = useAuthStore()
  if (!auth.user || boot.ready) return Promise.resolve()
  if (inflight) return inflight
  boot.loading = true
  boot.error = ''
  inflight = (async () => {
    try {
      if (!verified) await verifySession()
      if (!useAuthStore().user) return
      await Promise.all(tasks(false))
      boot.ready = true
      startLive()
    } catch (err) {
      boot.error = err.message
    } finally {
      boot.loading = false
      inflight = null
    }
  })()
  return inflight
}

/** Re-read whatever changed on the server (no re-render when nothing did). */
export async function refresh() {
  if (!boot.ready || document.visibilityState === 'hidden') return
  try {
    await Promise.all(tasks(true))
  } catch {
    /* a failed background refresh keeps the last good data; the next one retries */
  }
}

function onVisible() {
  if (document.visibilityState === 'visible') refresh()
}

function startLive() {
  stopLive()
  timer = setInterval(refresh, REFRESH_MS)
  document.addEventListener('visibilitychange', onVisible)
}

function stopLive() {
  if (timer) clearInterval(timer)
  timer = null
  document.removeEventListener('visibilitychange', onVisible)
}

/** Forget everything loaded for the previous user (sign-out or expired session). */
export function resetData() {
  stopLive()
  verified = false
  boot.ready = false
  boot.error = ''
  useStudentStore().clear()
  useStaffStore().clear()
  for (const k of Object.keys(STAFF_EVENTS)) delete STAFF_EVENTS[k]
}
