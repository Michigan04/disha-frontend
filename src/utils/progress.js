import { COURSES, LEVEL_COURSES } from '../data/courses'
import { GRADE_POINTS, FAIL_GRADE, LEVEL_RULES, RISK_RULES } from '../data/rules'
import { termAfter } from './dates'

export const isPass = (a) => !a.inProgress && a.grade && a.grade !== FAIL_GRADE
export const isFail = (a) => !a.inProgress && a.grade === FAIL_GRADE

export function attemptsFor(student, courseId) {
  return student.attempts.filter((a) => a.courseId === courseId)
}

export function currentTermLabel(student) {
  return student.terms[student.terms.length - 1]
}

export function currentTermNumber(student) {
  return student.terms.length
}

// passed | in_progress | not_cleared | not_started
export function courseStatus(student, courseId) {
  const list = attemptsFor(student, courseId)
  const passed = list.find(isPass)
  const fails = list.filter(isFail).length
  const current = list.find((a) => a.inProgress)
  if (passed) return { state: 'passed', grade: passed.grade, term: passed.term, fails, attempts: list.length }
  if (current) return { state: 'in_progress', fails, attemptNo: fails + 1, current, attempts: list.length }
  if (fails) return { state: 'not_cleared', fails, attempts: list.length }
  return { state: 'not_started', fails: 0, attempts: 0 }
}

export function courseList(student) {
  return LEVEL_COURSES[student.level].map((id) => ({ course: COURSES[id], status: courseStatus(student, id) }))
}

export function completed(student) {
  const done = courseList(student).filter((c) => c.status.state === 'passed')
  return {
    courses: done.filter((c) => c.course.type === 'course').length,
    projects: done.filter((c) => c.course.type === 'project').length,
    // the final milestone defines everything needed to finish the level
    total: (() => {
      const last = LEVEL_RULES[student.level].milestones.at(-1)
      return last.courses + (last.projects || 0)
    })(),
  }
}

function gpa(attempts) {
  const passed = attempts.filter(isPass)
  const credits = passed.reduce((s, a) => s + COURSES[a.courseId].credits, 0)
  if (!credits) return null
  const points = passed.reduce((s, a) => s + COURSES[a.courseId].credits * GRADE_POINTS[a.grade], 0)
  return Math.round((points / credits) * 100) / 100
}

export function cgpa(student) {
  return gpa(student.attempts)
}

export function termSummaries(student) {
  return student.terms.map((term, i) => {
    const inTerm = student.attempts.filter((a) => a.term === term)
    const upTo = student.attempts.filter((a) => student.terms.indexOf(a.term) <= i)
    const done = inTerm.every((a) => !a.inProgress)
    return {
      term,
      number: i + 1,
      attempts: inTerm,
      termGpa: done ? gpa(inTerm) : null,
      cgpaAfter: done ? gpa(upTo) : null,
      fails: inTerm.filter(isFail).length,
      inProgress: !done,
    }
  })
}

export function milestones(student) {
  const rule = LEVEL_RULES[student.level]
  const now = currentTermNumber(student)
  const done = completed(student)
  const list = rule.milestones.map((m) => {
    const coursesOk = done.courses >= m.courses
    const projectsOk = m.projects == null || done.projects >= m.projects
    const met = coursesOk && projectsOk
    let state = 'upcoming'
    if (met) state = 'met'
    else if (m.byTerm < now) state = 'missed'
    const needCourses = Math.max(0, m.courses - done.courses)
    const needProjects = m.projects == null ? 0 : Math.max(0, m.projects - done.projects)
    return {
      ...m,
      termLabel: termAfter(student.terms[0], m.byTerm - 1),
      met,
      state,
      needCourses,
      needProjects,
      text: m.projects == null ? `${m.courses} courses` : `${m.courses} courses + ${m.projects} ${m.projects === 1 ? 'project' : 'projects'}`,
    }
  })
  // The first milestone still to meet is the one to work towards now.
  const next = list.find((m) => m.state === 'upcoming')
  if (next) next.state = 'due'
  return list
}

export function nextMilestone(student) {
  return milestones(student).find((m) => !m.met) || null
}

// Two risk levels, as agreed by the team:
//   High: the same course failed twice and still not cleared -> instructor support
//   Low:  a course failed once and still not cleared         -> guidance from past students
export function risk(student) {
  const open = courseList(student).filter((c) => c.status.state !== 'passed' && c.status.fails > 0)
  const high = open.filter((c) => c.status.fails >= 2)
  const low = open.filter((c) => c.status.fails === 1)
  if (high.length) {
    return { level: 'high', ...RISK_RULES.high, courses: high, focus: high[0] }
  }
  if (low.length) {
    return { level: 'low', ...RISK_RULES.low, courses: low, focus: low[0] }
  }
  return { level: 'none', ...RISK_RULES.none, courses: [], focus: null }
}

export function oppeStatus(item) {
  const finalMissing = item.criteria.some((c) => c.final && !meets(c))
  if (finalMissing) return 'not_eligible'
  if (item.criteria.some((c) => !c.final)) return 'pending'
  return 'eligible'
}

export function meets(c) {
  if (typeof c.required === 'boolean') return c.actual === c.required
  return c.actual != null && c.actual >= c.required
}

export function currentCourses(student) {
  const term = currentTermLabel(student)
  return student.attempts
    .filter((a) => a.term === term && a.inProgress)
    .map((a) => ({ attempt: a, course: COURSES[a.courseId], status: courseStatus(student, a.courseId) }))
}
