<script setup>
import { computed, ref } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useStaffStore } from '../../stores/staff'
import { STAFF } from '../../data/staff'
import { COURSES } from '../../data/courses'
import { INTERVENTION_TYPES, OUTCOMES } from '../../data/actions'
import { formatDate, relativeDay } from '../../utils/dates'
import Icon from '../../components/Icon.vue'
import RiskChip from '../../components/staff/RiskChip.vue'

const auth = useAuthStore()
const staff = useStaffStore()
const scope = ref(auth.role === 'support' ? 'mine' : 'all')
const type = ref('all')

const inScope = (studentId) => scope.value === 'all' || staff.meta[studentId].owner === auth.user.staffId

const cases = computed(() =>
  staff.atRisk
    .filter((r) => (r.owner || staff.historyOf(r.id).length || r.risk.level === 'high') && inScope(r.id))
    .map((r) => {
      const last = staff.historyOf(r.id)[0] || null
      return { r, last, status: staff.statusOf(r.id) }
    })
    .filter((c) => type.value === 'all' || c.last?.type === type.value),
)

const COLUMNS = ['not_contacted', 'in_progress', 'no_response', 'escalated', 'resolved']
const columns = computed(() => COLUMNS.map((key) => ({ key, ...OUTCOMES[key], items: cases.value.filter((c) => c.status === key) })))
const followUps = computed(() => staff.followUps.filter((f) => f.due && inScope(f.studentId)))

const moved = ref('')
function move(c, outcome) {
  if (!outcome || outcome === c.status) return
  staff.setOutcome(c.r.id, outcome)
  moved.value = `${c.r.name} moved to “${OUTCOMES[outcome].label}”. Logged in the audit log.`
  setTimeout(() => (moved.value = ''), 3500)
}
</script>

<template>
  <div class="page wide">
    <header class="page-head">
      <h1>Interventions</h1>
      <p>Every open case and where it stands. Change a case’s outcome from its card; each change is logged.</p>
    </header>

    <div class="bar">
      <div class="seg" role="group" aria-label="Whose cases">
        <button type="button" :class="{ on: scope === 'mine' }" :aria-pressed="scope === 'mine'" :disabled="!auth.user.staffId || auth.role === 'admin'" @click="scope = 'mine'">My cases</button>
        <button type="button" :class="{ on: scope === 'all' }" :aria-pressed="scope === 'all'" @click="scope = 'all'">Everyone’s</button>
      </div>
      <label class="type">
        <span>Last action</span>
        <select v-model="type">
          <option value="all">Any type</option>
          <option v-for="(t, k) in INTERVENTION_TYPES" :key="k" :value="k">{{ t.label }}</option>
        </select>
      </label>
    </div>

    <section class="due" aria-labelledby="due-h">
      <h2 id="due-h"><Icon name="clock" :size="20" /> Follow-ups due now <span class="num count">{{ followUps.length }}</span></h2>
      <ul v-if="followUps.length" class="due-list">
        <li v-for="f in followUps" :key="f.id" :class="{ late: f.overdue }">
          <RouterLink :to="`/staff/students/${f.studentId}`">
            <strong>{{ staff.row(f.studentId).name }}</strong>
            <span>{{ COURSES[f.courseId]?.name }}</span>
            <span class="when">{{ f.overdue ? `Overdue since ${formatDate(f.followUp, { weekday: undefined })}` : 'Due today' }}</span>
          </RouterLink>
        </li>
      </ul>
      <p v-else class="muted">No follow-ups due. Nothing is overdue.</p>
    </section>

    <p v-if="moved" class="toast" role="status"><Icon name="check" :size="18" /> {{ moved }}</p>

    <div class="board">
      <section v-for="col in columns" :key="col.key" class="col" :class="col.key" :aria-labelledby="`col-${col.key}`">
        <header>
          <h2 :id="`col-${col.key}`"><span class="dot" :class="col.cls"></span>{{ col.label }}</h2>
          <span class="num n">{{ col.items.length }}</span>
        </header>
        <ul>
          <li v-for="c in col.items" :key="c.r.id" class="card">
            <div class="c-top">
              <RouterLink :to="`/staff/students/${c.r.id}`" class="nm">{{ c.r.name }}</RouterLink>
              <RiskChip :level="c.r.risk.level" :is-new="c.r.isNew" />
            </div>
            <p class="course">{{ c.r.risk.focus?.course.name }}</p>
            <p v-if="c.last" class="last">
              <Icon :name="INTERVENTION_TYPES[c.last.type].icon" :size="15" />
              {{ INTERVENTION_TYPES[c.last.type].label }} {{ relativeDay(c.last.at).toLowerCase() }}
            </p>
            <p v-else class="last none"><Icon name="alert" :size="15" /> No contact yet</p>
            <div class="c-foot">
              <span class="who">{{ c.r.owner ? STAFF[c.r.owner].name : 'No owner' }}</span>
              <span v-if="c.last?.followUp && c.status !== 'resolved'" class="chip" :class="c.last.followUp < new Date(new Date().setHours(0, 0, 0, 0)) ? 'high' : ''">{{ relativeDay(c.last.followUp) }}</span>
            </div>
            <label class="mv">
              <span class="sr-only">Move {{ c.r.name }} to</span>
              <select :value="c.status" @change="move(c, $event.target.value)">
                <option v-for="k in COLUMNS.filter((x) => x !== 'not_contacted')" :key="k" :value="k">{{ OUTCOMES[k].label }}</option>
                <option v-if="c.status === 'not_contacted'" value="not_contacted" disabled>Move to…</option>
              </select>
            </label>
          </li>
          <li v-if="!col.items.length" class="empty">None</li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style scoped>
