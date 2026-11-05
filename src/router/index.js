import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import StudentLayout from '../layouts/StudentLayout.vue'
import DashboardView from '../views/DashboardView.vue'

const STAFF = ['support', 'admin']

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { public: true, title: 'Sign in' } },
  {
    path: '/',
    component: StudentLayout,
    meta: { roles: ['student'] },
    children: [
      { path: '', name: 'home', component: DashboardView, meta: { title: 'Home' } },
      { path: 'progress', name: 'progress', component: () => import('../views/ProgressView.vue'), meta: { title: 'CGPA and terms' } },
      { path: 'courses', name: 'courses', component: () => import('../views/CoursesView.vue'), meta: { title: 'Courses' } },
      { path: 'courses/:id', name: 'course', component: () => import('../views/CourseDetailView.vue'), meta: { title: 'Course' } },
      { path: 'oppe', name: 'oppe', component: () => import('../views/OppeView.vue'), meta: { title: 'OPPE eligibility' } },
      { path: 'meetings', name: 'meetings', component: () => import('../views/MeetingsView.vue'), meta: { title: 'Meetings' } },
      { path: 'ask', name: 'ask', component: () => import('../views/AssistantView.vue'), meta: { title: 'Ask Disha' } },
    ],
  },
  {
    path: '/staff',
    component: () => import('../layouts/StaffLayout.vue'),
    meta: { roles: ['support', 'admin', 'instructor'] },
    children: [
      { path: '', name: 'staff-home', component: () => import('../views/staff/OverviewView.vue'), meta: { title: 'Overview', roles: STAFF } },
      { path: 'students', name: 'staff-students', component: () => import('../views/staff/StudentsView.vue'), meta: { title: 'At-risk students', roles: STAFF } },
      { path: 'students/:id', name: 'staff-student', component: () => import('../views/staff/StudentView.vue'), meta: { title: 'Student', roles: STAFF } },
      { path: 'interventions', name: 'staff-interventions', component: () => import('../views/staff/InterventionsView.vue'), meta: { title: 'Interventions', roles: STAFF } },
      { path: 'course', name: 'staff-course', component: () => import('../views/staff/CourseView.vue'), meta: { title: 'My course', roles: ['instructor'] } },
      { path: 'reports', name: 'staff-reports', component: () => import('../views/staff/ReportsView.vue'), meta: { title: 'Reports', roles: ['admin'] } },
      { path: 'data', name: 'staff-data', component: () => import('../views/staff/DataView.vue'), meta: { title: 'Data and system', roles: ['admin'] } },
      { path: 'rules', name: 'staff-rules', component: () => import('../views/staff/RulesView.vue'), meta: { title: 'Rules and access', roles: ['admin'] } },
      { path: 'audit', name: 'staff-audit', component: () => import('../views/staff/AuditView.vue'), meta: { title: 'Audit log', roles: ['admin'] } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  // Hash history works on any static host and when opening the built files locally.
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// Each page says which roles may open it; the most specific rule wins.
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    if (!auth.user) return true
    return typeof to.query.redirect === 'string' ? to.query.redirect : auth.home
  }
  if (!auth.user) return { path: '/login', query: to.fullPath === '/' ? {} : { redirect: to.fullPath } }
  const roles = [...to.matched].reverse().find((m) => m.meta.roles)?.meta.roles
  if (roles && !roles.includes(auth.role)) return auth.home
  return true
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} | Disha` : 'Disha'
})

export default router
