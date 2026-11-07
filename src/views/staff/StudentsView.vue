<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useStaffStore } from '../../stores/staff'
import { STAFF, SUPPORT_STAFF } from '../../data/staff'
import { OUTCOMES } from '../../data/actions'
import { relativeDay } from '../../utils/dates'
import Icon from '../../components/Icon.vue'
import RiskChip from '../../components/staff/RiskChip.vue'
import Person from '../../components/staff/Person.vue'

const auth = useAuthStore()
const staff = useStaffStore()
const route = useRoute()
const router = useRouter()
const isAdmin = computed(() => auth.role === 'admin')

const f = reactive({
  q: '',
  risk: String(route.query.risk || 'risk'),
  level: 'all',
  term: 'all',
  owner: String(route.query.owner || (auth.role === 'support' ? 'me' : 'all')),
})
watch(() => route.query, (q) => {
  if (q.risk) f.risk = String(q.risk)
  if (q.owner) f.owner = String(q.owner)
})

const RISK_FILTERS = [
  { key: 'risk', label: 'High and Low' },
  { key: 'high', label: 'High risk' },
  { key: 'low', label: 'Low risk' },
  { key: 'pred', label: 'Predicted to fail (model)' },
  { key: 'data', label: 'Data to check' },
  { key: 'all', label: 'All students' },
]

const ORDER = { high: 0, low: 1, none: 2 }
const list = computed(() => {
  const q = f.q.trim().toLowerCase()
  return staff.rows
    .filter((r) => {
      if (f.risk === 'risk' && r.risk.level === 'none') return false
      if (f.risk === 'high' && r.risk.level !== 'high') return false
      if (f.risk === 'low' && r.risk.level !== 'low') return false
      if (f.risk === 'pred' && !r.predictedFail) return false
      if (f.risk === 'data' && !r.meta.dataIssue) return false
      if (f.level !== 'all' && r.level !== f.level) return false
      if (f.term !== 'all' && r.term !== Number(f.term)) return false
      if (f.owner === 'me' && r.owner !== auth.user.staffId) return false
      if (f.owner === 'none' && r.owner) return false
      if (!['all', 'me', 'none'].includes(f.owner) && r.owner !== f.owner) return false
      if (q && !r.name.toLowerCase().includes(q) && !r.rollNo.includes(q)) return false
      return true
    })
    .sort((a, b) =>
      ORDER[a.risk.level] - ORDER[b.risk.level] ||
      Number(b.isNew) - Number(a.isNew) ||
      (a.worst?.prediction.score ?? 101) - (b.worst?.prediction.score ?? 101),
    )
})
const counts = computed(() => ({
  high: list.value.filter((r) => r.risk.level === 'high').length,
  low: list.value.filter((r) => r.risk.level === 'low').length,
}))

function reset() {
  Object.assign(f, { q: '', risk: 'risk', level: 'all', term: 'all', owner: 'all' })
  router.replace({ query: {} })
}

// Assigning (administrators, US-07)
const selected = ref([])
const allOn = computed(() => list.value.length > 0 && list.value.every((r) => selected.value.includes(r.id)))
function toggleAll() {
  selected.value = allOn.value ? [] : list.value.map((r) => r.id)
}
const a = reactive({ owner: '', reason: 'New High-risk case', error: '' })
const done = ref('')
function assign() {
  a.error = ''
  if (!a.owner) return (a.error = 'Choose a staff member.')
  if (a.reason.trim().length < 4) return (a.error = 'Give a short reason; it is saved in the audit log.')
  staff.assign(selected.value, a.owner, a.reason.trim())
  done.value = `${selected.value.length} ${selected.value.length === 1 ? 'student' : 'students'} assigned to ${STAFF[a.owner].name}.`
  selected.value = []
  setTimeout(() => (done.value = ''), 4000)
}
const loadOf = (id) => staff.caseload.find((m) => m.id === id)
</script>