.wide {
  max-width: 1320px;
}

.bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
  align-items: end;
  margin-bottom: 18px;
}

.seg {
  display: inline-flex;
  padding: 4px;
  border-radius: 12px;
  background: var(--surface);
  border: 1px solid var(--line);
}

.seg button {
  border: 0;
  background: none;
  padding: 7px 14px;
  border-radius: 9px;
  font-weight: 500;
  color: var(--ink-2);
  cursor: pointer;
}

.seg button.on {
  background: var(--ink);
  color: #fff;
}

.seg button:disabled {
  opacity: 0.45;
  cursor: default;
}

.type {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.8125rem;
  color: var(--muted);
  font-weight: 500;
}

.type select,
.mv select {
  padding: 8px 12px;
  border: 1px solid var(--line-2);
  border-radius: 10px;
  background: var(--surface);
  color: var(--ink);
  font-size: 0.9375rem;
}

.due {
  padding: 18px 20px;
  border-radius: var(--r-m);
  background: var(--surface);
  border: 1px solid var(--line);
  margin-bottom: 18px;
}

.due h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.0625rem;
  margin-bottom: 12px;
}

.count {
  font-size: 0.8125rem;
  padding: 1px 9px;
  border-radius: 999px;
  background: var(--high-soft);
  color: var(--high);
}

.due-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}

.due-list a {
  display: flex;
  flex-direction: column;
  padding: 10px 14px;
  border-radius: 12px;
  background: var(--low-soft);
  color: var(--ink);
  text-decoration: none;
  line-height: 1.35;
  border-left: 4px solid #e0952b;
}

.due-list .late a {
  background: var(--high-soft);
  border-left-color: var(--high);
}

.due-list strong {
  font-weight: 600;
}

.due-list span {
  font-size: 0.875rem;
  color: var(--ink-2);
}

.due-list .when {
  font-weight: 600;
  color: var(--low);
}

.due-list .late .when {
  color: var(--high);
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

.board {
  position: relative;
  display: grid;
  grid-template-columns: repeat(5, minmax(196px, 1fr));
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.col {
  background: #eceef3;
  border-radius: var(--r-m);
  padding: 12px;
  min-width: 0;
}

.col header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 0 4px;
}

.col h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9375rem;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--muted);
}

.dot.high { background: var(--high); }
.dot.route { background: var(--route); }
.dot.low { background: #e0952b; }
.dot.ok { background: var(--ok); }

.n {
  font-weight: 600;
  color: var(--muted);
}

.col ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card {
  background: var(--surface);
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 1px 2px rgba(20, 26, 50, 0.08);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.c-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 6px;
  flex-wrap: wrap;
}

.nm {
  font-weight: 600;
  color: var(--ink);
  text-decoration: none;
}

.nm:hover {
  color: var(--route-ink);
  text-decoration: underline;
}

.course {
  font-size: 0.875rem;
  color: var(--ink-2);
  line-height: 1.3;
}

.last {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  color: var(--muted);
}

.last.none {
  color: var(--high);
  font-weight: 500;
}

.c-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 0.8125rem;
}

.who {
  color: var(--ink-2);
  font-weight: 500;
}

.mv select {
  width: 100%;
  padding: 6px 10px;
  font-size: 0.875rem;
}

.empty {
  color: var(--muted);
  font-size: 0.875rem;
  text-align: center;
  padding: 10px;
}

@media (max-width: 860px) {
  .board {
    grid-template-columns: 1fr;
    overflow: visible;
  }
}
</style>
