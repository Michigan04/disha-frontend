// Roles and where each one lands after signing in. Accounts live in the backend;
// the sign-in page asks it for the demo accounts to offer (GET /api/auth/demo-accounts).

export const ROLES = {
  student: { label: 'Student', home: '/' },
  support: { label: 'Support staff', home: '/staff' },
  instructor: { label: 'Course instructor', home: '/staff/course' },
  admin: { label: 'Administrator', home: '/staff' },
}
