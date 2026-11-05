// Staff members, what each role may do, and today's sample meetings for staff.

import { at, inMinutes } from '../utils/dates'

const span = (start, minutes) => new Date(start.getTime() + minutes * 60000)

export const STAFF = {
  neha: { id: 'neha', name: 'Neha Kulkarni', role: 'support', title: 'Academic advisor', capacity: 12 },
  arjun: { id: 'arjun', name: 'Arjun Das', role: 'support', title: 'Support TA', capacity: 8 },
  fatima: { id: 'fatima', name: 'Fatima Sheikh', role: 'support', title: 'Academic advisor', capacity: 12 },
  kavya: { id: 'kavya', name: 'Prof. Kavya Menon', role: 'instructor', title: 'Course instructor, Programming in Python', courseId: 'python' },
  rohan: { id: 'rohan', name: 'Dr. Rohan Gupta', role: 'instructor', title: 'Course instructor, Statistics for Data Science II', courseId: 'stats2' },
  suresh: { id: 'suresh', name: 'Suresh Pillai', role: 'admin', title: 'Program administrator' },
}

export const SUPPORT_STAFF = Object.values(STAFF).filter((s) => s.role === 'support')
export const INSTRUCTOR_FOR = Object.fromEntries(Object.values(STAFF).filter((s) => s.courseId).map((s) => [s.courseId, s.id]))

// What each role can do (also drawn as the permission table on the Rules and access page).
export const PERMISSIONS = [
  { key: 'own_record', label: 'See own progress, risk and study plan', roles: ['student'] },
  { key: 'risk_list', label: 'See the at-risk student list', roles: ['support', 'admin'] },
  { key: 'profile', label: 'Open student profiles', roles: ['support', 'admin'] },
  { key: 'log', label: 'Log interventions and follow-ups', roles: ['support', 'admin'] },
  { key: 'referrals', label: 'See students referred to own course', roles: ['instructor'] },
  { key: 'record_support', label: 'Record support offered on a referral', roles: ['instructor'] },
  { key: 'assign', label: 'Assign students to staff', roles: ['admin'] },
  { key: 'reports', label: 'See outcome reports', roles: ['admin'] },
  { key: 'rules', label: 'Edit milestone and risk rules', roles: ['admin'] },
  { key: 'upload', label: 'Upload academic data', roles: ['admin'] },
  { key: 'audit', label: 'See the full audit log', roles: ['admin'] },
  { key: 'users', label: 'Manage users and roles', roles: ['admin'] },
]

export const can = (role, key) => Boolean(PERMISSIONS.find((p) => p.key === key)?.roles.includes(role))

// Today's meetings for each staff member (sample calendar).
export function staffEvents(staffId) {
  const list = {
    neha: [
      { id: 'n1', title: 'Follow-up call: Rohit Bansal', start: inMinutes(55), end: span(inMinutes(55), 20), link: 'https://meet.google.com/', organizer: 'Neha Kulkarni' },
      { id: 'n2', title: 'Case review with Prof. Kavya Menon', start: inMinutes(150), end: span(inMinutes(150), 30), link: 'https://meet.google.com/', organizer: 'Support team' },
      { id: 'n3', title: 'Weekly risk review', start: at(1, 11), end: at(1, 12), link: 'https://meet.google.com/', organizer: 'Suresh Pillai' },
    ],
    suresh: [
      { id: 's1', title: 'Weekly risk review with the support team', start: inMinutes(75), end: span(inMinutes(75), 45), link: 'https://meet.google.com/', organizer: 'Suresh Pillai' },
      { id: 's2', title: 'Week 8 assignment scores: import window opens', start: inMinutes(240), end: span(inMinutes(240), 30), link: '', organizer: 'Program office', location: 'Data and system' },
      { id: 's3', title: 'Rules review: Diploma project milestones', start: at(2, 15), end: at(2, 16), link: 'https://meet.google.com/', organizer: 'Program office' },
    ],
    kavya: [
      { id: 'k1', title: 'Mock OPPE briefing for referred students', start: inMinutes(90), end: span(inMinutes(90), 45), link: 'https://meet.google.com/', organizer: 'Prof. Kavya Menon' },
      { id: 'k2', title: 'Check-in with Rahul Verma', start: at(2, 18, 30), end: at(2, 19), link: 'https://meet.google.com/', organizer: 'Prof. Kavya Menon' },
    ],
  }
  return list[staffId] || []
}
