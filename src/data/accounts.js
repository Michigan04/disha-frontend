// Demo sign-in accounts. Frontend only: in the full platform, sign-in and roles are
// checked by the backend (institute single sign-on), never in the browser.

export const DEMO_PASSWORD = 'disha123'

export const ROLES = {
  student: { label: 'Student', home: '/' },
  support: { label: 'Support staff', home: '/staff' },
  instructor: { label: 'Course instructor', home: '/staff/course' },
  admin: { label: 'Administrator', home: '/staff' },
}

export const ACCOUNTS = [
  { email: 'ananya@disha.demo', name: 'Ananya Rao', role: 'student', studentId: 'ananya', note: 'Low risk: failed Statistics II once' },
  { email: 'rahul@disha.demo', name: 'Rahul Verma', role: 'student', studentId: 'rahul', note: 'High risk: failed Python twice' },
  { email: 'karthik@disha.demo', name: 'Karthik Iyer', role: 'student', studentId: 'karthik', note: 'On track, Diploma' },
  { email: 'neha@disha.demo', name: 'Neha Kulkarni', role: 'support', staffId: 'neha', note: 'Academic advisor with her own caseload' },
  { email: 'kavya@disha.demo', name: 'Prof. Kavya Menon', role: 'instructor', staffId: 'kavya', courseId: 'python', note: 'Instructor, Programming in Python' },
  { email: 'admin@disha.demo', name: 'Suresh Pillai', role: 'admin', staffId: 'suresh', note: 'Program administrator: sees everything' },
]

export const findAccount = (email) => ACCOUNTS.find((a) => a.email === String(email || '').trim().toLowerCase()) || null
