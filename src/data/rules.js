// Program rules used by the student views. In the full platform these come from the
// administrator's settings page (US-08); here they are fixed sample values.

export const APP_NAME = 'Disha'

export const GRADE_POINTS = { S: 10, A: 9, B: 8, C: 7, D: 6, E: 4, U: 0 }
export const FAIL_GRADE = 'U'

export const LEVEL_RULES = {
  foundation: {
    label: 'Foundation',
    limitTerms: 9,
    unit: 'courses',
    milestones: [
      { byTerm: 4, courses: 4 },
      { byTerm: 6, courses: 6 },
      { byTerm: 9, courses: 8 },
    ],
  },
  diploma: {
    label: 'Diploma',
    limitTerms: 12,
    unit: 'courses and projects',
    milestones: [
      { byTerm: 3, courses: 3, projects: 1 },
      { byTerm: 6, courses: 6, projects: 2 },
      { byTerm: 9, courses: 9, projects: 3 },
      { byTerm: 12, courses: 12, projects: 4 },
    ],
  },
}

// The two risk levels the team agreed on.
export const RISK_RULES = {
  high: {
    label: 'High risk',
    rule: 'Failed the same course twice',
    support: 'Instructor support',
  },
  low: {
    label: 'Low risk',
    rule: 'Failed a course once',
    support: 'Guidance from past students',
  },
  none: {
    label: 'On track',
    rule: 'No course failed',
    support: '',
  },
}
