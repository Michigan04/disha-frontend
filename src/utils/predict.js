import { GRADE_BANDS, schemeFor } from '../data/schemes'
import { COURSES } from '../data/courses'
import { oppeStatus } from './progress'

export const gradeFor = (score) => GRADE_BANDS.find((b) => score >= b.min).grade

const clamp = (v, lo = 0, hi = 100) => Math.min(hi, Math.max(lo, v))
const round1 = (v) => Math.round(v * 10) / 10

// Expected score in a part not yet taken, from what the student has shown so far.
function expected(a, q, adjust) {
  return clamp(q == null ? a + adjust - 4 : 0.55 * a + 0.45 * q + adjust)
}

// Status of each part: known score, missed (counts as 0), or still to come.
function partStatus(part, attempt, student, courseId) {
  if (part.key === 'assignments') return { status: 'known', value: attempt.assignmentAvg }
  if (attempt[part.key] != null) return { status: 'known', value: attempt[part.key] }
  if (part.oppe) {
    const o = student.oppe.find((x) => x.courseId === courseId && x.title === part.oppe)
    if (o && oppeStatus(o) === 'not_eligible') return { status: 'missed', value: 0 }
  }
  return { status: 'upcoming', value: null }
}

function total(parts, a, q, adjust, treatMissedAsUpcoming = false) {
  return parts.reduce((sum, p) => {
    let v
    if (p.key === 'assignments') v = a
    else if (p.key === 'quiz1' && q != null) v = q
    else if (p.status === 'missed' && !treatMissedAsUpcoming) v = 0
    else if (p.status === 'known') v = p.value
    else v = expected(a, q, adjust)
    return sum + (p.weight / 100) * v
  }, 0)
}

/**
 * Predict the final score for a course in progress.
 * `remainingAvg` (optional) is the assignment average the student expects for the rest
 * of the term, for the "what if" slider.
 */
export function predict(student, courseId, attempt, remainingAvg = null) {
  const scheme = schemeFor(COURSES[courseId])
  if (!scheme || !attempt?.inProgress || attempt.assignmentAvg == null) return null

  const parts = scheme.parts.map((p) => ({ ...p, ...partStatus(p, attempt, student, courseId) }))
  const a0 = attempt.assignmentAvg
  const a = remainingAvg == null
    ? a0
    : (a0 * attempt.week + remainingAvg * (attempt.weeks - attempt.week)) / attempt.weeks
  const q = attempt.quiz1 ?? null
  const adj = scheme.adjust

  const score = clamp(total(parts, a, q, adj))
  const upcomingWeight = parts.filter((p) => p.status === 'upcoming').reduce((s, p) => s + p.weight, 0)
  const spread = Math.max(3, (upcomingWeight / 100) * 12)

  // Why the prediction differs from a typical student's (a simple, additive breakdown).
  const avg = scheme.classAvg
  const baseline = clamp(total(parts, avg.assignments, q == null ? null : avg.quiz1, adj, true))
  const stepA = total(parts, a, q == null ? null : avg.quiz1, adj, true)
  const stepQ = total(parts, a, q, adj, true)
  const factors = [
    { label: 'Weekly assignment average', detail: `${round1(a)} vs class ${avg.assignments}`, delta: round1(stepA - total(parts, avg.assignments, q == null ? null : avg.quiz1, adj, true)) },
  ]
  if (q != null) factors.push({ label: 'Quiz 1', detail: `${q} vs class ${avg.quiz1}`, delta: round1(stepQ - stepA) })
  const missed = parts.filter((p) => p.status === 'missed')
  if (missed.length) {
    factors.push({ label: `${missed.map((p) => p.label).join(', ')} not taken`, detail: 'not eligible', delta: round1(total(parts, a, q, adj) - stepQ) })
  }

  return {
    score: round1(score),
    low: round1(clamp(score - spread)),
    high: round1(clamp(score + spread)),
    // grade from the rounded score, so the number and the grade shown always agree
    grade: gradeFor(Math.round(score)),
    parts: parts.map((p) => ({
      ...p,
      shown: p.key === 'assignments' ? round1(a) : p.status === 'upcoming' ? round1(expected(a, q, adj)) : p.value,
    })),
    baseline: round1(baseline),
    factors,
    upcomingWeight,
  }
}
