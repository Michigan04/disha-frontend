<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useStaffStore } from '../../stores/staff'
import { STAFF, staffEvents } from '../../data/staff'
import { COURSES } from '../../data/courses'
import { INTERVENTION_TYPES, OUTCOMES } from '../../data/actions'
import { formatDate, greeting, relativeDay } from '../../utils/dates'
import TodayCard from '../../components/TodayCard.vue'
import Icon from '../../components/Icon.vue'
import KpiChart from '../../components/staff/KpiChart.vue'
import Donut from '../../components/staff/Donut.vue'
import Ring from '../../components/staff/Ring.vue'
import StackBar from '../../components/staff/StackBar.vue'
import TrendChart from '../../components/staff/TrendChart.vue'
import Person from '../../components/staff/Person.vue'
import { VIZ, loadColor } from '../../utils/viz'

const auth = useAuthStore()
const staff = useStaffStore()
const isAdmin = computed(() => auth.role === 'admin')
const myId = computed(() => auth.user.staffId)

const high = computed(() => staff.atRisk.filter((r) => r.risk.level === 'high'))
const low = computed(() => staff.atRisk.filter((r) => r.risk.level === 'low'))
const newHigh = computed(() => high.value.filter((r) => r.isNew))
const unassigned = computed(() => high.value.filter((r) => !r.owner))
const predictedFail = computed(() => staff.rows.filter((r) => r.predictedFail))
const mine = computed(() => staff.atRisk.filter((r) => r.owner === myId.value))
const follow = computed(() => staff.followUps.filter((f) => isAdmin.value || staff.meta[f.studentId].owner === myId.value))
const dueNow = computed(() => follow.value.filter((f) => f.due))
const overdue = computed(() => follow.value.filter((f) => f.overdue))

// Courses linked to the most risk flags
const byCourse = computed(() => {
  const map = {}
  const bump = (id, key) => {
    map[id] = map[id] || { course: COURSES[id], high: 0, low: 0, pred: 0 }
    map[id][key] += 1
  }
  for (const r of staff.rows) {
    for (const c of r.risk.courses) bump(c.course.id, r.risk.level)
    for (const c of r.current) if (c.prediction && Math.round(c.prediction.score) < 40 && !r.risk.courses.some((x) => x.course.id === c.course.id)) bump(c.course.id, 'pred')
  }
  return Object.values(map).sort((a, b) => b.high * 3 + b.low + b.pred - (a.high * 3 + a.low + a.pred)).slice(0, 6)
})

// Risk colours, shared by every chart on this page (see utils/viz.js)
const C = { none: VIZ.good, low: VIZ.warning, high: VIZ.critical, pred: VIZ.pred }

// Weekly counts this term, stored at each risk recalculation (risk_snapshots)
const trend = computed(() => {
  const t = staff.riskTrend
  const has = t.labels.length > 0
  return {
    labels: has ? t.labels : ['Now'],
    series: [
      { name: 'Low', color: C.low, values: has ? t.low : [low.value.length] },
      { name: 'High', color: C.high, values: has ? t.high : [high.value.length] },
    ],
  }
})
const signed = (n) => (n > 0 ? `+${n}` : n < 0 ? `\u2212${-n}` : '0')
const change = (vals) => (vals.length ? vals.at(-1) - vals[0] : 0)

// Risk mix of the whole cohort
const riskParts = computed(() => [
  { key: 'high', label: 'High risk', value: high.value.length, color: C.high, to: { path: '/staff/students', query: { risk: 'high' } } },
  { key: 'low', label: 'Low risk', value: low.value.length, color: C.low, to: { path: '/staff/students', query: { risk: 'low' } } },
  { key: 'none', label: 'On track', value: staff.rows.length - staff.atRisk.length, color: C.none },
])
const atRiskPct = computed(() => Math.round((staff.atRisk.length / (staff.rows.length || 1)) * 100))

