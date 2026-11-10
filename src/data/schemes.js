// Grading schemes and class averages used for score prediction.
// Loaded from the backend (see reference.js).
//   GRADE_BANDS        [{ grade, min }], highest first
//   SCHEMES[courseId]  { parts: [{ key, label, weight, oppe? }], classAvg, adjust }
//   DEFAULT_SCHEMES    { course, oppe }: used for courses without their own scheme

import { reactive } from 'vue'

export const GRADE_BANDS = reactive([])
export const SCHEMES = reactive({})
export const DEFAULT_SCHEMES = reactive({})

export function schemeFor(course) {
  if (!course || course.type !== 'course') return null
  return SCHEMES[course.id] || (course.oppe ? DEFAULT_SCHEMES.oppe : DEFAULT_SCHEMES.course) || null
}
