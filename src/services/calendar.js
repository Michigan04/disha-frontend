// Google Calendar integration.
//
// With VITE_GOOGLE_CLIENT_ID set, "Connect Google Calendar" signs the student in with
// Google Identity Services and reads the next 30 days of events (read-only scope).
// Without it, the app shows each demo student's sample meetings, so it runs with no setup.

import { reactive } from 'vue'

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID
const SCOPE = 'https://www.googleapis.com/auth/calendar.readonly'
const EVENTS_URL = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'

export const calendarConfigured = Boolean(CLIENT_ID)

const state = reactive({
  connected: false,
  loading: false,
  error: '',
  source: 'sample', // 'sample' | 'google'
  events: [],
  syncedAt: null,
})

let token = null

function loadGoogleScript() {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.oauth2) return resolve()
    const s = document.createElement('script')
    s.src = 'https://accounts.google.com/gsi/client'
    s.async = true
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('Google sign-in could not be loaded. Check your connection and try again.'))
    document.head.appendChild(s)
  })
}

async function requestToken() {
  await loadGoogleScript()
  return new Promise((resolve, reject) => {
    const client = window.google.accounts.oauth2.initTokenClient({
      client_id: CLIENT_ID,
      scope: SCOPE,
      callback: (res) => (res.error ? reject(new Error('Google Calendar access was not granted.')) : resolve(res.access_token)),
    })
    client.requestAccessToken()
  })
}

function toEvent(e) {
  const video = e.conferenceData?.entryPoints?.find((p) => p.entryPointType === 'video')
  return {
    id: e.id,
    title: e.summary || 'Untitled event',
    start: new Date(e.start?.dateTime || e.start?.date),
    end: new Date(e.end?.dateTime || e.end?.date),
    link: e.hangoutLink || video?.uri || '',
    organizer: e.organizer?.displayName || e.organizer?.email || '',
    location: e.location || '',
  }
}

async function fetchGoogleEvents() {
  const params = new URLSearchParams({
    timeMin: new Date().toISOString(),
    timeMax: new Date(Date.now() + 30 * 864e5).toISOString(),
    singleEvents: 'true',
    orderBy: 'startTime',
    maxResults: '25',
  })
  const res = await fetch(`${EVENTS_URL}?${params}`, { headers: { Authorization: `Bearer ${token}` } })
  if (res.status === 401) {
    token = null
    throw new Error('Your Google session has expired. Connect Google Calendar again.')
  }
  if (!res.ok) throw new Error('Google Calendar did not respond. Try again in a minute.')
  const data = await res.json()
  return (data.items || []).map(toEvent)
}

function sampleEvents(student) {
  return [...(student?.meetings || [])].sort((a, b) => a.start - b.start)
}

export function useCalendar() {
  async function load(student) {
    state.error = ''
    if (state.source === 'google' && token) {
      state.loading = true
      try {
        state.events = await fetchGoogleEvents()
        state.syncedAt = new Date()
      } catch (err) {
        state.error = err.message
      } finally {
        state.loading = false
      }
      return
    }
    state.events = sampleEvents(student)
  }

  async function connect(student) {
    state.error = ''
    state.loading = true
    try {
      if (calendarConfigured) {
        token = await requestToken()
        state.source = 'google'
        state.events = await fetchGoogleEvents()
      } else {
        // Demo: behave like a successful connection using the sample meetings.
        await new Promise((r) => setTimeout(r, 500))
        state.source = 'sample'
        state.events = sampleEvents(student)
      }
      state.connected = true
      state.syncedAt = new Date()
    } catch (err) {
      state.error = err.message
    } finally {
      state.loading = false
    }
  }

  function disconnect(student) {
    if (token && window.google?.accounts?.oauth2) window.google.accounts.oauth2.revoke(token)
    token = null
    state.connected = false
    state.source = 'sample'
    state.events = sampleEvents(student)
  }

  return { state, load, connect, disconnect }
}