// Where each at-risk case stands (latest intervention outcome)
const caseRows = computed(() => (isAdmin.value ? staff.atRisk : mine.value))
const caseStatus = computed(() => {
  const count = {}
  for (const r of caseRows.value) {
    const k = staff.statusOf(r.id) || 'plan'
    count[k] = (count[k] || 0) + 1
  }
  const label = (k) => (k === 'plan' ? 'Following the study plan' : OUTCOMES[k].label)
  return Object.entries(count)
    .map(([key, n]) => ({ key, n, label: label(key) }))
    .sort((a, b) => b.n - a.n)
})
// Red = needs action, mustard = stalled, blue = under way, green = done, sand = no case yet
const STATUS_STYLE = {
  not_contacted: { color: VIZ.critical },
  escalated: { color: VIZ.critical, hatch: true },
  no_response: { color: VIZ.warning },
  in_progress: { color: VIZ.active },
  resolved: { color: VIZ.good },
  plan: { color: VIZ.neutral },
}
const STATUS_ORDER = ['not_contacted', 'escalated', 'no_response', 'in_progress', 'resolved', 'plan']
const caseParts = computed(() =>
  [...caseStatus.value]
    .sort((a, b) => STATUS_ORDER.indexOf(a.key) - STATUS_ORDER.indexOf(b.key))
    .map((c) => ({ key: c.key, label: c.label, value: c.n, ...(STATUS_STYLE[c.key] || { color: VIZ.neutral }) })),
)
const needAction = computed(() => caseStatus.value.filter((c) => c.key === 'not_contacted' || c.key === 'escalated').reduce((t, c) => t + c.n, 0))
const riskSlices = (o) => [
  { key: 'high', label: 'High risk', value: o.high, color: C.high },
  { key: 'low', label: 'Low risk', value: o.low, color: C.low },
  { key: 'none', label: 'On track', value: o.none ?? 0, color: C.none },
]
const coursePie = (c) => [
  { key: 'high', label: 'High risk', value: c.high, color: C.high },
  { key: 'low', label: 'Low risk', value: c.low, color: C.low },
  { key: 'pred', label: 'Predicted to fail', value: c.pred, color: C.pred },
]

// Risk mix by level
const byLevel = computed(() => {
  const out = {}
  for (const r of staff.rows) {
    const o = (out[r.level] = out[r.level] || { key: r.level, label: r.levelLabel, n: 0, none: 0, low: 0, high: 0 })
    o.n += 1
    o[r.risk.level] += 1
  }
  return Object.values(out)
})

// Caseload against capacity: the whole support team (admin) or my own (support)
const myCapacity = computed(() => STAFF[myId.value]?.capacity || 12)
const load = computed(() => {
  const cases = isAdmin.value ? staff.caseload.flatMap((m) => m.cases) : mine.value
  const capacity = isAdmin.value ? staff.caseload.reduce((t, m) => t + m.capacity, 0) : myCapacity.value
  return { cases: cases.length, capacity, high: cases.filter((r) => r.risk.level === 'high').length, low: cases.filter((r) => r.risk.level === 'low').length }
})

const lastImport = computed(() => staff.imports[0])
const failedJobs = computed(() => staff.jobs.filter((j) => j.status === 'failed'))
const events = computed(() => staffEvents(myId.value))
</script>

