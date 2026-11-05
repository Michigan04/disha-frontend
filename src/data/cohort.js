// The demo cohort that staff see: the three demo students plus 57 generated ones.
// Generated students have the same shape as the demo students, so staff pages reuse
// the exact rules the student pages use (CGPA, milestones, risk, OPPE, prediction).
// A fixed seed keeps the cohort identical on every load.

import { at } from '../utils/dates'
import { buildStudents } from './students'
import { COURSES, LEVEL_COURSES } from './courses'
import { INSTRUCTOR_FOR, STAFF } from './staff'
import { risk } from '../utils/progress'

const TERMS = ['Jan 2024', 'May 2024', 'Sep 2024', 'Jan 2025', 'May 2025', 'Sep 2025', 'Jan 2026', 'May 2026', 'Sep 2026']
const PASS_GRADES = ['S', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C', 'D', 'E']

// [name, level, current term number, situation]
// situation: ok | once:<course> | twice:<course> | oppe:<course> | lowpred:<course>
const SPECS = [
  ['Rohit Bansal', 'F', 4, 'twice:python'],
  ['Priya Nair', 'F', 3, 'once:stats1'],
  ['Vikram Singh', 'F', 4, 'twice:stats2'],
  ['Sneha Patil', 'F', 2, 'ok'],
  ['Farhan Qureshi', 'F', 3, 'once:python'],
  ['Meera Joshi', 'F', 4, 'oppe:python'],
  ['Kabir Malhotra', 'F', 3, 'twice:ct'],
  ['Nandini Bose', 'F', 2, 'once:math1'],
  ['Tanvi Deshmukh', 'F', 4, 'once:stats2'],
  ['Harsh Agarwal', 'F', 3, 'lowpred:stats2'],
  ['Zoya Mirza', 'F', 2, 'ok'],
  ['Aditya Chauhan', 'F', 4, 'twice:python'],
  ['Ritika Saxena', 'F', 3, 'once:python'],
  ['Manav Thakur', 'F', 2, 'ok'],
  ['Ishita Banerjee', 'F', 4, 'once:math2'],
  ['Pranav Hegde', 'F', 3, 'ok'],
  ['Simran Kaur', 'F', 4, 'oppe:python'],
  ['Varun Bhat', 'F', 3, 'once:ct'],
  ['Anjali Mishra', 'F', 2, 'ok'],
  ['Yash Jain', 'F', 4, 'twice:stats2'],
  ['Pooja Rawat', 'F', 3, 'ok'],
  ['Nikhil Shetty', 'F', 4, 'once:python'],
  ['Sana Ansari', 'F', 2, 'lowpred:math1'],
  ['Devansh Arora', 'F', 3, 'ok'],
  ['Kritika Rathore', 'F', 4, 'once:stats1'],
  ['Omkar Pawar', 'F', 3, 'ok'],
  ['Lavanya Krishnan', 'F', 2, 'ok'],
  ['Rehan Siddiqui', 'F', 4, 'ok'],
  ['Shruti Pandey', 'D', 3, 'twice:pdsa'],
  ['Tushar Goyal', 'D', 2, 'once:dbms'],
  ['Bhavna Chawla', 'D', 3, 'ok'],
  ['Gaurav Yadav', 'D', 2, 'oppe:sc'],
  ['Aishwarya Subramanian', 'D', 3, 'once:java'],
  ['Imran Lone', 'D', 2, 'lowpred:pdsa'],
  ['Divya Prakash', 'D', 1, 'ok'],
  ['Kunal Sethi', 'D', 3, 'once:sc'],
  ['Megha Tripathi', 'D', 2, 'ok'],
  ['Abhinav Dutta', 'F', 3, 'once:stats2'],
  ['Riya Kapoor', 'F', 2, 'ok'],
  ['Sameer Naik', 'F', 4, 'twice:python'],
  ['Ankita Dubey', 'F', 3, 'lowpred:python'],
  ['Ishaan Kohli', 'F', 3, 'once:python'],
  ['Arnav Choudhary', 'F', 2, 'ok'],
  ['Tara Iyengar', 'F', 3, 'ok'],
  ['Mohit Chandra', 'F', 4, 'ok'],
  ['Neelam Bhatt', 'F', 2, 'ok'],
  ['Siddhi Kamath', 'D', 2, 'ok'],
  ['Parth Shah', 'F', 3, 'ok'],
  ['Ayesha Khan', 'F', 4, 'ok'],
  ['Rishabh Tiwari', 'D', 3, 'ok'],
  ['Pallavi Desai', 'F', 2, 'ok'],
  ['Vivek Rana', 'F', 3, 'ok'],
  ['Juhi Saini', 'D', 1, 'ok'],
  ['Akash Mehra', 'F', 4, 'ok'],
  ['Natasha D’Souza', 'F', 3, 'ok'],
  ['Uday Raghavan', 'D', 2, 'ok'],
  ['Komal Rajput', 'F', 2, 'ok'],
]

const NEW_HIGH = ['Vikram Singh', 'Aditya Chauhan']
const UNASSIGNED_HIGH = ['Vikram Singh', 'Yash Jain']
const DATA_ISSUES = {
  'Zoya Mirza': 'Quiz 1 score missing for the current term',
  'Omkar Pawar': 'Two different grades uploaded for English II (May 2026)',
}

function prng(seed) {
  let s = seed >>> 0
  return () => {
    s = (Math.imul(s, 1664525) + 1013904223) >>> 0
    return s / 4294967296
  }
}

const slug = (name) => name.toLowerCase().replace(/[^a-z]+/g, '-').replace(/^-|-$/g, '')

function generate([name, lv, T, situation], i) {
  const rand = prng(7919 * (i + 3))
  const r = (a, b) => a + Math.floor(rand() * (b - a + 1))
  const pick = (list) => list[Math.floor(rand() * list.length)]
  const level = lv === 'F' ? 'foundation' : 'diploma'
  const [kind, focus] = situation.split(':')
  const fails = kind === 'twice' ? 2 : kind === 'once' ? 1 : 0
  const terms = TERMS.slice(TERMS.length - T)
  const admittedFrom = level === 'foundation' ? terms[0] : TERMS[Math.max(0, TERMS.length - T - 4)]

  const queue = LEVEL_COURSES[level].filter((id) => id !== focus)
  const attempts = []
  const needNow = focus ? 1 : 2
  for (let k = 0; k < T - 1; k += 1) {
    let n = k === 0 ? 3 : 2
    if (level === 'diploma') n = 2
    n = Math.max(0, Math.min(n, queue.length - needNow))
    for (const id of queue.splice(0, n)) attempts.push({ courseId: id, term: terms[k], grade: pick(PASS_GRADES) })
    // failed attempts of the focus course sit in the terms just before this one
    if (fails && k >= T - 1 - fails) attempts.push({ courseId: focus, term: terms[k], grade: 'U' })
  }

  const now = terms[T - 1]
  const current = focus ? [focus, ...queue.slice(0, 1)] : queue.slice(0, 2)
  for (const id of current) {
    const a = { courseId: id, term: now, inProgress: true, week: 7, weeks: 12 }
    if (COURSES[id].type === 'course') {
      if (id === focus && kind === 'twice') Object.assign(a, { assignmentAvg: r(26, 44), quiz1: r(30, 50) })
      else if (id === focus && kind === 'once') Object.assign(a, { assignmentAvg: r(48, 72), quiz1: r(42, 66) })
      else if (id === focus && kind === 'oppe') Object.assign(a, { assignmentAvg: r(29, 37), quiz1: r(46, 60) })
      else if (id === focus && kind === 'lowpred') Object.assign(a, { assignmentAvg: r(40, 44), quiz1: r(26, 34) })
      else Object.assign(a, { assignmentAvg: r(58, 92), quiz1: r(50, 90) })
      if (DATA_ISSUES[name] && current.indexOf(id) === 0) delete a.quiz1
    }
    attempts.push(a)
  }

  const oppe = current
    .filter((id) => COURSES[id].oppe)
    .map((id) => {
      const avg = attempts.find((a) => a.courseId === id && a.inProgress).assignmentAvg
      return {
        id: `${id}-oppe1`,
        courseId: id,
        title: 'OPPE 1',
        date: at(id === 'python' ? 9 : 12, 10),
        criteria: [{ label: 'Average of the best 5 of the first 7 weekly assignments', required: 40, actual: avg, final: true }],
      }
    })

  const yy = (level === 'foundation' ? admittedFrom : admittedFrom).slice(-2)
  return {
    id: slug(name),
    name,
    firstName: name.split(' ')[0],
    rollNo: `${yy}f${level === 'foundation' ? 1 : 2}${String(100100 + i * 1733).slice(-6)}`,
    level,
    program: level === 'foundation' ? 'BS in Data Science and Applications' : 'Diploma in Programming',
    terms,
    admittedFrom,
    updatedAt: at(-2, 9),
    attempts,
    oppe,
    meetings: [],
  }
}

/** Students, staff-only details per student, and the intervention history. */
export function buildCohort() {
  const demo = buildStudents()
  const generated = SPECS.map(generate)
  const students = [...demo, ...generated]

  const rand = prng(424242)
  const r = (a, b) => a + Math.floor(rand() * (b - a + 1))
  const support = ['neha', 'arjun', 'fatima']
  let rr = 0

  const meta = {}
  const interventions = []
  let seq = 1
  const add = (x) => interventions.push({ id: `i${seq++}`, referralTo: null, followUp: null, ...x })

  for (const s of students) {
    const rk = risk(s)
    const course = rk.focus?.course
    const m = {
      owner: null,
      flaggedOn: null,
      prevLevel: rk.level,
      dataIssue: DATA_ISSUES[s.name] || null,
      plan: null,
      ownerHistory: [],
    }
    if (rk.level === 'high') {
      const isNew = NEW_HIGH.includes(s.name)
      m.flaggedOn = isNew ? at(-2, 9) : at(-r(24, 70), 9)
      if (isNew) m.prevLevel = 'low'
      if (!UNASSIGNED_HIGH.includes(s.name)) {
        m.owner = s.id === 'rahul' || s.name === 'Rohit Bansal' ? 'neha' : s.name === 'Aditya Chauhan' ? 'arjun' : support[rr++ % 3]
        m.ownerHistory.push({ owner: m.owner, at: new Date(m.flaggedOn.getTime() + (isNew ? 0.2 : 1) * 864e5), by: 'suresh', reason: 'New High-risk case' })
      }
    } else if (rk.level === 'low') {
      m.flaggedOn = at(-r(12, 60), 9)
      m.plan = s.id === 'ananya' ? { done: 18, total: 36, lastActive: at(-1, 21) } : { done: r(3, 24), total: 36, lastActive: at(-r(0, 13), 20) }
      if (s.id !== 'ananya' && rr % 2 === 0) {
        m.owner = support[rr % 3]
        m.ownerHistory.push({ owner: m.owner, at: new Date(m.flaggedOn.getTime() + 2 * 864e5), by: 'suresh', reason: 'Low risk, plan not started' })
      }
      rr += 1
    }
    meta[s.id] = m

    // Intervention history for owned cases
    if (!m.owner || !course) continue
    const ownerName = STAFF[m.owner].name
    const t0 = m.flaggedOn.getTime()
    const d = (days, hour = 11) => {
      const x = new Date(t0 + days * 864e5)
      x.setHours(hour, 0, 0, 0)
      return x
    }

    if (s.id === 'rahul') {
      add({ studentId: s.id, courseId: 'python', reason: 'failed_twice', type: 'email', at: d(2), by: 'neha', notes: 'Shared the Python OPPE practice set and the dates for this term’s OPPEs.', outcome: 'in_progress' })
      add({ studentId: s.id, courseId: 'python', reason: 'failed_twice', type: 'referral', at: d(5), by: 'neha', referralTo: 'kavya', notes: 'Failed Programming in Python twice. Needs hands-on OPPE practice and weekly check-ins.', outcome: 'in_progress' })
      add({ studentId: s.id, courseId: 'python', reason: 'failed_twice', type: 'meeting', at: at(-5, 18, 30), by: 'kavya', notes: 'First check-in. Went through both OPPE attempts: loops and dictionaries are the gap. Set 20 practice problems.', followUp: at(2, 18, 30), outcome: 'in_progress' })
      continue
    }

    if (rk.level === 'high') {
      const instr = INSTRUCTOR_FOR[course.id]
      if (s.name === 'Aditya Chauhan') continue // assigned yesterday, not contacted yet
      add({ studentId: s.id, courseId: course.id, reason: 'failed_twice', type: pickType(s.name), at: d(2), by: m.owner, notes: `Called about ${course.name}. Agreed to attend this week’s doubt session.`, outcome: 'in_progress' })
      const outcome = { 'Rohit Bansal': 'no_response', 'Kabir Malhotra': 'escalated', 'Sameer Naik': 'resolved', 'Shruti Pandey': 'in_progress' }[s.name] || 'in_progress'
      const follow = { 'Rohit Bansal': at(0, 13), 'Kabir Malhotra': at(-1, 12), 'Shruti Pandey': at(-3, 12), 'Sameer Naik': null }[s.name]
      if (instr) {
        add({ studentId: s.id, courseId: course.id, reason: 'failed_twice', type: 'referral', at: d(6), by: m.owner, referralTo: instr, notes: `Referred to ${STAFF[instr].name}: ${course.name} failed twice.`, followUp: follow === undefined ? at(r(1, 6), 12) : follow, outcome })
      } else {
        add({ studentId: s.id, courseId: course.id, reason: 'failed_twice', type: 'meeting', at: d(6), by: m.owner, notes: `Planned the ${course.name} re-attempt week by week with the student.`, followUp: follow === undefined ? at(r(1, 6), 12) : follow, outcome })
      }
      if (s.name === 'Kabir Malhotra') {
        add({ studentId: s.id, courseId: course.id, reason: 'failed_twice', type: 'email', at: at(-1, 12), by: m.owner, notes: `No reply to two calls. Escalated to the program office (${ownerName}).`, followUp: at(-1, 12), outcome: 'escalated' })
      }
      continue
    }

    // Low risk
    const outcome = r(0, 3) === 0 ? 'no_response' : 'in_progress'
    add({ studentId: s.id, courseId: course.id, reason: 'failed_once', type: 'email', at: d(3), by: m.owner, notes: `Shared the 12-week study plan for ${course.name}.`, followUp: at(r(-4, 7), 12), outcome })
  }

  return { students, meta, interventions }

  function pickType(name) {
    return name.length % 2 ? 'call' : 'email'
  }
}
