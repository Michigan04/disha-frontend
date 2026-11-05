// CSV upload for the administrator (US-10): parse in the browser, check every row,
// and report rejected rows with their row number and reason. Nothing is sent anywhere.

import { COURSES } from '../data/courses'

// Sample course codes for the upload files.
export const COURSE_CODES = {
  BSMA1001: 'math1', BSMA1002: 'stats1', BSCS1001: 'ct', BSHS1001: 'eng1',
  BSMA1003: 'math2', BSMA1004: 'stats2', BSCS1002: 'python', BSHS1002: 'eng2',
  BSCS2001: 'dbms', BSCS2002: 'pdsa', BSCS2003: 'mad1', BSCS2003P: 'mad1p',
  BSSE2001: 'sc', BSCS2005: 'java', BSCS2006: 'mad2', BSCS2006P: 'mad2p',
}

export const CATEGORIES = {
  results: {
    label: 'Term results',
    columns: ['roll_no', 'course_code', 'term', 'grade'],
    example: ['25f1000101', 'BSMA1004', 'May 2026', 'U'],
  },
  registrations: {
    label: 'Course registrations',
    columns: ['roll_no', 'course_code', 'term'],
    example: ['25f1000101', 'BSMA1004', 'Sep 2026'],
  },
  scores: {
    label: 'Weekly assignment scores',
    columns: ['roll_no', 'course_code', 'term', 'week', 'score'],
    example: ['25f1000101', 'BSMA1004', 'Sep 2026', '7', '64'],
  },
}

export const SAMPLE_FILES = {
  scores: [
    'roll_no,course_code,term,week,score',
    '25f1000101,BSMA1004,Sep 2026,8,71',
    '25f1000101,BSCS1002,Sep 2026,8,78',
    '25f1000214,BSCS1002,Sep 2026,8,46',
    '25f1000214,BSMA1004,Sep 2026,8,60',
    '24f2000377,BSCS2005,Sep 2026,8,84',
    '24f2000377,BSCS2006,Sep 2026,8,80',
    '25f1101833,BSCS1002,Sep 2026,8,',
    '25f1103566,BSMA1004,Sep 2026,8,58',
    '25f1103566,BSMA1004,Sep 2026,8,58',
    '25f1105299,BSCS9999,Sep 2026,8,66',
    '25f1107032,BSCS1002,Sep 2026,14,72',
    '25f1108765,BSMA1003,Sep 2026,8,91',
    'abc123,BSMA1001,Sep 2026,8,55',
    '25f1110498,BSHS1002,Sep 2026,8,74',
  ].join('\n'),
}

export function parseCsv(text) {
  const rows = []
  let row = []
  let cell = ''
  let quoted = false
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i]
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') {
        cell += '"'
        i += 1
      } else if (ch === '"') quoted = false
      else cell += ch
    } else if (ch === '"') quoted = true
    else if (ch === ',') {
      row.push(cell)
      cell = ''
    } else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i += 1
      row.push(cell)
      rows.push(row)
      row = []
      cell = ''
    } else cell += ch
  }
  if (cell !== '' || row.length) {
    row.push(cell)
    rows.push(row)
  }
  return rows.filter((r) => r.some((c) => c.trim() !== ''))
}

const TERM_RE = /^(Jan|May|Sep) 20\d\d$/
const ROLL_RE = /^\d{2}f\d{7}$/
const GRADES = ['S', 'A', 'B', 'C', 'D', 'E', 'U']

/** Check a parsed file against its category. Returns accepted rows and rejected rows with reasons. */
export function validate(rows, categoryKey) {
  const cat = CATEGORIES[categoryKey]
  if (!rows.length) return { error: 'The file is empty.' }
  const header = rows[0].map((h) => h.trim().toLowerCase())
  const missing = cat.columns.filter((c) => !header.includes(c))
  if (missing.length) return { error: `Missing column${missing.length > 1 ? 's' : ''}: ${missing.join(', ')}. Download the template to see the expected columns.` }

  const idx = Object.fromEntries(cat.columns.map((c) => [c, header.indexOf(c)]))
  const seen = new Set()
  const accepted = []
  const rejected = []
  const terms = new Set()

  rows.slice(1).forEach((r, i) => {
    const line = i + 2
    const v = Object.fromEntries(cat.columns.map((c) => [c, (r[idx[c]] ?? '').trim()]))
    const empty = cat.columns.filter((c) => v[c] === '')
    let reason = null
    if (empty.length) reason = `Missing ${empty.join(', ')}`
    else if (!ROLL_RE.test(v.roll_no)) reason = `Roll number "${v.roll_no}" is not in the expected format`
    else if (!COURSE_CODES[v.course_code.toUpperCase()]) reason = `Unknown course code ${v.course_code}`
    else if (!TERM_RE.test(v.term)) reason = `Term "${v.term}" should look like Sep 2026`
    else if (categoryKey === 'results' && !GRADES.includes(v.grade.toUpperCase())) reason = `Grade "${v.grade}" is not one of S, A, B, C, D, E, U`
    else if (categoryKey === 'scores' && !(Number(v.week) >= 1 && Number(v.week) <= 12)) reason = `Week ${v.week} is outside 1 to 12`
    else if (categoryKey === 'scores' && !(Number(v.score) >= 0 && Number(v.score) <= 100)) reason = `Score ${v.score} is outside 0 to 100`
    if (!reason) {
      const key = [v.roll_no, v.course_code.toUpperCase(), v.term, v.week || ''].join('|')
      if (seen.has(key)) reason = `Duplicate of an earlier row for the same student, course and ${categoryKey === 'scores' ? 'week' : 'term'}`
      seen.add(key)
    }
    if (reason) rejected.push({ line, reason, raw: r.join(',') })
    else {
      accepted.push({ ...v, course: COURSES[COURSE_CODES[v.course_code.toUpperCase()]] })
      terms.add(v.term)
    }
  })
  return { accepted, rejected, total: rows.length - 1, terms: [...terms], category: cat.label }
}

export function templateCsv(categoryKey) {
  const cat = CATEGORIES[categoryKey]
  return `${cat.columns.join(',')}\n${cat.example.join(',')}\n`
}