<template>
  <div class="page wide">
    <div class="head-row">
      <header class="head">
        <p class="where">{{ isAdmin ? 'Program administrator' : 'Support staff' }} · Sep 2026 term, week 7</p>
        <h1>{{ greeting() }}, {{ auth.user.name.split(' ')[0] }}</h1>
        <p class="summary">
          <template v-if="isAdmin">{{ high.length }} students are at High risk and {{ low.length }} at Low risk out of {{ staff.rows.length }}. <strong v-if="unassigned.length">{{ unassigned.length }} High-risk {{ unassigned.length === 1 ? 'student has' : 'students have' }} no owner yet.</strong></template>
          <template v-else>You have {{ mine.length }} open {{ mine.length === 1 ? 'case' : 'cases' }}. {{ dueNow.length }} {{ dueNow.length === 1 ? 'follow-up is' : 'follow-ups are' }} due<template v-if="overdue.length">, {{ overdue.length }} of them overdue</template>.</template>
        </p>
        <p class="fresh"><Icon name="clock" :size="15" /> Risk last recalculated {{ relativeDay(staff.lastRecalc).toLowerCase() }}, from {{ lastImport.category.toLowerCase() }} ({{ lastImport.term }})</p>
      </header>
      <TodayCard :events="events" />
    </div>

    <section v-if="newHigh.length" class="alert" aria-labelledby="alert-h">
      <span class="bell"><Icon name="bell" :size="20" /></span>
      <div class="alert-body">
        <h2 id="alert-h">{{ newHigh.length }} {{ newHigh.length === 1 ? 'student' : 'students' }} moved to High risk after the last recalculation</h2>
        <div class="names">
          <RouterLink v-for="r in newHigh" :key="r.id" :to="`/staff/students/${r.id}`" class="name-chip">
            {{ r.name }} <span class="muted">{{ r.main?.text }}</span>
            <span v-if="!r.owner" class="chip high">No owner</span>
          </RouterLink>
        </div>
      </div>
      <RouterLink v-if="isAdmin && unassigned.length" class="btn" :to="{ path: '/staff/students', query: { owner: 'none', risk: 'high' } }">Assign now</RouterLink>
    </section>

    <div class="kpis">
      <KpiChart :value="high.length" label="High risk" icon="alert" tone="high" :delta="signed(change(trend.series[1].values))" :delta-good="change(trend.series[1].values) <= 0" sub="since week 1" :to="{ path: '/staff/students', query: { risk: 'high' } }">
        <Ring :value="high.length" :max="staff.rows.length" :color="C.high" label="Share of students at High risk" />
      </KpiChart>
      <KpiChart :value="low.length" label="Low risk" icon="flag" tone="low" :delta="signed(change(trend.series[0].values))" :delta-good="change(trend.series[0].values) <= 0" sub="since week 1" :to="{ path: '/staff/students', query: { risk: 'low' } }">
        <Ring :value="low.length" :max="staff.rows.length" :color="C.low" label="Share of students at Low risk" />
      </KpiChart>
      <KpiChart v-if="isAdmin" :value="unassigned.length" label="High risk, no owner" icon="person" :tone="unassigned.length ? 'high' : 'ok'" :sub="`of ${high.length} High-risk students`" :to="{ path: '/staff/students', query: { owner: 'none' } }">
        <Ring :value="unassigned.length" :max="high.length" :color="unassigned.length ? VIZ.critical : VIZ.good" label="High-risk students without an owner" />
      </KpiChart>
      <KpiChart v-else :value="mine.length" label="My open cases" icon="person" :tone="mine.length / myCapacity > 0.9 ? 'high' : mine.length / myCapacity > 0.75 ? 'low' : 'ok'" :sub="`${mine.filter((r) => r.risk.level === 'high').length} High, ${mine.filter((r) => r.risk.level === 'low').length} Low, of ${myCapacity} places`" :to="{ path: '/staff/students', query: { owner: 'me' } }">
        <Ring :value="mine.length" :max="myCapacity" :color="loadColor(mine.length, myCapacity)" label="My cases against my capacity" />
      </KpiChart>
      <KpiChart :value="dueNow.length" label="Follow-ups due" icon="clock" :tone="overdue.length ? 'high' : dueNow.length ? 'low' : 'ok'" :sub="`${overdue.length} of them overdue`" to="/staff/interventions">
        <Ring :value="overdue.length" :max="dueNow.length" :color="VIZ.critical" label="Follow-ups that are overdue" />
      </KpiChart>
      <KpiChart :value="predictedFail.length" label="Predicted to fail" icon="spark" tone="pred" sub="of all students, model estimate" :to="{ path: '/staff/students', query: { risk: 'pred' } }">
        <Ring :value="predictedFail.length" :max="staff.rows.length" :color="C.pred" label="Share of students predicted to fail" />
      </KpiChart>
    </div>

    <div class="charts">
      <section class="panel" aria-labelledby="mix-h">
        <div class="panel-head">
          <h2 id="mix-h">Risk mix</h2>
          <span class="muted small">All {{ staff.rows.length }} students</span>
        </div>
        <Donut :parts="riskParts" :center="`${atRiskPct}%`" center-sub="at risk" />
        <div class="by-level">
          <h3>By level</h3>
          <ul class="pies">
            <li v-for="lv in byLevel" :key="lv.key">
              <Donut :parts="riskSlices(lv)" :center="`${Math.round(((lv.high + lv.low) / lv.n) * 100)}%`" center-sub="at risk" :size="96" :thickness="22" :legend="false" />
              <strong>{{ lv.label }}</strong>
              <span class="muted num">{{ lv.high }} High, {{ lv.low }} Low of {{ lv.n }}</span>
            </li>
          </ul>
        </div>
      </section>

      <section class="panel status-card" aria-labelledby="st-h">
        <div class="panel-head">
          <h2 id="st-h">{{ isAdmin ? 'Where cases stand' : 'Where my cases stand' }}</h2>
          <span class="muted small">{{ caseRows.length }} at risk</span>
        </div>
        <Donut :parts="caseParts" :center="needAction" center-sub="need action" :size="150" :thickness="24" :legend="false" class="status-pie" />
        <ul class="status-legend">
          <li v-for="p in caseParts" :key="p.key">
            <i :class="{ hatch: p.hatch }" :style="{ background: p.color }"></i>
            <span>{{ p.label }}</span>
            <strong class="num">{{ p.value }}</strong>
          </li>
        </ul>
        <p class="note">Latest outcome logged for each case. Red slices need action; striped red is escalated.</p>
      </section>

      <section class="panel gauge-card" aria-labelledby="g-h">
        <div class="panel-head">
          <h2 id="g-h">{{ isAdmin ? 'Team capacity used' : 'My caseload' }}</h2>
        </div>
        <Ring class="cap-ring" :value="load.cases" :max="load.capacity" :color="loadColor(load.cases, load.capacity)" :size="164" :thickness="12" :sub="`${load.cases} of ${load.capacity}`" :label="isAdmin ? 'Cases against the support team capacity' : 'My cases against my capacity'" />
        <p class="cap-state" :class="load.cases / load.capacity > 0.9 ? 'high' : load.cases / load.capacity > 0.75 ? 'low' : 'ok'">{{ load.cases / load.capacity > 0.9 ? 'At capacity' : load.cases / load.capacity > 0.75 ? 'Getting tight' : 'Room to take more' }}</p>
        <dl class="g-stats">
          <div><dt>High risk</dt><dd class="num">{{ load.high }}</dd></div>
          <div><dt>Low risk</dt><dd class="num">{{ load.low }}</dd></div>
          <div><dt>Places left</dt><dd class="num">{{ load.capacity - load.cases }}</dd></div>
        </dl>
        <p class="g-note">{{ isAdmin ? `Open cases across ${staff.caseload.length} support staff, against their combined capacity.` : 'Your open cases against the number you can take.' }}</p>
      </section>
    </div>

    <div class="row two-a">
      <section class="panel" aria-labelledby="t-h">
        <div class="panel-head">
          <h2 id="t-h">At-risk students this term</h2>
          <span class="muted small">By week</span>
        </div>
        <TrendChart :labels="trend.labels" :series="trend.series" :height="262" />
        <p class="note">Weeks 1 to 6 are sample history. Week 7 is today’s count.</p>
      </section>

      <section class="panel" aria-labelledby="c-h">
        <div class="panel-head">
          <h2 id="c-h">Courses with the most risk flags</h2>
        </div>
        <ul class="course-pies">
          <li v-for="c in byCourse" :key="c.course.id">
            <Donut :parts="coursePie(c)" :center="c.high + c.low + c.pred" center-sub="flags" :size="96" :thickness="22" :legend="false" />
            <span class="cp-name">{{ c.course.name }}</span>
            <span class="muted num small">{{ c.high }} High · {{ c.low }} Low · {{ c.pred }} predicted</span>
          </li>
        </ul>
        <p class="legend">
          <span><i class="sw high"></i>High risk</span>
          <span><i class="sw low"></i>Low risk</span>
          <span><i class="sw pred"></i>Predicted to fail (model)</span>
        </p>
      </section>
    </div>

    <div class="row two-a">
      <section class="panel" aria-labelledby="f-h">
        <div class="panel-head">
          <h2 id="f-h">Follow-ups, oldest first</h2>
          <RouterLink to="/staff/interventions">All interventions</RouterLink>
        </div>
        <ul v-if="follow.length" class="follow">
          <li v-for="f in follow.slice(0, 6)" :key="f.id">
            <RouterLink :to="`/staff/students/${f.studentId}`" class="f-row">
              <span class="f-ic" :class="{ late: f.overdue, due: f.due && !f.overdue }"><Icon :name="INTERVENTION_TYPES[f.type].icon" :size="16" /></span>
              <span class="f-main">
                <strong>{{ staff.row(f.studentId).name }}</strong>
                <span class="muted">{{ COURSES[f.courseId]?.name }} · {{ STAFF[staff.meta[f.studentId].owner]?.name || 'No owner' }}</span>
              </span>
              <span class="chip" :class="f.overdue ? 'high' : f.due ? 'low' : ''">{{ f.overdue ? `Overdue, ${formatDate(f.followUp, { weekday: undefined })}` : relativeDay(f.followUp) }}</span>
            </RouterLink>
          </li>
        </ul>
        <p v-else class="muted">Nothing due. Well done.</p>
      </section>

      <div class="side-stack">
        <section v-if="isAdmin" class="panel" aria-labelledby="l-h">
          <div class="panel-head">
            <h2 id="l-h">Caseload by staff member</h2>
          </div>
          <ul class="load">
            <li v-for="m in staff.caseload" :key="m.id">
              <Person :name="m.name" :sub="m.title" :size="32" />
              <div class="l-bar">
                <StackBar
                  :parts="[
                    { value: m.cases.filter((r) => r.risk.level === 'high').length, cls: 'high', label: 'High' },
                    { value: m.cases.filter((r) => r.risk.level === 'low').length, cls: 'low', label: 'Low' },
                  ]"
                  :max="m.capacity"
                  :height="12"
                />
                <span class="num small">{{ m.cases.length }} of {{ m.capacity }}</span>
              </div>
            </li>
          </ul>
          <p class="note">Bar length is cases against each person’s capacity.</p>
        </section>

        <section v-else class="panel" aria-labelledby="m-h">
          <div class="panel-head">
            <h2 id="m-h">My cases</h2>
            <RouterLink :to="{ path: '/staff/students', query: { owner: 'me' } }">Open list</RouterLink>
          </div>
          <ul class="mine">
            <li v-for="r in mine.slice(0, 6)" :key="r.id">
              <RouterLink :to="`/staff/students/${r.id}`">
                <Person :name="r.name" :sub="r.main?.text" :size="32" :tone="r.risk.level" />
              </RouterLink>
            </li>
          </ul>
        </section>

        <section v-if="isAdmin" class="panel" aria-labelledby="s-h">
          <div class="panel-head">
            <h2 id="s-h">Data and system</h2>
            <RouterLink to="/staff/data">Open</RouterLink>
          </div>
          <ul class="sys">
            <li><span class="dot ok"></span>Last import: {{ lastImport.category }}, {{ relativeDay(lastImport.at).toLowerCase() }}</li>
            <li><span class="dot ok"></span>Risk recalculated {{ relativeDay(staff.lastRecalc).toLowerCase() }} (rules v{{ staff.rules.version }})</li>
            <li v-for="j in failedJobs" :key="j.id"><span class="dot high"></span>{{ j.name }}: failed</li>
            <li><span class="dot" :class="staff.llmEnabled ? 'ok' : 'low'"></span>Language model for student messages: {{ staff.llmEnabled ? 'on' : 'off' }}</li>
          </ul>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wide {
  max-width: 1240px;
}

