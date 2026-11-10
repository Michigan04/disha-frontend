// Program rules, loaded from the backend (see reference.js). The administrator edits
// them on the Rules and access page (US-08).
//   GRADE_POINTS        { S: 10, A: 9, ... }
//   LEVEL_RULES[level]  { label, limitTerms, unit, milestones: [{ byTerm, courses, projects? }] }
//   RISK_RULES[level]   { label, rule, support } for high, low and none

import { reactive } from 'vue'

export const APP_NAME = 'Disha'
export const FAIL_GRADE = 'U'

export const GRADE_POINTS = reactive({})
export const LEVEL_RULES = reactive({})
export const RISK_RULES = reactive({})
