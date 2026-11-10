// Staff directory and permissions, loaded from the backend (see reference.js).
//   STAFF[id]        { id, name, email, role, title, capacity?, courseId? }
//   PERMISSIONS      [{ key, label, roles }]: what each role may do. The backend enforces
//                    these; the pages use them to hide what a role cannot open.

import { reactive } from 'vue'

export const STAFF = reactive({})
export const SUPPORT_STAFF = reactive([])
export const INSTRUCTOR_FOR = reactive({})
export const PERMISSIONS = reactive([])
export const STAFF_EVENTS = reactive({})

export const can = (role, key) => Boolean(PERMISSIONS.find((p) => p.key === key)?.roles.includes(role))

// Meetings for the signed-in staff member.
export const staffEvents = (staffId) => STAFF_EVENTS[staffId] || []
