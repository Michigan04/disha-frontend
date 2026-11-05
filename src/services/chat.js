// "Ask Disha" assistant.
//
// Every reply is a JSON object that follows RESPONSE_SCHEMA. The backend asks the LLM
// (for example Ollama with `format` set to this schema) to answer in this shape; the
// frontend validates it and renders each field. Without VITE_CHAT_API_URL, a built-in
// responder answers common questions from the student's own data, in the same JSON shape.

import { COURSES } from '../data/courses'
import { GRADE_POINTS, LEVEL_RULES, RISK_RULES } from '../data/rules'
import { PAST_STUDENT_INSIGHTS } from '../data/insights'
import { formatDate, formatTime, relativeDay } from '../utils/dates'
import { meets, oppeStatus } from '../utils/progress'
import { predict } from '../utils/predict'

const API_URL = import.meta.env.VITE_CHAT_API_URL

export const RESPONSE_SCHEMA = {
  type: 'object',
  required: ['answer', 'intent', 'key_points', 'actions', 'follow_up_questions', 'sources', 'confidence', 'escalate_to_human'],
  properties: {
    answer: { type: 'string', description: 'Plain-language answer, at most 3 sentences.' },
    intent: { type: 'string', enum: ['cgpa', 'prediction', 'terms', 'oppe', 'failed_course', 'meetings', 'registration', 'general', 'out_of_scope'] },
    key_points: { type: 'array', items: { type: 'string' }, maxItems: 4 },
    actions: {
      type: 'array',
      maxItems: 3,
      items: { type: 'object', required: ['label', 'route'], properties: { label: { type: 'string' }, route: { type: 'string' } } },
    },
    follow_up_questions: { type: 'array', items: { type: 'string' }, maxItems: 3 },
    sources: { type: 'array', items: { type: 'object', required: ['title'], properties: { title: { type: 'string' } } } },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    escalate_to_human: { type: 'boolean', description: 'True when a person (support staff or instructor) should follow up.' },
  },
}

export const SYSTEM_PROMPT = [
  'You are Disha, an assistant for students of the IITM BS degree.',
  'Answer only from the student context and program rules provided. If the answer is not there, say so and set escalate_to_human to true.',
  'Reply with one JSON object that matches the given schema and nothing else.',
  'Keep "answer" under three sentences, in plain words. Use routes from: /, /progress, /courses, /courses/<id>, /oppe, /meetings.',
].join(' ')

export const usingLiveModel = Boolean(API_URL)

// The context sent with every question, also shown to the student on the Ask Disha page.
export function buildContext(store) {
  const s = store.student
  return {
    student: {
      name: s.name,
      level: store.rule.label,
      current_term: `${store.termLabel} (term ${store.termNumber} of ${store.rule.limitTerms})`,
      cgpa: store.cgpa,
      completed: store.done,
      risk_level: store.risk.label,
      courses_needing_attention: store.risk.courses.map((c) => ({ course: c.course.name, failed_attempts: c.status.fails })),
      this_term: store.current.map((c) => {
        const p = predict(s, c.course.id, c.attempt)
        return {
          course: c.course.name,
          week: c.attempt.week,
          assignment_average: c.attempt.assignmentAvg,
          quiz1: c.attempt.quiz1 ?? null,
          predicted_score: p ? Math.round(p.score) : null,
          predicted_grade: p?.grade ?? null,
        }
      }),
      oppe: s.oppe.map((o) => ({ course: COURSES[o.courseId].name, exam: o.title, date: o.date.toISOString(), status: oppeStatus(o) })),
      next_milestone: store.nextMilestone ? `${store.nextMilestone.text} by term ${store.nextMilestone.byTerm}` : 'All milestones met',
      upcoming_meetings: s.meetings.map((m) => ({ title: m.title, start: m.start.toISOString() })),
    },
    program_rules: {
      milestones: LEVEL_RULES[s.level].milestones,
      grade_points: GRADE_POINTS,
      risk_levels: { high: RISK_RULES.high.rule, low: RISK_RULES.low.rule },
    },
  }
}