.head-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 28px;
  align-items: start;
  margin-bottom: 22px;
}

.where {
  color: var(--muted);
  font-weight: 500;
  margin-bottom: 4px;
}

.summary {
  margin-top: 10px;
  font-size: 1.125rem;
  color: var(--ink-2);
  max-width: 62ch;
}

.summary strong {
  color: var(--high);
  font-weight: 600;
}

.fresh {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  font-size: 0.875rem;
  color: var(--muted);
}

.alert {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  padding: 16px 20px;
  border-radius: var(--r-m);
  background: var(--high-soft);
  border: 1px solid var(--high-mid);
  margin-bottom: 20px;
}

.bell {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--high);
  color: #fff;
}

.alert h2 {
  font-size: 1.0625rem;
  color: var(--high);
}

.names {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.name-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  padding: 5px 12px;
  border-radius: 12px;
  background: var(--surface);
  color: var(--ink);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9375rem;
}

.name-chip .muted::before {
  content: '· ';
}

.name-chip .muted {
  font-weight: 400;
}

.name-chip:hover {
  box-shadow: 0 0 0 1px var(--high);
}

.kpis {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.charts {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr) minmax(0, 0.85fr);
  gap: 20px;
  margin-bottom: 24px;
  align-items: stretch;
}

.row {
  display: grid;
  gap: 20px;
  margin-bottom: 24px;
  align-items: stretch;
}

