import { defineStore } from 'pinia'
import { buildCohort } from '../data/cohort'
import { STAFF } from '../data/staff'
import { LEVEL_RULES } from '../data/rules'
import { COURSES } from '../data/courses'
import { at, startOfDay } from '../utils/dates'
import { riskWith, summarize } from '../utils/staff'
import { useAuthStore } from './auth'

// Everything on the staff side. Changes made here (assignments, interventions, rules,
// imports) last until the page is reloaded; the full platform saves them in the backend.

const copyMilestones = () => JSON.parse(JSON.stringify({ foundation: LEVEL_RULES.foundation.milestones, diploma: LEVEL_RULES.diploma.milestones }))

function seed() {
  const { students, meta, interventions } = buildCohort()
  const rules = { version: 2, effective: 'Sep 2026', highFails: 2, lowFails: 1, oppeMin: 40, milestones: copyMilestones() }
  const ruleHistory = [
    { version: 1, effective: 'Jan 2026', at: at(-300, 10), by: 'Suresh Pillai', summary: 'High: same course failed 3 times. Low: failed once. OPPE: assignment average 40.', reason: 'First rules for the pilot term' },
    { version: 2, effective: 'Sep 2026', at: at(-62, 10), by: 'Suresh Pillai', summary: 'High: same course failed twice. Low: failed once. OPPE: assignment average 40.', reason: 'May 2026 policy: a second failed attempt now gets instructor support' },
  ]
  const imports = [
    { id: 'imp3', file: 'sep26_week7_scores.csv', category: 'Weekly assignment scores', term: 'Sep 2026', rows: 1290, accepted: 1284, rejected: 6, status: 'succeeded', at: at(-2, 9), by: 'Suresh Pillai' },
    { id: 'imp2', file: 'sep26_registrations.csv', category: 'Course registrations', term: 'Sep 2026', rows: 2410, accepted: 2410, rejected: 0, status: 'succeeded', at: at(-55, 11), by: 'Suresh Pillai' },
    { id: 'imp1', file: 'may26_results.csv', category: 'Term results', term: 'May 2026', rows: 5122, accepted: 5108, rejected: 14, status: 'succeeded', at: at(-60, 10), by: 'Suresh Pillai' },
  ]
  const jobs = [
    { id: 'j1', name: 'Risk recalculation', detail: 'Rule v2, from the week 7 scores import', status: 'succeeded', at: at(-2, 9, 5) },
    { id: 'j2', name: 'Alert: new High-risk students to staff', detail: '2 students, sent in the app and by email', status: 'succeeded', at: at(-2, 9, 10) },
    { id: 'j3', name: 'Email: OPPE 1 eligibility results', detail: 'Mail server rejected 3 addresses that no longer exist', status: 'failed', at: at(-2, 9, 20) },
    { id: 'j4', name: 'Weekly study plan reminders to students', detail: 'Scheduled for tomorrow, 8:00 am', status: 'pending', at: at(1, 8) },
  ]
  const users = [
    ...Object.values(STAFF).map((s) => ({ email: `${s.id}@disha.demo`, name: s.name, role: s.role, title: s.title, active: true })),
    { email: 'rakesh@disha.demo', name: 'Rakesh Jha', role: 'support', title: 'Support TA (left in May 2026)', active: false },
  ]

  // The audit log starts with the history behind the sample data.
  const audit = []
  const name = (id) => STAFF[id]?.name || id
  for (const r of ruleHistory) audit.push({ at: r.at, who: r.by, action: 'Rule change', details: `Rules v${r.version} from ${r.effective}. ${r.summary} Reason: ${r.reason}.` })
  for (const i of imports) audit.push({ at: i.at, who: i.by, action: 'Data import', details: `${i.category}, ${i.term}: ${i.accepted.toLocaleString('en-IN')} rows accepted, ${i.rejected} rejected (${i.file}).` })
  audit.push({ at: at(-2, 9, 5), who: 'System', action: 'Risk recalculation', details: 'Rules v2 on the week 7 scores import. 2 students moved to High risk.' })
  for (const s of students) {
    for (const h of meta[s.id].ownerHistory) audit.push({ at: h.at, who: name(h.by), action: 'Assignment', studentId: s.id, details: `${s.name} assigned to ${name(h.owner)}. Reason: ${h.reason}.` })
  }
  for (const i of interventions) {
    audit.push({ at: i.at, who: name(i.by), action: 'Intervention', studentId: i.studentId, details: `${cap(i.type)} logged for ${students.find((s) => s.id === i.studentId).name}${i.referralTo ? `, referred to ${name(i.referralTo)}` : ''}.` })
  }
  audit.sort((a, b) => b.at - a.at)
  audit.forEach((e, n) => { e.id = `a${audit.length - n}` })

  return { students, meta, interventions, rules, ruleHistory, imports, jobs, users, audit, llmEnabled: true, shared: {}, lastRecalc: at(-2, 9, 5) }
}

