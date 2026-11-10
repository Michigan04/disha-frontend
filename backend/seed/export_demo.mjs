// One-off: dumps the frontend's former sample data to demo_data.json for the DB seed.
// Run from the repo root on a commit that still has src/data/cohort.js:  node backend/seed/export_demo.mjs
import { createServer } from 'vite'
import { writeFileSync } from 'node:fs'

const server = await createServer({ server: { middlewareMode: true }, appType: 'custom', logLevel: 'error' })
const load = (p) => server.ssrLoadModule(p)
const { createPinia, setActivePinia } = await import('pinia')
setActivePinia(createPinia())
const { useStaffStore } = await load('/src/stores/staff.js')
const courses = await load('/src/data/courses.js')
const rules = await load('/src/data/rules.js')
const staff = await load('/src/data/staff.js')
const accounts = await load('/src/data/accounts.js')
const guides = await load('/src/data/guides.js')
const plans = await load('/src/data/plans.js')
const insights = await load('/src/data/insights.js')
const schemes = await load('/src/data/schemes.js')
const actions = await load('/src/data/actions.js')
const csv = await load('/src/utils/csv.js')

const s = useStaffStore()
const out = {
  generatedAt: new Date(),
  courses: courses.COURSES,
  levelCourses: courses.LEVEL_COURSES,
  courseCodes: csv.COURSE_CODES,
  gradePoints: rules.GRADE_POINTS,
  levelRules: rules.LEVEL_RULES,
  riskRules: rules.RISK_RULES,
  staff: staff.STAFF,
  permissions: staff.PERMISSIONS,
  staffEvents: Object.fromEntries(Object.keys(staff.STAFF).map((id) => [id, staff.staffEvents(id)])),
  accounts: accounts.ACCOUNTS,
  guides: guides.COURSE_GUIDES,
  plans: plans.STUDY_PLANS,
  insights: insights.PAST_STUDENT_INSIGHTS,
  gradeBands: schemes.GRADE_BANDS,
  schemes: schemes.SCHEMES,
  defaultScheme: schemes.schemeFor({ id: '_', type: 'course' }),
  defaultOppeScheme: schemes.schemeFor({ id: '_', type: 'course', oppe: true }),
  suggestedActions: actions.SUGGESTED_ACTIONS,
  students: s.students,
  meta: s.meta,
  interventions: s.interventions,
  rules: s.rules,
  ruleHistory: s.ruleHistory,
  imports: s.imports,
  jobs: s.jobs,
  users: s.users,
  audit: s.audit,
}
writeFileSync(new URL('./demo_data.json', import.meta.url), JSON.stringify(out, null, 1))
await server.close()
console.log('students', out.students.length, 'interventions', out.interventions.length, 'audit', out.audit.length)
