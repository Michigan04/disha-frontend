<script setup>
import { computed, ref } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useStaffStore } from '../../stores/staff'
import { STAFF, staffEvents } from '../../data/staff'
import { COURSES } from '../../data/courses'
import { OUTCOMES } from '../../data/actions'
import { formatDate, greeting } from '../../utils/dates'
import Icon from '../../components/Icon.vue'
import Kpi from '../../components/staff/Kpi.vue'
import Person from '../../components/staff/Person.vue'
import TodayCard from '../../components/TodayCard.vue'
import InterventionForm from '../../components/staff/InterventionForm.vue'

// Course instructor or TA view (US-12): only students referred to this course,
// plus totals for the whole course.
const auth = useAuthStore()
const staff = useStaffStore()
const me = computed(() => STAFF[auth.user.staffId])
const course = computed(() => COURSES[me.value.courseId])

const referrals = computed(() => {
  const byStudent = {}
  for (const i of staff.interventions) {
    if (i.referralTo === me.value.id && (!byStudent[i.studentId] || i.at > byStudent[i.studentId].at)) byStudent[i.studentId] = i
  }
  return Object.values(byStudent)
    .sort((a, b) => b.at - a.at)
    .map((item) => {
      const support = staff.historyOf(item.studentId).filter((i) => i.by === me.value.id)
      return { ref: item, row: staff.row(item.studentId), support, status: staff.statusOf(item.studentId) }
    })
})

// Everyone taking the course this term (totals only)
const takers = computed(() => staff.rows.map((r) => r.current.find((c) => c.course.id === course.value.id)).filter(Boolean))
const avg = computed(() => Math.round(takers.value.reduce((s, c) => s + c.attempt.assignmentAvg, 0) / Math.max(1, takers.value.length)))
const eligiblePct = computed(() => Math.round((takers.value.filter((c) => c.attempt.assignmentAvg >= staff.rules.oppeMin).length / Math.max(1, takers.value.length)) * 100))
const bins = computed(() => {
  const edges = [0, 20, 40, 60, 80, 101]
  return edges.slice(0, -1).map((lo, i) => ({
    label: i === 4 ? '80–100' : `${lo}–${edges[i + 1] - 1}`,
    below: lo < staff.rules.oppeMin,
    n: takers.value.filter((c) => c.attempt.assignmentAvg >= lo && c.attempt.assignmentAvg < edges[i + 1]).length,
  }))
})
const binMax = computed(() => Math.max(1, ...bins.value.map((b) => b.n)))

const LAST_TERM = [
  { label: 'Weekly assignments (40 or more)', pct: 82 },
  { label: 'Quiz 1 (40 or more)', pct: 71 },
  { label: 'OPPE 1 passed', pct: 58 },
  { label: 'OPPE 2 passed', pct: 64 },
  { label: 'End-term exam (40 or more)', pct: 73 },
]

const open = ref(null)
const saved = ref('')
function save(rec) {
  staff.logIntervention(rec)
  open.value = null
  saved.value = 'Support recorded. It is now in the student’s intervention history.'
  setTimeout(() => (saved.value = ''), 4000)
}
</script>

