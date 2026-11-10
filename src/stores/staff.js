import { defineStore } from 'pinia'
import { STAFF } from '../data/staff'
import { LEVEL_RULES } from '../data/rules'
import { COURSES } from '../data/courses'
import { loadReference } from '../data/reference'
import { api } from '../services/api'
import { at, startOfDay } from '../utils/dates'
import { riskWith, summarize } from '../utils/staff'
import { useAuthStore } from './auth'

// Everything on the staff side, loaded from GET /api/staff/bootstrap.
// Each action shows its change on the page straight away, sends it to the backend,
// then reloads so the page matches what was saved. If the backend refuses, the
// reload undoes the change and `error` says why.

const cap = (s) => s[0].toUpperCase() + s.slice(1)
const clone = (x) => JSON.parse(JSON.stringify(x))

const empty = () => ({
  students: [], meta: {}, interventions: [],
  rules: { version: 0, effective: '', highFails: 2, lowFails: 1, oppeMin: 40, milestones: {} },
  ruleHistory: [], imports: [], jobs: [], users: [], audit: [],
  llmEnabled: true, shared: {}, lastRecalc: null,
  loaded: false, error: '',
})

export const useStaffStore = defineStore('staff', {
  state: empty,
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
    async load() {
      const data = await api.get('/staff/bootstrap')
      this.$patch((s) => {
        Object.assign(s, data)
        s.loaded = true
      })
    },
    clear() {
      this.$reset()
    },
    /** Send a change to the backend, then reload so the page shows what was saved. */
    async save(request, { reference = false } = {}) {
      this.error = ''
      let result = null
      try {
        result = await request
      } catch (err) {
        this.error = err.message
      }
      try {
        if (reference) await loadReference()
        await this.load()
      } catch (err) {
        this.error = this.error || err.message
      }
      return result
    },
    who() {
      return useAuthStore().user?.name || 'Unknown user'
    },
    me() {
      return useAuthStore().user?.staffId || null
    },
    // Shown at once; replaced by the saved entry on the reload.
    log(action, details, studentId = null) {
      this.audit.unshift({ id: `new-${Date.now()}-${this.audit.length}`, at: new Date(), who: this.who(), action, details, studentId })
    },
    assign(ids, owner, reason) {
      for (const id of ids) {
        const m = this.meta[id]
        const before = m.owner
        m.owner = owner
        m.ownerHistory.push({ owner, at: new Date(), by: this.me(), reason })
        const s = this.students.find((x) => x.id === id)
        this.log('Assignment', `${s.name} ${before ? `reassigned from ${STAFF[before]?.name} to` : 'assigned to'} ${STAFF[owner]?.name}. Reason: ${reason}.`, id)
      }
      return this.save(api.post('/staff/assignments', { studentIds: ids, owner, reason }))
    },
    logIntervention(rec) {
      const item = { id: `new-${Date.now()}`, referralTo: null, followUp: null, ...rec, by: this.me() }
      this.interventions.push(item)
      const s = this.students.find((x) => x.id === rec.studentId)
      this.log('Intervention', `${cap(rec.type)} logged for ${s.name}${rec.referralTo ? `, referred to ${STAFF[rec.referralTo]?.name}` : ''}. Outcome: ${rec.outcome.replace('_', ' ')}.`, rec.studentId)
      this.save(api.post('/staff/interventions', rec))
      return item
    },
    setOutcome(studentId, outcome) {
      const latest = this.historyOf(studentId)[0]
      const s = this.students.find((x) => x.id === studentId)
      if (latest) latest.outcome = outcome
      else {
        this.interventions.push({ id: `new-${Date.now()}`, studentId, courseId: this.row(studentId)?.risk.focus?.course.id || null, reason: 'status', type: 'call', at: new Date(), by: this.me(), notes: 'Status changed on the board.', followUp: null, referralTo: null, outcome })
      }
      this.log('Outcome', `${s.name}: case marked "${outcome.replace('_', ' ')}".`, studentId)
      return this.save(api.put(`/staff/students/${studentId}/outcome`, { outcome }))
    },
    toggleShared(studentId, key, text) {
      const list = this.shared[studentId] || (this.shared[studentId] = [])
      const idx = list.indexOf(key)
      if (idx >= 0) list.splice(idx, 1)
      else list.push(key)
      return this.save(api.post(`/staff/students/${studentId}/shared`, { key, text }))
    },
    // A quick check in the browser while the administrator edits; the backend repeats
    // the same checks before anything is saved.
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
    /** Saves the rules as the next version; the backend recalculates everyone's risk. */
    async applyRules(next, reason) {
      const { version, ...rules } = clone(next)
      const res = await this.save(api.post('/rules', { rules, reason }), { reference: true })
      return res?.changes || null
    },
    /** Applies an upload the backend has already checked (see DataView). */
    async confirmImport(importId) {
      const res = await this.save(api.post(`/imports/${importId}/commit`))
      return res?.import || null
    },
    setLLM(on) {
      this.llmEnabled = on
      return this.save(api.put('/admin/settings/llm', { enabled: on }))
    },
    setUser(id, change) {
      const u = this.users.find((x) => x.id === id)
      if (!u) return null
      if ('role' in change) u.role = change.role
      if ('active' in change) u.active = change.active
      return this.save(api.patch(`/admin/users/${id}`, change), { reference: true })
    },
  },
})

export const courseName = (id) => COURSES[id]?.name || ''
