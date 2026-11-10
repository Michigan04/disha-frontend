// Week-by-week study plans for a course the student has failed before.
// Loaded from the backend (see reference.js).
//   STUDY_PLANS[courseId] { goal, hoursPerWeek, weeks: [{ w, focus, hours, checkpoint?, tasks }] }

import { reactive } from 'vue'

export const STUDY_PLANS = reactive({})
