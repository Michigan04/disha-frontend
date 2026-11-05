const DAY = 24 * 60 * 60 * 1000

// A date `days` from now at the given hour and minute (local time).
export function at(days, hour = 10, minute = 0) {
  const d = new Date()
  d.setHours(hour, minute, 0, 0)
  return new Date(d.getTime() + days * DAY)
}

export function startOfDay(d) {
  const x = new Date(d)
  x.setHours(0, 0, 0, 0)
  return x
}

export function daysUntil(d) {
  return Math.round((startOfDay(d) - startOfDay(new Date())) / DAY)
}

export function relativeDay(d) {
  const n = daysUntil(d)
  if (n === 0) return 'Today'
  if (n === 1) return 'Tomorrow'
  if (n === -1) return 'Yesterday'
  if (n > 1 && n < 7) return `In ${n} days`
  if (n < 0) return `${-n} days ago`
  return formatDate(d)
}

export function formatDate(d, opts = {}) {
  return new Intl.DateTimeFormat('en-IN', { weekday: 'short', day: 'numeric', month: 'short', ...opts }).format(d)
}

export function formatTime(d) {
  return new Intl.DateTimeFormat('en-IN', { hour: 'numeric', minute: '2-digit', hour12: true })
    .format(d)
    .replace(' ', ' ')
    .toLowerCase()
}

export function weekday(d) {
  return new Intl.DateTimeFormat('en-IN', { weekday: 'short' }).format(d)
}

// Terms run Jan, May and Sep. Given 'Sep 2026', return the term `steps` later.
const TERM_MONTHS = ['Jan', 'May', 'Sep']
export function termAfter(label, steps = 1) {
  let [m, y] = label.split(' ')
  let i = TERM_MONTHS.indexOf(m)
  let year = Number(y)
  for (let k = 0; k < steps; k += 1) {
    i += 1
    if (i === 3) {
      i = 0
      year += 1
    }
  }
  return `${TERM_MONTHS[i]} ${year}`
}

export function greeting(now = new Date()) {
  const h = now.getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

// A time `minutes` from now, rounded up to the next 5 minutes (for sample "today" events).
export function inMinutes(minutes) {
  const d = new Date(Date.now() + minutes * 60 * 1000)
  d.setSeconds(0, 0)
  d.setMinutes(Math.ceil(d.getMinutes() / 5) * 5)
  return d
}

export function minutesUntil(d, now = new Date()) {
  return Math.round((d - now) / 60000)
}

export function isToday(d, now = new Date()) {
  return startOfDay(d).getTime() === startOfDay(now).getTime()
}