export function validateResponse(raw) {
  let obj = raw
  if (typeof raw === 'string') {
    try {
      obj = JSON.parse(raw)
    } catch {
      throw new Error('The assistant replied in a format the app could not read.')
    }
  }
  const errors = []
  const isStrArr = (v) => Array.isArray(v) && v.every((x) => typeof x === 'string')
  if (typeof obj?.answer !== 'string' || !obj.answer.trim()) errors.push('answer')
  if (!RESPONSE_SCHEMA.properties.intent.enum.includes(obj?.intent)) errors.push('intent')
  if (!isStrArr(obj?.key_points)) errors.push('key_points')
  if (!Array.isArray(obj?.actions) || !obj.actions.every((a) => typeof a?.label === 'string' && typeof a?.route === 'string')) errors.push('actions')
  if (!isStrArr(obj?.follow_up_questions)) errors.push('follow_up_questions')
  if (!Array.isArray(obj?.sources) || !obj.sources.every((x) => typeof x?.title === 'string')) errors.push('sources')
  if (!['high', 'medium', 'low'].includes(obj?.confidence)) errors.push('confidence')
  if (typeof obj?.escalate_to_human !== 'boolean') errors.push('escalate_to_human')
  if (errors.length) throw new Error(`The assistant's reply was missing: ${errors.join(', ')}.`)
  // Only allow in-app routes in action buttons.
  obj.actions = obj.actions.filter((a) => a.route.startsWith('/'))
  return obj
}

export async function ask(question, history, store) {
  if (API_URL) {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        system: SYSTEM_PROMPT,
        messages: [...history, { role: 'user', content: question }],
        context: buildContext(store),
        response_schema: RESPONSE_SCHEMA,
      }),
    })
    if (!res.ok) throw new Error('The assistant is not reachable right now. Try again in a minute.')
    const data = await res.json()
    return validateResponse(data.response ?? data.message ?? data)
  }
  await new Promise((r) => setTimeout(r, 650))
  return validateResponse(localReply(question, store))
}

// ---------- Built-in responder for the demo ----------

const reply = (intent, answer, extra = {}) => ({
  answer,
  intent,
  key_points: [],
  actions: [],
  follow_up_questions: [],
  sources: [{ title: 'Your academic record in Disha' }],
  confidence: 'high',
  escalate_to_human: false,
  ...extra,
})

function cgpaTarget(store, target) {
  const remaining = store.courses.filter((c) => c.status.state !== 'passed')
  const doneCredits = store.courses.filter((c) => c.status.state === 'passed').reduce((s, c) => s + c.course.credits, 0)
  const restCredits = remaining.reduce((s, c) => s + c.course.credits, 0)
  if (!restCredits) return null
  const need = (target * (doneCredits + restCredits) - store.cgpa * doneCredits) / restCredits
  return Math.round(need * 100) / 100
}

// Short names students use for their courses.
const COURSE_WORDS = {
  stats2: ['stats', 'statistics'],
  python: ['python'],
  java: ['java'],
  mad2: ['mad', 'app dev', 'application development'],
}

