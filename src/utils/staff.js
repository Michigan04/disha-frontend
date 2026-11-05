// What staff see about a student, worked out with the same functions the student pages use.

import { COURSES } from '../data/courses'
import { LEVEL_RULES } from '../data/rules'
import {
  cgpa, completed, courseList, currentCourses, currentTermLabel, currentTermNumber, milestones, oppeStatus,
} from './progress'
import { predict } from './predict'
import { daysUntil } from './dates'

// Risk with the administrator's current thresholds (the student pages use the defaults).
export function riskWith(student, rules) {
  const open = courseList(student).filter((c) => c.status.state !== 'passed' && c.status.fails > 0)
  const high = open.filter((c) => c.status.fails >= rules.highFails)
  const low = open.filter((c) => c.status.fails >= rules.lowFails && c.status.fails < rules.highFails)
  if (high.length) return { level: 'high', courses: high, focus: high[0] }
  if (low.length) return { level: 'low', courses: low, focus: low[0] }
  return { level: 'none', courses: [], focus: null }
}

export const RISK_VIEW = {
  high: { label: 'High', cls: 'high' },
  low: { label: 'Low', cls: 'low' },
  none: { label: 'On track', cls: 'ok' },
}

function withThreshold(item, min) {
  return { ...item, criteria: item.criteria.map((c) => (typeof c.required === 'number' ? { ...c, required: min } : c)) }
}

/** Everything the staff list and profile need about one student. */
export function summarize(student, meta, rules) {
  const rk = riskWith(student, rules)
  const current = currentCourses(student).map((c) => ({ ...c, prediction: predict(student, c.course.id, c.attempt) }))
  const oppe = student.oppe.map((o) => ({ ...o, course: COURSES[o.courseId], status: oppeStatus(withThreshold(o, rules.oppeMin)) }))
  const ms = milestones(student)
  const preds = current.filter((c) => c.prediction)
  const worst = preds.length ? preds.reduce((a, b) => (b.prediction.score < a.prediction.score ? b : a)) : null

  const reasons = []
  for (const c of rk.courses) {
    reasons.push({
      key: c.status.fails >= rules.highFails ? 'failed_twice' : 'failed_once',
      courseId: c.course.id,
      text: `Failed ${c.course.name} ${c.status.fails === 1 ? 'once' : `${c.status.fails} times`}`,
    })
  }
  for (const o of oppe.filter((x) => x.status === 'not_eligible')) {
    reasons.push({ key: 'oppe_not_eligible', courseId: o.courseId, text: `Not eligible for ${o.course.name} ${o.title}` })
  }
  for (const c of preds.filter((x) => Math.round(x.prediction.score) < 40)) {
    reasons.push({ key: 'low_prediction', courseId: c.course.id, text: `Predicted ${Math.round(c.prediction.score)} in ${c.course.name}, below the pass mark` })
  }
  const inactiveDays = meta.plan ? -daysUntil(meta.plan.lastActive) : 0
  if (rk.level === 'low' && meta.plan && inactiveDays >= 7) {
    reasons.push({ key: 'plan_inactive', courseId: rk.focus.course.id, text: `Study plan not opened for ${inactiveDays} days` })
  }
  const missed = ms.find((m) => m.state === 'missed')
  if (missed) reasons.push({ key: 'behind_milestone', text: `Missed the term ${missed.byTerm} milestone (${missed.text})` })
  if (meta.dataIssue) reasons.push({ key: 'data_issue', text: meta.dataIssue })

  return {
    id: student.id,
    student,
    name: student.name,
    rollNo: student.rollNo,
    level: student.level,
    levelLabel: LEVEL_RULES[student.level].label,
    term: currentTermNumber(student),
    termLabel: currentTermLabel(student),
    cohort: student.admittedFrom,
    cgpa: cgpa(student),
    done: completed(student),
    milestones: ms,
    risk: rk,
    isNew: rk.level === 'high' && meta.prevLevel !== 'high',
    reasons,
    main: reasons[0] || null,
    current,
    worst,
    oppe,
    owner: meta.owner,
    meta,
    inactiveDays,
    predictedFail: preds.some((c) => Math.round(c.prediction.score) < 40),
  }
}

export const initials = (name) => name.replace(/^(Prof\.|Dr\.)\s*/, '').split(/\s+/).map((p) => p[0]).slice(0, 2).join('')