const cap = (s) => s[0].toUpperCase() + s.slice(1)

export const useStaffStore = defineStore('staff', {
  state: seed,
  getters: {
    rows(s) {
      return s.students.map((st) => summarize(st, s.meta[st.id], s.rules))
    },
    row() {
      return (id) => this.rows.find((r) => r.id === id) || null
    },
    historyOf: (s) => (id) => s.interventions.filter((i) => i.studentId === id).sort((a, b) => b.at - a.at),
    statusOf() {
      return (id) => {
        const latest = this.historyOf(id)[0]
        if (latest) return latest.outcome
        const row = this.row(id)
        if (!row || row.risk.level === 'none') return null
        // Low risk without an owner follows the study plan; no contact is expected yet.
        if (row.risk.level === 'low' && !row.owner) return null
        return 'not_contacted'
      }
    },
    atRisk() {
      return this.rows.filter((r) => r.risk.level !== 'none')
    },
    followUps(s) {
      const latest = {}
      for (const i of s.interventions) if (!latest[i.studentId] || i.at > latest[i.studentId].at) latest[i.studentId] = i
      const end = startOfDay(at(1, 0))
      return Object.values(latest)
        .filter((i) => i.followUp && i.outcome !== 'resolved')
        .map((i) => ({ ...i, overdue: i.followUp < startOfDay(new Date()), due: i.followUp < end }))
        .sort((a, b) => a.followUp - b.followUp)
    },
    caseload() {
      return Object.values(STAFF)
        .filter((m) => m.role === 'support')
        .map((m) => ({ ...m, cases: this.atRisk.filter((r) => r.owner === m.id) }))
    },
  },
  actions: {
    who() {
      return useAuthStore().user?.name || 'Unknown user'
    },
    log(action, details, studentId = null) {
      this.audit.unshift({ id: `a${this.audit.length + 1}`, at: new Date(), who: this.who(), action, details, studentId })
    },
    assign(ids, owner, reason) {
      for (const id of ids) {
        const m = this.meta[id]
        const before = m.owner
        m.owner = owner
        m.ownerHistory.push({ owner, at: new Date(), by: this.who(), reason })
        const s = this.students.find((x) => x.id === id)
        this.log('Assignment', `${s.name} ${before ? `reassigned from ${STAFF[before].name} to` : 'assigned to'} ${STAFF[owner].name}. Reason: ${reason}.`, id)
      }
    },
    logIntervention(rec) {
      const me = useAuthStore().user
      const item = { id: `i${this.interventions.length + 1}-${Date.now()}`, referralTo: null, followUp: null, ...rec, by: me?.staffId || 'suresh' }
      this.interventions.push(item)
      const s = this.students.find((x) => x.id === rec.studentId)
      this.log('Intervention', `${cap(rec.type)} logged for ${s.name}${rec.referralTo ? `, referred to ${STAFF[rec.referralTo].name}` : ''}. Outcome: ${rec.outcome.replace('_', ' ')}.`, rec.studentId)
      return item
    },
    setOutcome(studentId, outcome) {
      const latest = this.historyOf(studentId)[0]
      const s = this.students.find((x) => x.id === studentId)
      if (latest) latest.outcome = outcome
      else {
        this.interventions.push({ id: `i${this.interventions.length + 1}-${Date.now()}`, studentId, courseId: this.row(studentId)?.risk.focus?.course.id || null, reason: 'status', type: 'call', at: new Date(), by: useAuthStore().user?.staffId || 'suresh', notes: 'Status changed on the board.', followUp: null, referralTo: null, outcome })
      }
      this.log('Outcome', `${s.name}: case marked "${outcome.replace('_', ' ')}".`, studentId)
    },
    toggleShared(studentId, key, text) {
      const list = this.shared[studentId] || (this.shared[studentId] = [])
      const idx = list.indexOf(key)
      if (idx >= 0) list.splice(idx, 1)
      else {
        list.push(key)
        const s = this.students.find((x) => x.id === studentId)
        this.log('Suggestion shared', `${s.name}: "${text}"`, studentId)
      }
    },
    previewRules(next) {
      const problems = []
      if (!(next.highFails > next.lowFails)) problems.push('High risk must need more failed attempts than Low risk.')
      if (next.lowFails < 1) problems.push('Low risk needs at least one failed attempt.')
      if (!(next.oppeMin >= 0 && next.oppeMin <= 100)) problems.push('The OPPE threshold must be between 0 and 100.')
      for (const [lv, list] of Object.entries(next.milestones)) {
        list.forEach((m, i) => {
          const prev = list[i - 1]
          if (m.byTerm > LEVEL_RULES[lv].limitTerms) problems.push(`${LEVEL_RULES[lv].label}: milestone ${i + 1} is after the ${LEVEL_RULES[lv].limitTerms}-term limit.`)
          if (prev && (m.byTerm <= prev.byTerm || m.courses < prev.courses)) problems.push(`${LEVEL_RULES[lv].label}: milestone ${i + 1} must come later and need at least as many courses as milestone ${i}.`)
        })
      }
      const changes = this.students
        .map((s) => ({ s, from: riskWith(s, this.rules).level, to: riskWith(s, next).level }))
        .filter((c) => c.from !== c.to)
        .map((c) => ({ id: c.s.id, name: c.s.name, from: c.from, to: c.to }))
      return { problems, changes }
    },
    applyRules(next, reason) {
      const { changes } = this.previewRules(next)
      const version = this.rules.version + 1
      this.rules = { ...JSON.parse(JSON.stringify(next)), version }
      const summary = `High: same course failed ${next.highFails} times. Low: failed ${next.lowFails === 1 ? 'once' : `${next.lowFails} times`}. OPPE: assignment average ${next.oppeMin}.`
      this.ruleHistory.push({ version, effective: next.effective, at: new Date(), by: this.who(), summary, reason })
      this.log('Rule change', `Rules v${version} from ${next.effective}. ${summary} Reason: ${reason}.`)
      this.lastRecalc = new Date()
      this.jobs.unshift({ id: `j${Date.now()}`, name: 'Risk recalculation', detail: `Rules v${version}: ${changes.length} ${changes.length === 1 ? 'student changed' : 'students changed'} risk level`, status: 'succeeded', at: new Date() })
      this.audit.unshift({ id: `a${this.audit.length + 1}`, at: new Date(), who: 'System', action: 'Risk recalculation', details: `Rules v${version}: ${changes.length} risk level ${changes.length === 1 ? 'change' : 'changes'}.` })
      return changes
    },
    confirmImport(file, result) {
      const rec = { id: `imp${Date.now()}`, file, category: result.category, term: result.terms.join(', ') || 'None', rows: result.total, accepted: result.accepted.length, rejected: result.rejected.length, status: 'succeeded', at: new Date(), by: this.who() }
      this.imports.unshift(rec)
      this.log('Data import', `${rec.category}, ${rec.term}: ${rec.accepted} rows accepted, ${rec.rejected} rejected (${file}).`)
      const job = { id: `j${Date.now()}`, name: 'Risk recalculation', detail: `Rules v${this.rules.version}, from ${file}`, status: 'running', at: new Date() }
      this.jobs.unshift(job)
      setTimeout(() => {
        const j = this.jobs.find((x) => x.id === job.id)
        if (j) {
          j.status = 'succeeded'
          j.detail = `Rules v${this.rules.version}, from ${file}: ${this.students.length} students checked, no risk level changed`
        }
        this.lastRecalc = new Date()
        this.audit.unshift({ id: `a${this.audit.length + 1}`, at: new Date(), who: 'System', action: 'Risk recalculation', details: `After ${file}: no risk level changed.` })
      }, 1400)
      return rec
    },
    setLLM(on) {
      this.llmEnabled = on
      this.log('Setting', on ? 'Language model for student messages switched on.' : 'Language model for student messages switched off: students now see the rule-based reasons.')
    },
    setUser(email, change) {
      const u = this.users.find((x) => x.email === email)
      if (!u) return
      if ('role' in change && change.role !== u.role) {
        this.log('Access', `${u.name}: role changed from ${u.role} to ${change.role}.`)
        u.role = change.role
      }
      if ('active' in change && change.active !== u.active) {
        u.active = change.active
        this.log('Access', `${u.name}: account ${u.active ? 'reactivated' : 'deactivated'}.`)
      }
    },
  },
})

export const courseName = (id) => COURSES[id]?.name || ''