<template>
  <div class="page wide">
    <header class="page-head">
      <h1>At-risk students</h1>
      <p>Most urgent first: High risk, then new cases, then the lowest predicted score.</p>
    </header>

    <div class="filters" role="search">
      <label class="search">
        <Icon name="search" :size="18" />
        <span class="sr-only">Search by name or roll number</span>
        <input v-model="f.q" type="search" placeholder="Search name or roll number" />
      </label>
      <label><span>Risk</span>
        <select v-model="f.risk"><option v-for="o in RISK_FILTERS" :key="o.key" :value="o.key">{{ o.label }}</option></select>
      </label>
      <label><span>Level</span>
        <select v-model="f.level"><option value="all">All levels</option><option value="foundation">Foundation</option><option value="diploma">Diploma</option></select>
      </label>
      <label><span>Term</span>
        <select v-model="f.term"><option value="all">Any term</option><option v-for="n in 4" :key="n" :value="String(n)">Term {{ n }}</option></select>
      </label>
      <label><span>Owner</span>
        <select v-model="f.owner">
          <option value="all">Anyone</option>
          <option v-if="auth.user.staffId && auth.role === 'support'" value="me">Me</option>
          <option value="none">No owner</option>
          <option v-for="m in SUPPORT_STAFF" :key="m.id" :value="m.id">{{ m.name }}</option>
        </select>
      </label>
    </div>

    <div class="count-row">
      <p class="count"><strong class="num">{{ list.length }}</strong> {{ list.length === 1 ? 'student' : 'students' }} <span class="chip high">{{ counts.high }} High</span> <span class="chip low">{{ counts.low }} Low</span></p>
      <button type="button" class="link" @click="reset">Clear filters</button>
    </div>

    <div v-if="isAdmin && selected.length" class="assign" role="region" aria-label="Assign selected students">
      <strong>{{ selected.length }} selected</strong>
      <label><span class="sr-only">Assign to</span>
        <select v-model="a.owner">
          <option value="" disabled>Assign to…</option>
          <option v-for="m in SUPPORT_STAFF" :key="m.id" :value="m.id">{{ m.name }} ({{ loadOf(m.id).cases.length }} of {{ m.capacity }} cases)</option>
        </select>
      </label>
      <label class="grow"><span class="sr-only">Reason</span><input v-model="a.reason" type="text" placeholder="Reason (saved in the audit log)" /></label>
      <button class="btn" type="button" @click="assign"><Icon name="person" :size="18" /> Assign</button>
      <button class="btn quiet" type="button" @click="selected = []">Cancel</button>
      <p v-if="a.error" class="err" role="alert">{{ a.error }}</p>
    </div>
    <p v-if="done" class="toast" role="status"><Icon name="check" :size="18" /> {{ done }}</p>

    <div class="table" role="table" aria-label="Students">
      <div class="tr th" role="row">
        <span v-if="isAdmin" role="columnheader" class="c-sel"><input type="checkbox" :checked="allOn" aria-label="Select all shown" @change="toggleAll" /></span>
        <span role="columnheader">Student</span>
        <span role="columnheader">Risk</span>
        <span role="columnheader">Main reason</span>
        <span role="columnheader">Predicted (model)</span>
        <span role="columnheader">Owner</span>
        <span role="columnheader">Case</span>
      </div>
      <div v-for="r in list" :key="r.id" class="tr" :class="{ sel: selected.includes(r.id) }" role="row">
        <span v-if="isAdmin" class="c-sel" role="cell"><input v-model="selected" type="checkbox" :value="r.id" :aria-label="`Select ${r.name}`" /></span>
        <span role="cell" class="c-name">
          <RouterLink :to="`/staff/students/${r.id}`"><Person :name="r.name" :sub="`${r.rollNo} · ${r.levelLabel}, term ${r.term}`" :tone="r.risk.level === 'none' ? 'ok' : r.risk.level" /></RouterLink>
        </span>
        <span role="cell" class="c-risk"><RiskChip :level="r.risk.level" :is-new="r.isNew" /><span v-if="r.meta.dataIssue" class="chip">Check data</span></span>
        <span role="cell" class="c-reason">
          <template v-if="r.main">{{ r.main.text }}<span v-if="r.reasons.length > 1" class="more"> +{{ r.reasons.length - 1 }} more</span></template>
          <span v-else class="muted">No risk reasons</span>
        </span>
        <span role="cell" class="c-pred">
          <template v-if="r.worst">
            <span class="pbar" aria-hidden="true"><span class="fill" :class="{ fail: Math.round(r.worst.prediction.score) < 40 }" :style="{ width: `${r.worst.prediction.score}%` }"></span><span class="pass"></span></span>
            <span class="num pv" :class="{ fail: Math.round(r.worst.prediction.score) < 40 }">{{ Math.round(r.worst.prediction.score) }} {{ r.worst.prediction.grade }}</span>
            <span class="pc">{{ r.worst.course.name }}</span>
          </template>
          <span v-else class="muted">No course in progress</span>
        </span>
        <span role="cell" class="c-owner">
          <template v-if="r.owner">{{ STAFF[r.owner].name }}</template>
          <span v-else-if="r.risk.level === 'high'" class="chip high">No owner</span>
          <span v-else class="muted">{{ r.risk.level === 'low' ? 'Study plan only' : '–' }}</span>
        </span>
        <span role="cell" class="c-case">
          <span v-if="staff.statusOf(r.id)" class="chip" :class="OUTCOMES[staff.statusOf(r.id)].cls">{{ OUTCOMES[staff.statusOf(r.id)].label }}</span>
          <span class="upd">Updated {{ relativeDay(r.student.updatedAt).toLowerCase() }}</span>
        </span>
      </div>
      <p v-if="!list.length" class="empty">No students match these filters.</p>
    </div>
  </div>
</template>