function localReply(q, store) {
  const text = q.toLowerCase()
  const s = store.student
  const r = store.risk

  if (/^(hi|hello|hey|namaste)\b/.test(text)) {
    return reply('general', `Hi ${s.firstName}. I can answer questions about your CGPA, terms, OPPE eligibility, failed courses and upcoming sessions.`, {
      follow_up_questions: ['Am I eligible for my next OPPE?', 'How many terms do I have left?', 'What should I do about my failed course?'],
    })
  }

  const target = text.match(/(?:reach|get|need).*?(\d{1,2}(?:\.\d+)?)/)
  if (target && /cgpa|gpa/.test(text)) {
    const t = Number(target[1])
    const need = cgpaTarget(store, t)
    if (need == null) return reply('cgpa', 'You have passed every course at this level, so your CGPA here is final.')
    const ok = need <= 10
    return reply('cgpa', ok
      ? `To reach a CGPA of ${t}, you need an average of about ${Math.max(need, 0)} grade points in your remaining courses, roughly ${need > 9 ? 'an S' : need > 8 ? 'an A' : need > 7 ? 'a B' : 'a C or better'} in each.`
      : `A CGPA of ${t} is no longer reachable at this level, even with S grades in every remaining course.`, {
      key_points: [`Current CGPA: ${store.cgpa.toFixed(2)}`, 'Assumes every remaining course carries its usual credits', 'Grade points: S 10, A 9, B 8, C 7, D 6, E 4'],
      actions: [{ label: 'Open CGPA and terms', route: '/progress' }],
      sources: [{ title: 'Your academic record in Disha' }, { title: 'Grade points (program rules)' }],
      confidence: 'medium',
    })
  }

  if (/focus|this week|priorit|what should i do next|to ?do/.test(text)) {
    const items = []
    if (r.level === 'high' && s.intervention) {
      items.push(`Join your check-in with ${s.intervention.instructor}, ${relativeDay(s.intervention.meetingAt).toLowerCase()} at ${formatTime(s.intervention.meetingAt)}`)
    }
    for (const c of store.current) {
      if (c.attempt.assignmentAvg < 40) items.push(`Raise your ${c.course.name} assignment average: it is ${c.attempt.assignmentAvg}, and the OPPE needs 40`)
    }
    if (r.level === 'low') items.push(`Finish this week's tasks in your ${r.focus.course.name} study plan`)
    const soon = s.oppe.filter((o) => oppeStatus(o) === 'eligible').sort((a, b) => a.date - b.date)[0]
    if (soon) items.push(`Prepare for ${COURSES[soon.courseId].name} ${soon.title} on ${formatDate(soon.date)}`)
    const next = [...s.meetings].sort((a, b) => a.start - b.start)[0]
    if (next) items.push(`Attend "${next.title}", ${relativeDay(next.start).toLowerCase()} at ${formatTime(next.start)}`)
    return reply('general', 'Here is what matters most for you this week.', {
      key_points: items.slice(0, 4),
      actions: [r.focus ? { label: 'Open your plan', route: `/courses/${r.focus.course.id}?tab=plan` } : { label: 'Open courses', route: '/courses' }, { label: 'Open meetings', route: '/meetings' }],
      follow_up_questions: ['Am I eligible for my next OPPE?', 'How many terms do I have left?'],
      sources: [{ title: 'Your academic record in Disha' }, { title: 'Your Google Calendar' }],
    })
  }

  if (/predict|expected|how am i doing|on track|will i pass|final (score|grade|marks)|my (score|marks) (in|for)/.test(text)) {
    const rows = store.current.map((c) => ({ c, p: predict(s, c.course.id, c.attempt) })).filter((x) => x.p)
    if (!rows.length) return reply('prediction', 'You have no course in progress this term, so there is nothing to predict yet.')
    const named = rows.find(({ c }) => (COURSE_WORDS[c.course.id] || [c.course.name.toLowerCase()]).some((w) => text.includes(w)))
    const weakest = named || [...rows].sort((a, b) => a.p.score - b.p.score)[0]
    const sc = Math.round(weakest.p.score)
    const atRisk = sc < 40
    return reply('prediction', atRisk
      ? `At your current pace, ${weakest.c.course.name} is heading for about ${sc} out of 100, which is below the pass mark of 40. Your weekly assignments are the quickest way to move that number.`
      : named
        ? `At your current pace, ${weakest.c.course.name} is heading for about ${sc} out of 100, a grade ${weakest.p.grade}. ${sc < 60 ? 'You are above the pass mark, but close to it, so keep your weekly assignments up.' : 'Keep your weekly assignments steady to hold this grade.'}`
        : `At your current pace, your lowest predicted score this term is ${sc} in ${weakest.c.course.name} (grade ${weakest.p.grade}). Better weekly assignments will lift it the most.`, {
      key_points: rows.map(({ c, p }) => `${c.course.name}: about ${Math.round(p.score)}/100, grade ${p.grade} (likely ${Math.round(p.low)} to ${Math.round(p.high)})`),
      actions: [{ label: `See the ${weakest.c.course.name} prediction`, route: `/courses/${weakest.c.course.id}` }],
      follow_up_questions: ['What should I focus on this week?', 'Am I eligible for my next OPPE?'],
      sources: [{ title: 'Your scores so far in Disha' }, { title: 'Results of past students with similar scores' }],
      confidence: 'medium',
    })
  }

  if (/cgpa|gpa|grade|score/.test(text)) {
    return reply('cgpa', `Your CGPA is ${store.cgpa.toFixed(2)}, from ${store.done.courses + store.done.projects} completed ${store.done.courses + store.done.projects === 1 ? 'course' : 'courses'}. It is the credit-weighted average of the grade points of the courses you have passed.`, {
      key_points: ['A course you have not cleared does not count until you pass it', 'Grade points: S 10, A 9, B 8, C 7, D 6, E 4', 'Your CGPA updates when new results are uploaded'],
      actions: [{ label: 'Open CGPA and terms', route: '/progress' }],
      follow_up_questions: ['What do I need to reach a CGPA of 8?', 'How many terms do I have left?'],
      sources: [{ title: 'Your academic record in Disha' }, { title: 'Grade points (program rules)' }],
    })
  }

  if (/oppe|eligib|proctored/.test(text)) {
    if (!s.oppe.length) return reply('oppe', 'None of your courses this term has an OPPE.', { actions: [{ label: 'Open OPPE eligibility', route: '/oppe' }] })
    const lines = s.oppe.map((o) => {
      const st = oppeStatus(o)
      const name = `${COURSES[o.courseId].name} ${o.title}`
      if (st === 'eligible') return `${name}: eligible (${formatDate(o.date)})`
      if (st === 'not_eligible') {
        const miss = o.criteria.find((c) => c.final && !meets(c))
        return `${name}: not eligible, ${miss.label.toLowerCase()} is ${miss.actual} and needs ${miss.required}`
      }
      return `${name}: decided after ${formatDate(o.criteria.find((c) => !c.final).finalOn)}`
    })
    const anyNo = s.oppe.some((o) => oppeStatus(o) === 'not_eligible')
    return reply('oppe', anyNo
      ? 'You are not eligible for one of your OPPEs yet. The details and what you can still do are below.'
      : 'Here is where you stand for each OPPE this term.', {
      key_points: lines,
      actions: [{ label: 'Open OPPE eligibility', route: '/oppe' }],
      follow_up_questions: ['When is my next OPPE?', 'What counts towards OPPE eligibility?'],
      sources: [{ title: 'OPPE eligibility rules for your courses' }, { title: 'Your weekly assignment scores' }],
    })
  }

  if (/fail|failed|repeat|re-?attempt|again|back ?log|clear/.test(text)) {
    if (r.level === 'high') {
      const iv = s.intervention
      return reply('failed_course', `${r.focus.course.name} has not been cleared in two attempts, so your instructor is supporting you directly. Your next check-in with ${iv.instructor} is ${relativeDay(iv.meetingAt).toLowerCase()} at ${formatTime(iv.meetingAt)}.`, {
        key_points: iv.plan,
        actions: [{ label: 'See your support plan', route: `/courses/${r.focus.course.id}` }, { label: 'Open meetings', route: '/meetings' }],
        follow_up_questions: ['What should I bring to the check-in?', 'Am I eligible for my next OPPE?'],
        sources: [{ title: 'Instructor support plan' }, { title: 'Your academic record in Disha' }],
        escalate_to_human: true,
      })
    }
    if (r.level === 'low') {
      const ins = PAST_STUDENT_INSIGHTS[r.focus.course.id]
      const pct = ins ? Math.round((ins.passedNext / ins.failedOnce) * 100) : null
      return reply('failed_course', ins
        ? `You did not clear ${r.focus.course.name} once, which is common. Of ${ins.failedOnce} past students in the same position, ${pct}% passed on their next attempt.`
        : `You did not clear ${r.focus.course.name} once. Focus on the weekly assignments and the live sessions this term.`, {
        key_points: ins ? ins.whatHelped.slice(0, 3).map((w) => `${w.text} (${w.share}% of those who passed)`) : [],
        actions: [{ label: 'Open your recovery plan', route: `/courses/${r.focus.course.id}` }],
        follow_up_questions: ['How many terms do I have left?', 'Am I eligible for my next OPPE?'],
        sources: [{ title: 'Anonymised outcomes of past students' }, { title: 'Your academic record in Disha' }],
        confidence: 'medium',
      })
    }
    return reply('failed_course', 'You have not failed any course. If you do, Disha will show a recovery plan based on how past students passed the same course.', {
      actions: [{ label: 'Open courses', route: '/courses' }],
    })
  }

  if (/term|milestone|limit|deadline|remov|time left|how long/.test(text)) {
    const m = store.nextMilestone
    const left = store.rule.limitTerms - store.termNumber
    return reply('terms', m
      ? `You are in term ${store.termNumber} of ${store.rule.limitTerms} at the ${store.rule.label} level, with ${left} ${left === 1 ? 'term' : 'terms'} left. Your next milestone is ${m.text} by term ${m.byTerm} (${m.termLabel}).`
      : `You are in term ${store.termNumber} of ${store.rule.limitTerms} and have met every milestone at this level.`, {
      key_points: store.milestones.map((x) => `${x.text} by term ${x.byTerm}: ${x.met ? 'met' : x.state === 'missed' ? 'missed' : `${x.needCourses} more ${x.needCourses === 1 ? 'course' : 'courses'}${x.needProjects ? ` and ${x.needProjects} ${x.needProjects === 1 ? 'project' : 'projects'}` : ''} needed`}`),
      actions: [{ label: 'Open CGPA and terms', route: '/progress' }],
      follow_up_questions: ['What happens if I miss a milestone?', 'What is my CGPA?'],
      sources: [{ title: `${store.rule.label} milestone rules` }, { title: 'Your academic record in Disha' }],
    })
  }

  if (/meeting|session|calendar|class|live|schedule|when is/.test(text)) {
    const next = [...s.meetings].sort((a, b) => a.start - b.start)[0]
    return reply('meetings', next
      ? `Your next session is "${next.title}", ${relativeDay(next.start).toLowerCase()} at ${formatTime(next.start)}.`
      : 'You have no upcoming sessions in the next 30 days.', {
      key_points: s.meetings.slice(1, 4).map((m) => `${m.title}: ${formatDate(m.start)}, ${formatTime(m.start)}`),
      actions: [{ label: 'Open meetings', route: '/meetings' }],
      sources: [{ title: 'Your Google Calendar' }],
    })
  }

  if (/regist|enrol|prerequisite|how many courses|course limit/.test(text)) {
    return reply('registration', 'Registration happens on the IITM portal, which checks prerequisites and the limit of 4 courses per term. Before you register, check how your choice affects your next milestone in CGPA and terms.', {
      key_points: ['Up to 4 courses in a term', 'Some courses need prerequisites to be cleared first', 'A course you failed can be taken again in a later term'],
      actions: [{ label: 'Open CGPA and terms', route: '/progress' }],
      sources: [{ title: 'Program rules' }],
      confidence: 'medium',
    })
  }

  return reply('out_of_scope', 'I do not have enough information to answer that reliably. A member of the support team can help you with it.', {
    follow_up_questions: ['Am I eligible for my next OPPE?', 'How many terms do I have left?', 'What is my CGPA?'],
    sources: [],
    confidence: 'low',
    escalate_to_human: true,
  })
}