.two-a {
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
}

.side-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.charts .panel,
.row .panel {
  padding: 22px 24px;
}

.status-pie {
  align-self: center;
  margin: 4px 0 14px;
}

.status-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-legend li {
  display: grid;
  grid-template-columns: 12px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  font-size: 0.9375rem;
}

.status-legend i {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.status-legend i.hatch {
  background-image: repeating-linear-gradient(135deg, transparent 0 2px, rgba(255, 255, 255, 0.55) 2px 4px) !important;
}

.status-legend strong {
  font-weight: 600;
}

.cap-ring {
  align-self: center;
}

.cap-state {
  text-align: center;
  font-weight: 600;
  margin-top: 8px;
}

.cap-state.high { color: var(--high); }
.cap-state.low { color: var(--low); }
.cap-state.ok { color: var(--ok); }

.gauge-card,
.status-card {
  display: flex;
  flex-direction: column;
}

.status-card .note {
  margin-top: auto;
  padding-top: 14px;
}

.gauge-card .panel-head {
  margin-bottom: 18px;
}

.g-stats {
  margin: 18px 0 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  text-align: center;
}

.g-stats div {
  padding: 10px 6px;
  border-radius: var(--r-s);
  background: var(--paper);
}

.g-stats dt {
  font-size: 0.75rem;
  color: var(--muted);
}

.g-stats dd {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.by-level {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--line);
}

.by-level h3 {
  font-size: 0.9375rem;
  margin-bottom: 10px;
}

.pies,
.course-pies {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 16px 12px;
}

.course-pies {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.pies li,
.course-pies li {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 2px;
  font-size: 0.875rem;
  line-height: 1.3;
}

.pies li > :first-child,
.course-pies li > :first-child {
  margin-bottom: 6px;
}

.cp-name {
  font-weight: 600;
}

.g-note {
  margin-top: auto;
  padding-top: 14px;
  font-size: 0.875rem;
  color: var(--ink-2);
  text-align: center;
}

.g-note a {
  font-weight: 600;
}

.small {
  font-size: 0.875rem;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  margin-top: 14px;
  font-size: 0.8125rem;
  color: var(--muted);
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.sw {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  display: inline-block;
}

.sw.high { background: var(--viz-critical); }
.sw.low { background: var(--viz-warning); }
.sw.pred { background: var(--viz-pred); }

.follow,
.mine,
.sys,
.load {
  list-style: none;
  margin: 0;
  padding: 0;
}

.follow li + li,
.mine li + li {
  border-top: 1px solid var(--line);
}

.f-row {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 10px 0;
  color: inherit;
  text-decoration: none;
}

.f-row:hover strong {
  color: var(--route-ink);
}

.f-ic {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--paper);
  color: var(--ink-2);
}

.f-ic.late { background: var(--high-soft); color: var(--high); }
.f-ic.due { background: var(--low-soft); color: var(--low); }

.f-main {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  min-width: 0;
}

.f-main strong {
  font-weight: 600;
}

.f-main .muted {
  font-size: 0.8125rem;
}

.load {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.load li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.l-bar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}

.mine a {
  display: block;
  padding: 8px 0;
  color: inherit;
  text-decoration: none;
}

.sys {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 0.9375rem;
}

.sys li {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex: none;
  background: var(--muted);
}

.dot.ok { background: var(--ok); }
.dot.high { background: var(--high); }
.dot.low { background: var(--low-fill); }

@media (max-width: 1240px) {
  .kpis {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .charts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .charts > :first-child {
    grid-column: 1 / -1;
  }
}

@media (max-width: 1100px) {
  .head-row {
    grid-template-columns: 1fr;
    gap: 18px;
  }
}

@media (max-width: 980px) {
  .charts,
  .two-a {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .kpis > :last-child:nth-child(odd) {
    grid-column: 1 / -1;
  }
  .alert {
    grid-template-columns: minmax(0, 1fr);
    padding: 14px 16px;
  }
  .bell {
    display: none;
  }
  .name-chip .muted::before {
    content: none;
  }
  .name-chip {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
    width: 100%;
  }
  .alert .btn {
    grid-column: 1 / -1;
    justify-self: start;
  }
  .load li {
    grid-template-columns: 1fr;
    gap: 6px;
  }
}

@media (max-width: 480px) {
  .kpis {
    grid-template-columns: 1fr;
  }
}
</style>
