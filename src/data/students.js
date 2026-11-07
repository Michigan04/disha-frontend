// Sample students for the demo. Each one shows a different situation:
//   Ananya  Foundation, failed one course once           -> Low risk, AI guidance
//   Rahul   Foundation, failed the same course twice     -> High risk, instructor support
//   Karthik Diploma, no failures                         -> On track
// Dates are relative to today so the demo always shows upcoming events.

import { at, inMinutes } from '../utils/dates'

const span = (start, minutes) => new Date(start.getTime() + minutes * 60000)

export function buildStudents() {
  return [
    {
      id: 'ananya',
      name: 'Ananya Rao',
      firstName: 'Ananya',
      rollNo: '25f1000101',
      level: 'foundation',
      program: 'BS in Data Science and Applications',
      terms: ['Sep 2025', 'Jan 2026', 'May 2026', 'Sep 2026'],
      admittedFrom: 'Sep 2025',
      combinedLimit: null,
      updatedAt: at(-2, 9),
      attempts: [
        { courseId: 'math1', term: 'Sep 2025', grade: 'B' },
        { courseId: 'eng1', term: 'Sep 2025', grade: 'A' },
        { courseId: 'ct', term: 'Sep 2025', grade: 'C' },
        { courseId: 'stats1', term: 'Jan 2026', grade: 'B' },
        { courseId: 'math2', term: 'Jan 2026', grade: 'C' },
        { courseId: 'stats2', term: 'May 2026', grade: 'U' },
        { courseId: 'eng2', term: 'May 2026', grade: 'B' },
        { courseId: 'stats2', term: 'Sep 2026', inProgress: true, week: 7, weeks: 12, assignmentAvg: 64, quiz1: 58 },
        { courseId: 'python', term: 'Sep 2026', inProgress: true, week: 7, weeks: 12, assignmentAvg: 72, quiz1: 66 },
      ],
      oppe: [
        {
          id: 'py-oppe1',
          courseId: 'python',
          title: 'OPPE 1',
          date: at(9, 10),
          criteria: [
            { label: 'Average of the best 5 of the first 7 weekly assignments', required: 40, actual: 72, final: true },
            { label: 'Quiz 1 attended', required: true, actual: true, final: true },
          ],
        },
        {
          id: 'py-oppe2',
          courseId: 'python',
          title: 'OPPE 2',
          date: at(30, 10),
          criteria: [
            { label: 'Average of the best 6 of the first 9 weekly assignments', required: 40, actual: 70, final: false, finalOn: at(14, 23, 59) },
            { label: 'OPPE 1 attempted', required: true, actual: null, final: false, finalOn: at(9, 13) },
          ],
        },
      ],
      meetings: [
        { id: 'm0', title: 'Programming in Python live session: dictionaries', start: inMinutes(70), end: span(inMinutes(70), 60), link: 'https://meet.google.com/', organizer: 'Python course team' },
        { id: 'm1', title: 'Statistics II live session: hypothesis testing', start: at(1, 19), end: at(1, 20), link: 'https://meet.google.com/', organizer: 'Statistics II course team' },
        { id: 'm2', title: 'Programming in Python doubt-clearing session', start: at(3, 20), end: at(3, 21), link: 'https://meet.google.com/', organizer: 'Python course TAs' },
        { id: 'm3', title: 'Python OPPE 1 mock test', start: at(6, 10), end: at(6, 11, 30), link: '', organizer: 'Exam cell', location: 'Online exam portal' },
        { id: 'm4', title: 'Statistics II revision session', start: at(8, 19), end: at(8, 20, 30), link: 'https://meet.google.com/', organizer: 'Statistics II course team' },
      ],
    },
    {
      id: 'rahul',
      name: 'Rahul Verma',
      firstName: 'Rahul',
      rollNo: '25f1000214',
      level: 'foundation',
      program: 'BS in Data Science and Applications',
      terms: ['Sep 2025', 'Jan 2026', 'May 2026', 'Sep 2026'],
      admittedFrom: 'Sep 2025',
      combinedLimit: null,
      updatedAt: at(-2, 9),
      attempts: [
        { courseId: 'math1', term: 'Sep 2025', grade: 'B' },
        { courseId: 'eng1', term: 'Sep 2025', grade: 'B' },
        { courseId: 'ct', term: 'Sep 2025', grade: 'B' },
        { courseId: 'stats1', term: 'Jan 2026', grade: 'C' },
        { courseId: 'python', term: 'Jan 2026', grade: 'U' },
        { courseId: 'python', term: 'May 2026', grade: 'U' },
        { courseId: 'math2', term: 'May 2026', grade: 'C' },
        { courseId: 'python', term: 'Sep 2026', inProgress: true, week: 7, weeks: 12, assignmentAvg: 31, quiz1: 42 },
        { courseId: 'stats2', term: 'Sep 2026', inProgress: true, week: 7, weeks: 12, assignmentAvg: 58, quiz1: 55 },
      ],
      intervention: {
        courseId: 'python',
        instructor: 'Prof. Kavya Menon',
        role: 'Course instructor, Programming in Python',
        status: 'Session booked',
        meetingAt: at(2, 18, 30),
        link: 'https://meet.google.com/',
        reason: 'Programming in Python has not been cleared in two attempts.',
        plan: [
          'A 30-minute check-in with the instructor every week until OPPE 2.',
          'A set of 20 OPPE-style problems, reviewed by a course TA each Sunday.',
          'A mock OPPE in Week 9 under exam conditions, with feedback the same day.',
        ],
      },
      oppe: [
        {
          id: 'py-oppe1',
          courseId: 'python',
          title: 'OPPE 1',
          date: at(9, 10),
          criteria: [
            { label: 'Average of the best 5 of the first 7 weekly assignments', required: 40, actual: 31, final: true },
            { label: 'Quiz 1 attended', required: true, actual: true, final: true },
          ],
          ifNotEligible: 'Weeks 8 and 9 still count towards OPPE 2. Bring your average up to 40 to sit OPPE 2.',
        },
        {
          id: 'py-oppe2',
          courseId: 'python',
          title: 'OPPE 2',
          date: at(30, 10),
          criteria: [
            { label: 'Average of the best 6 of the first 9 weekly assignments', required: 40, actual: 36, final: false, finalOn: at(14, 23, 59) },
          ],
        },
      ],
      meetings: [
        { id: 'r0', title: 'Python doubt-clearing with your course TA', start: inMinutes(40), end: span(inMinutes(40), 30), link: 'https://meet.google.com/', organizer: 'Python course TAs', important: true },
        { id: 'r00', title: 'Statistics II live session: sampling', start: inMinutes(180), end: span(inMinutes(180), 60), link: 'https://meet.google.com/', organizer: 'Statistics II course team' },
        { id: 'r1', title: 'Statistics II live session: hypothesis testing', start: at(1, 19), end: at(1, 20), link: 'https://meet.google.com/', organizer: 'Statistics II course team' },
        { id: 'r2', title: 'Check-in with Prof. Kavya Menon', start: at(2, 18, 30), end: at(2, 19), link: 'https://meet.google.com/', organizer: 'Prof. Kavya Menon', important: true },
        { id: 'r3', title: 'Programming in Python doubt-clearing session', start: at(3, 20), end: at(3, 21), link: 'https://meet.google.com/', organizer: 'Python course TAs' },
        { id: 'r4', title: 'Python OPPE 1 mock test', start: at(6, 10), end: at(6, 11, 30), link: '', organizer: 'Exam cell', location: 'Online exam portal' },
      ],
    },
    {
      id: 'karthik',
      name: 'Karthik Iyer',
      firstName: 'Karthik',
      rollNo: '24f2000377',
      level: 'diploma',
      program: 'Diploma in Programming',
      terms: ['Jan 2026', 'May 2026', 'Sep 2026'],
      admittedFrom: 'Sep 2024',
      combinedLimit: null,
      updatedAt: at(-1, 9),
      attempts: [
        { courseId: 'dbms', term: 'Jan 2026', grade: 'A' },
        { courseId: 'pdsa', term: 'Jan 2026', grade: 'B' },
        { courseId: 'mad1', term: 'May 2026', grade: 'A' },
        { courseId: 'mad1p', term: 'May 2026', grade: 'S' },
        { courseId: 'sc', term: 'May 2026', grade: 'B' },
        { courseId: 'java', term: 'Sep 2026', inProgress: true, week: 7, weeks: 12, assignmentAvg: 81, quiz1: 74 },
        { courseId: 'mad2', term: 'Sep 2026', inProgress: true, week: 7, weeks: 12, assignmentAvg: 77, quiz1: 70 },
      ],
      oppe: [
        {
          id: 'java-oppe1',
          courseId: 'java',
          title: 'OPPE 1',
          date: at(12, 14),
          criteria: [
            { label: 'Average of the best 5 of the first 7 weekly assignments', required: 40, actual: 81, final: true },
          ],
        },
      ],
      meetings: [
        { id: 'k0', title: 'MAD II project mentor call', start: inMinutes(95), end: span(inMinutes(95), 30), link: 'https://meet.google.com/', organizer: 'Project mentor' },
        { id: 'k1', title: 'Java live session: interfaces and generics', start: at(1, 19), end: at(1, 20), link: 'https://meet.google.com/', organizer: 'Java course team' },
        { id: 'k2', title: 'MAD II project viva slot booking opens', start: at(4, 9), end: at(4, 9, 30), link: '', organizer: 'Project team', location: 'Student portal' },
        { id: 'k3', title: 'Java OPPE 1 mock test', start: at(9, 14), end: at(9, 15, 30), link: '', organizer: 'Exam cell', location: 'Online exam portal' },
      ],
    },
  ]
}