<style scoped>
.wide {
  max-width: 1240px;
}

.filters {
  display: grid;
  grid-template-columns: minmax(200px, 1.4fr) repeat(4, minmax(0, 1fr));
  gap: 10px;
  align-items: end;
}

.filters label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.8125rem;
  color: var(--muted);
  font-weight: 500;
  min-width: 0;
}

.filters select,
.search input,
.assign select,
.assign input {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--line-2);
  border-radius: 10px;
  background: var(--surface);
  font-size: 0.9375rem;
  color: var(--ink);
}

.search {
  position: relative;
}

.search svg {
  position: absolute;
  left: 12px;
  bottom: 11px;
  color: var(--muted);
}

.search input {
  padding-left: 38px;
}

.count-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin: 16px 0 10px;
}

.count {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.link {
  border: 0;
  background: none;
  color: var(--route-ink);
  font-weight: 500;
  cursor: pointer;
  padding: 4px;
}

.assign {
  position: sticky;
  top: 8px;
  z-index: 3;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
  border-radius: var(--r-m);
  background: var(--ink);
  color: #fff;
  box-shadow: 0 8px 24px rgba(20, 26, 50, 0.18);
}

.assign label {
  min-width: 220px;
}

.assign .grow {
  flex: 1 1 220px;
}

.assign .btn.quiet {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
}

.assign .btn.quiet:hover {
  background: rgba(255, 255, 255, 0.1);
}

.err {
  flex-basis: 100%;
  color: #ffb4ab;
  font-size: 0.875rem;
}

.toast {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
  border-radius: var(--r-m);
  background: var(--ok-soft);
  color: var(--ok);
  font-weight: 500;
}

.table {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-m);
  overflow: hidden;
}

.tr {
  display: grid;
  grid-template-columns: 34px minmax(250px, 1.5fr) 120px minmax(0, 1.5fr) minmax(0, 1.2fr) minmax(0, 0.9fr) minmax(0, 0.9fr);
  gap: 14px;
  align-items: center;
  padding: 12px 18px;
}

.table:not(:has(.c-sel)) .tr {
  grid-template-columns: minmax(250px, 1.5fr) 120px minmax(0, 1.5fr) minmax(0, 1.2fr) minmax(0, 0.9fr) minmax(0, 0.9fr);
}

.tr + .tr {
  border-top: 1px solid var(--line);
}

.th {
  background: var(--paper);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--muted);
  padding-top: 10px;
  padding-bottom: 10px;
}

.tr.sel {
  background: var(--route-soft);
}

.c-sel input {
  width: 17px;
  height: 17px;
  accent-color: var(--route);
}

.c-name a {
  color: inherit;
  text-decoration: none;
  display: block;
}

.c-name a:hover :deep(strong) {
  color: var(--route-ink);
  text-decoration: underline;
}

.c-risk {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.c-reason {
  font-size: 0.9375rem;
  line-height: 1.35;
}

.more {
  color: var(--muted);
  font-size: 0.8125rem;
}

.c-pred {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 2px 8px;
  align-items: center;
}

.pbar {
  position: relative;
  height: 8px;
  border-radius: 999px;
  background: var(--line);
}

.fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  border-radius: inherit;
  background: var(--route);
}

.fill.fail {
  background: var(--high);
}

.pass {
  position: absolute;
  left: 40%;
  top: -3px;
  bottom: -3px;
  width: 2px;
  background: var(--ink-2);
}

.pv {
  font-weight: 600;
  font-size: 0.9375rem;
}

.pv.fail {
  color: var(--high);
}

.pc {
  grid-column: 1 / -1;
  font-size: 0.75rem;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.c-owner {
  font-size: 0.9375rem;
}

.c-case {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
}

.upd {
  font-size: 0.75rem;
  color: var(--muted);
}

.empty {
  padding: 28px;
  text-align: center;
  color: var(--muted);
}

@media (max-width: 1100px) {
  .filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .search {
    grid-column: 1 / -1;
  }
  .th {
    display: none;
  }
  .tr,
  .table:not(:has(.c-sel)) .tr {
    grid-template-columns: minmax(0, 1fr) auto;
    grid-template-areas:
      'name risk'
      'reason reason'
      'pred pred'
      'owner case';
    gap: 8px 12px;
    padding: 14px 16px;
  }
  .tr:has(.c-sel) {
    grid-template-columns: 26px minmax(0, 1fr) auto;
    grid-template-areas:
      'sel name risk'
      '. reason reason'
      '. pred pred'
      '. owner case';
  }
  .c-sel { grid-area: sel; }
  .c-name { grid-area: name; }
  .c-risk { grid-area: risk; justify-content: flex-end; }
  .c-reason { grid-area: reason; }
  .c-pred { grid-area: pred; }
  .c-owner { grid-area: owner; }
  .c-case { grid-area: case; align-items: flex-end; }
}
</style>