<template>
  <div class="page wide">
    <div class="head-row">
      <header>
        <p class="where">Course instructor · Sep 2026 term, week 7 of 12</p>
        <h1>{{ greeting() }}, {{ auth.user.name.replace('Prof. ', '').split(' ')[0] }}</h1>
        <p class="summary">{{ course.name }}: {{ referrals.length }} {{ referrals.length === 1 ? 'student has' : 'students have' }} been referred to you by support staff.</p>
        <p class="priv"><Icon name="lock" :size="15" /> You see referred students only, and totals for everyone else in the course.</p>
      </header>
      <TodayCard :events="staffEvents(me.id)" />
    </div>

    <div class="kpis">
      <Kpi :value="referrals.length" label="Referred to you" sub="By support staff" icon="refer" tone="low" />
      <Kpi :value="referrals.reduce((s, x) => s + x.support.length, 0)" label="Support recorded" sub="This term" icon="check" tone="ok" />
      <Kpi :value="`${eligiblePct}%`" label="Eligible for OPPE 1" :sub="`Assignment average ${staff.rules.oppeMin} or more`" icon="oppe" />
      <Kpi :value="avg" label="Average weekly assignment" :sub="`${takers.length} students this term`" icon="chart" />
    </div>

    <p v-if="saved" class="toast" role="status"><Icon name="check" :size="18" /> {{ saved }}</p>

    <section class="panel" aria-labelledby="ref-h">
      <div class="panel-head"><h2 id="ref-h">Referrals</h2></div>
      <ul class="refs">
        <li v-for="x in referrals" :key="x.ref.id">
          <div class="r-main">
            <Person :name="x.row.name" :sub="x.row.rollNo" :tone="x.row.risk.level" />
            <div class="r-why">
              <p>{{ x.ref.notes }}</p>
              <span class="muted">Referred by {{ STAFF[x.ref.by].name }} on {{ formatDate(x.ref.at) }}</span>
            </div>
            <div class="r-side">
              <span class="chip" :class="OUTCOMES[x.status].cls">{{ OUTCOMES[x.status].label }}</span>
              <span class="muted small">{{ x.support.length }} support {{ x.support.length === 1 ? 'session' : 'sessions' }} recorded</span>
              <button v-if="open !== x.ref.id" class="btn quiet" type="button" @click="open = x.ref.id"><Icon name="plus" :size="16" /> Record support</button>
            </div>
          </div>
          <div v-if="open === x.ref.id" class="r-form">
            <InterventionForm :row="x.row" mode="support" @save="save" @cancel="open = null" />
          </div>
        </li>
        <li v-if="!referrals.length" class="muted">No referrals yet.</li>
      </ul>
    </section>

    <div class="two">
      <section class="panel" aria-labelledby="hist-h">
        <div class="panel-head">
          <h2 id="hist-h">Weekly assignment average, this term</h2>
        </div>
        <div class="hist" role="img" :aria-label="bins.map((b) => `${b.label}: ${b.n} students`).join(', ')">
          <div v-for="b in bins" :key="b.label" class="hcol">
            <span class="hn num">{{ b.n }}</span>
            <span class="hb" :class="{ below: b.below }" :style="{ height: `${(b.n / binMax) * 120}px` }"></span>
            <span class="hl num">{{ b.label }}</span>
          </div>
        </div>
        <p class="note"><span class="sw"></span> Below {{ staff.rules.oppeMin }}: not eligible for the OPPE. Students in the course this term, no names shown.</p>
      </section>

      <section class="panel" aria-labelledby="comp-h">
        <div class="panel-head">
          <h2 id="comp-h">Last term by component</h2>
          <span class="muted small">May 2026, sample</span>
        </div>
        <ul class="comp">
          <li v-for="c in LAST_TERM" :key="c.label">
            <div class="ct"><span>{{ c.label }}</span><strong class="num">{{ c.pct }}%</strong></div>
            <div class="cb"><span :class="{ weak: c.pct < 65 }" :style="{ width: `${c.pct}%` }"></span></div>
          </li>
        </ul>
        <p class="note">The OPPEs had the lowest pass rates, so OPPE-style practice helps most.</p>
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
}

.priv {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--line);
  font-size: 0.875rem;
  color: var(--ink-2);
}

.kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.toast {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 14px;
  border-radius: var(--r-m);
  background: var(--ok-soft);
  color: var(--ok);
  font-weight: 500;
}

.refs {
  list-style: none;
  margin: 0;
  padding: 0;
}

.refs > li + li {
  border-top: 1px solid var(--line);
}

.r-main {
  display: grid;
  grid-template-columns: minmax(180px, 0.8fr) minmax(0, 1.6fr) auto;
  gap: 16px;
  align-items: center;
  padding: 14px 0;
}

.r-why p {
  font-size: 0.9375rem;
}

.r-why .muted {
  font-size: 0.8125rem;
}

.r-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.small {
  font-size: 0.8125rem;
}

.r-form {
  padding: 16px;
  margin-bottom: 14px;
  border-radius: var(--r-m);
  background: var(--paper);
}

.two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.hist {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  align-items: end;
  height: 180px;
  padding-top: 10px;
}

.hcol {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  height: 100%;
}

.hb {
  width: 100%;
  max-width: 64px;
  border-radius: 6px 6px 0 0;
  background: var(--route);
  min-height: 2px;
}

.hb.below {
  background: var(--high);
}

.hn {
  font-weight: 600;
  font-size: 0.9375rem;
}

.hl {
  font-size: 0.75rem;
  color: var(--muted);
}

.sw {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  background: var(--high);
  margin-right: 4px;
}

.comp {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ct {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 0.9375rem;
  margin-bottom: 4px;
}

.ct strong {
  font-weight: 600;
}

.cb {
  height: 10px;
  border-radius: 999px;
  background: var(--line);
  overflow: hidden;
}

.cb span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--route);
}

.cb span.weak {
  background: var(--low-fill);
}

@media (max-width: 1100px) {
  .head-row {
    grid-template-columns: 1fr;
  }
  .kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .r-main {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  .r-side {
    align-items: flex-start;
  }
  .two {
    grid-template-columns: 1fr;
  }
}
</style>
