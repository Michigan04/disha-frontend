// Sample grading schemes and class averages used for score prediction.
// Real weights come from each course page; in the full platform the prediction comes
// from the team's model (with SHAP explanations), not from this simple formula.

export const GRADE_BANDS = [
  { grade: 'S', min: 90 },
  { grade: 'A', min: 80 },
  { grade: 'B', min: 70 },
  { grade: 'C', min: 60 },
  { grade: 'D', min: 50 },
  { grade: 'E', min: 40 },
  { grade: 'U', min: 0 },
]

export const SCHEMES = {
  stats2: {
    parts: [
      { key: 'assignments', label: 'Weekly assignments', weight: 10 },
      { key: 'quiz1', label: 'Quiz 1', weight: 20 },
      { key: 'quiz2', label: 'Quiz 2', weight: 20 },
      { key: 'endterm', label: 'End-term exam', weight: 50 },
    ],
    classAvg: { assignments: 66, quiz1: 57 },
    adjust: -2,
  },
  python: {
    parts: [
      { key: 'assignments', label: 'Weekly assignments', weight: 10 },
      { key: 'quiz1', label: 'Quiz 1', weight: 15 },
      { key: 'oppe1', label: 'OPPE 1', weight: 20, oppe: 'OPPE 1' },
      { key: 'oppe2', label: 'OPPE 2', weight: 15, oppe: 'OPPE 2' },
      { key: 'endterm', label: 'End-term exam', weight: 40 },
    ],
    classAvg: { assignments: 70, quiz1: 62 },
    adjust: 0,
  },
  java: {
    parts: [
      { key: 'assignments', label: 'Weekly assignments', weight: 10 },
      { key: 'quiz1', label: 'Quiz 1', weight: 15 },
      { key: 'oppe1', label: 'OPPE 1', weight: 25, oppe: 'OPPE 1' },
      { key: 'endterm', label: 'End-term exam', weight: 50 },
    ],
    classAvg: { assignments: 72, quiz1: 65 },
    adjust: 0,
  },
  mad2: {
    parts: [
      { key: 'assignments', label: 'Weekly assignments', weight: 20 },
      { key: 'quiz1', label: 'Quiz 1', weight: 30 },
      { key: 'endterm', label: 'End-term exam', weight: 50 },
    ],
    classAvg: { assignments: 74, quiz1: 66 },
    adjust: 0,
  },
}

// Used for courses without their own sample scheme above.
const DEFAULT_SCHEME = {
  parts: [
    { key: 'assignments', label: 'Weekly assignments', weight: 10 },
    { key: 'quiz1', label: 'Quiz 1', weight: 20 },
    { key: 'quiz2', label: 'Quiz 2', weight: 20 },
    { key: 'endterm', label: 'End-term exam', weight: 50 },
  ],
  classAvg: { assignments: 68, quiz1: 60 },
  adjust: 0,
}

const DEFAULT_OPPE_SCHEME = {
  parts: [
    { key: 'assignments', label: 'Weekly assignments', weight: 10 },
    { key: 'quiz1', label: 'Quiz 1', weight: 15 },
    { key: 'oppe1', label: 'OPPE 1', weight: 25, oppe: 'OPPE 1' },
    { key: 'endterm', label: 'End-term exam', weight: 50 },
  ],
  classAvg: { assignments: 70, quiz1: 62 },
  adjust: 0,
}

export function schemeFor(course) {
  if (!course || course.type !== 'course') return null
  return SCHEMES[course.id] || (course.oppe ? DEFAULT_OPPE_SCHEME : DEFAULT_SCHEME)
}
