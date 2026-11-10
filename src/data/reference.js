// Reference data comes from the backend (GET /api/reference): the course catalogue,
// program rules, staff directory and course content. The modules in this folder export
// empty reactive containers; loadReference() fills them once the user has signed in,
// so pages keep reading COURSES[id], STAFF[id], LEVEL_RULES[level] and so on.
// services/loader.js calls it after sign-in and keeps it fresh.

import { api } from '../services/api'
import { COURSES, LEVEL_COURSES, TERM_OUTCOMES } from './courses'
import { GRADE_POINTS, LEVEL_RULES, RISK_RULES } from './rules'
import { INSTRUCTOR_FOR, PERMISSIONS, STAFF, SUPPORT_STAFF } from './staff'
import { SUGGESTED_ACTIONS } from './actions'
import { COURSE_GUIDES } from './guides'
import { STUDY_PLANS } from './plans'
import { PAST_STUDENT_INSIGHTS } from './insights'
import { DEFAULT_SCHEMES, GRADE_BANDS, SCHEMES } from './schemes'

function fill(target, source) {
  if (Array.isArray(target)) {
    target.splice(0, target.length, ...(source || []))
    return
  }
  for (const key of Object.keys(target)) delete target[key]
  Object.assign(target, source || {})
}

export function applyReference(ref) {
  fill(COURSES, ref.courses)
  fill(LEVEL_COURSES, ref.levelCourses)
  fill(TERM_OUTCOMES, ref.outcomes)
  fill(GRADE_POINTS, ref.gradePoints)
  fill(LEVEL_RULES, ref.levelRules)
  fill(RISK_RULES, ref.riskRules)
  fill(PERMISSIONS, ref.permissions)
  fill(SUGGESTED_ACTIONS, ref.suggestedActions)
  fill(COURSE_GUIDES, ref.guides)
  fill(STUDY_PLANS, ref.plans)
  fill(PAST_STUDENT_INSIGHTS, ref.insights)
  fill(GRADE_BANDS, ref.gradeBands)
  fill(SCHEMES, ref.schemes)
  fill(DEFAULT_SCHEMES, { course: ref.defaultScheme, oppe: ref.defaultOppeScheme })
  fill(STAFF, ref.staff)
  const staff = Object.values(ref.staff || {})
  fill(SUPPORT_STAFF, staff.filter((s) => s.role === 'support'))
  fill(INSTRUCTOR_FOR, Object.fromEntries(staff.filter((s) => s.courseId).map((s) => [s.courseId, s.id])))
}

export async function loadReference() {
  applyReference((await api.fresh('/reference')).data)
}
