<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useStaffStore } from '../../stores/staff'
import { STAFF, staffEvents } from '../../data/staff'
import { COURSES } from '../../data/courses'
import { INTERVENTION_TYPES } from '../../data/actions'
import { formatDate, greeting, relativeDay } from '../../utils/dates'
import TodayCard from '../../components/TodayCard.vue'
import Icon from '../../components/Icon.vue'
import Kpi from '../../components/staff/Kpi.vue'
import StackBar from '../../components/staff/StackBar.vue'
import TrendChart from '../../components/staff/TrendChart.vue'
import Person from '../../components/staff/Person.vue'

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
const courseMax = computed(() => Math.max(...byCourse.value.map((c) => c.high + c.low + c.pred)))

// Weekly counts this term (sample history ending at today's numbers)
const trend = computed(() => {
  const h = high.value.length
  const l = low.value.length
  return {
    labels: ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7'],
    series: [
      { name: 'Low', color: '#c27610', values: [l + 4, l + 4, l + 3, l + 2, l + 2, l + 1, l] },
      { name: 'High', color: '#b42318', values: [h - 3, h - 3, h - 2, h - 2, h - 2, h - 2, h] },
    ],
  }
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
      <Kpi :value="staff.rows.length" label="Students tracked" sub="Demo cohort, Sep 2026" icon="users" />
      <Kpi :value="high.length" label="High risk" :sub="`${newHigh.length} new this week`" icon="alert" tone="high" :to="{ path: '/staff/students', query: { risk: 'high' } }" />
      <Kpi :value="low.length" label="Low risk" sub="Following a study plan" icon="flag" tone="low" :to="{ path: '/staff/students', query: { risk: 'low' } }" />
      <Kpi v-if="isAdmin" :value="unassigned.length" label="High risk, no owner" sub="Every case needs an owner" icon="person" :tone="unassigned.length ? 'high' : 'ok'" :to="{ path: '/staff/students', query: { owner: 'none' } }" />
      <Kpi v-else :value="mine.length" label="My open cases" :sub="`${mine.filter((r) => r.risk.level === 'high').length} High, ${mine.filter((r) => r.risk.level === 'low').length} Low`" icon="person" :to="{ path: '/staff/students', query: { owner: 'me' } }" />
      <Kpi :value="dueNow.length" label="Follow-ups due" :sub="`${overdue.length} overdue`" icon="clock" :tone="overdue.length ? 'high' : ''" to="/staff/interventions" />
      <Kpi :value="predictedFail.length" label="Predicted to fail a course" sub="Model estimate, not a risk level" icon="spark" :to="{ path: '/staff/students', query: { risk: 'pred' } }" />
    </div>

    <div class="grid">
      <section class="panel a-courses" aria-labelledby="c-h">
        <div class="panel-head">
          <h2 id="c-h">Courses with the most risk flags</h2>
        </div>
        <ul class="courses">
          <li v-for="c in byCourse" :key="c.course.id">
            <div class="c-top">
              <span>{{ c.course.name }}</span>
              <span class="num muted">{{ c.high + c.low + c.pred }}</span>
            </div>
            <StackBar :parts="[{ value: c.high, cls: 'high', label: 'High risk' }, { value: c.low, cls: 'low', label: 'Low risk' }, { value: c.pred, cls: 'pred', label: 'Predicted to fail' }]" :max="courseMax" :height="14" />
          </li>
        </ul>
        <p class="legend">
          <span><i class="sw high"></i>High risk</span>
          <span><i class="sw low"></i>Low risk</span>
          <span><i class="sw pred"></i>Predicted to fail (model)</span>
        </p>
      </section>

      <section class="panel a-follow" aria-labelledby="f-h">
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

      <section class="panel a-trend" aria-labelledby="t-h">
        <div class="panel-head">
          <h2 id="t-h">At-risk students this term</h2>
          <span class="muted small">By week</span>
        </div>
        <TrendChart :labels="trend.labels" :series="trend.series" :height="190" />
        <p class="note">Weeks 1 to 6 are sample history. Week 7 is today’s count.</p>
      </section>

      <section v-if="isAdmin" class="panel a-load" aria-labelledby="l-h">
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

      <section v-else class="panel a-load" aria-labelledby="m-h">
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

      <section v-if="isAdmin" class="panel a-sys" aria-labelledby="s-h">
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
  border: 1px solid #f5c9c3;
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
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  grid-template-areas:
    'courses follow'
    'trend load'
    'trend sys';
  gap: 20px;
  align-items: start;
}

.a-courses { grid-area: courses; }
.a-follow { grid-area: follow; }
.a-trend { grid-area: trend; }
.a-load { grid-area: load; }
.a-sys { grid-area: sys; }

.small {
  font-size: 0.875rem;
}

.courses {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.c-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 0.9375rem;
  margin-bottom: 4px;
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

.sw.high { background: var(--high); }
.sw.low { background: #e0952b; }
.sw.pred { background: repeating-linear-gradient(135deg, #8c90ff 0 3px, #b9bbff 3px 6px); }

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
.dot.low { background: #e0952b; }

@media (max-width: 1240px) {
  .kpis {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1100px) {
  .head-row {
    grid-template-columns: 1fr;
    gap: 18px;
  }
}

@media (max-width: 980px) {
  .grid {
    grid-template-columns: 1fr;
    grid-template-areas: 'follow' 'courses' 'load' 'trend' 'sys';
  }
}

@media (max-width: 640px) {
  .kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
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
</style>
