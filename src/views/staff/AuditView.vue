<script setup>
import { computed, reactive } from 'vue'
import { useStaffStore } from '../../stores/staff'
import { formatDate, formatTime } from '../../utils/dates'
import Icon from '../../components/Icon.vue'

// Audit log (US-11): who did what and when. Read only.
const staff = useStaffStore()
const f = reactive({ q: '', action: 'all', who: 'all', from: '', to: '' })

const actions = computed(() => [...new Set(staff.audit.map((a) => a.action))].sort())
const people = computed(() => [...new Set(staff.audit.map((a) => a.who))].sort())
const TONE = { 'Rule change': 'ink', 'Data import': 'route', 'Risk recalculation': 'route', Assignment: 'ok', Intervention: 'ok', Outcome: 'low', Access: 'high', Setting: 'high', 'Suggestion shared': 'ok', 'AI review': 'low' }

const list = computed(() => {
  const q = f.q.trim().toLowerCase()
  const from = f.from ? new Date(`${f.from}T00:00:00`) : null
  const to = f.to ? new Date(`${f.to}T23:59:59`) : null
  return staff.audit.filter((a) => {
    if (f.action !== 'all' && a.action !== f.action) return false
    if (f.who !== 'all' && a.who !== f.who) return false
    if (from && a.at < from) return false
    if (to && a.at > to) return false
    if (q && !`${a.details} ${a.who}`.toLowerCase().includes(q)) return false
    return true
  })
})
</script>

<template>
  <div class="page wide">
    <header class="page-head">
      <h1>Audit log</h1>
      <p>Every risk change, rule change, assignment, import and intervention, with who did it and when.</p>
    </header>

    <p class="lock"><Icon name="lock" :size="16" /> Entries cannot be edited or deleted. Only administrators can see the full log.</p>

    <div class="filters" role="search">
      <label class="search">
        <Icon name="search" :size="18" />
        <span class="sr-only">Search by student, user or detail</span>
        <input v-model="f.q" type="search" placeholder="Search student, user or detail" />
      </label>
      <label><span>Action</span>
        <select v-model="f.action"><option value="all">All actions</option><option v-for="a in actions" :key="a">{{ a }}</option></select>
      </label>
      <label><span>Done by</span>
        <select v-model="f.who"><option value="all">Anyone</option><option v-for="p in people" :key="p">{{ p }}</option></select>
      </label>
      <label><span>From</span><input v-model="f.from" type="date" /></label>
      <label><span>To</span><input v-model="f.to" type="date" /></label>
    </div>

    <p class="count"><strong class="num">{{ list.length }}</strong> of {{ staff.audit.length }} entries</p>

    <ol class="log">
      <li v-for="a in list" :key="a.id">
        <span class="when num"><strong>{{ formatDate(a.at, { weekday: undefined }) }}</strong>{{ formatTime(a.at) }}</span>
        <span class="act"><span class="tag" :class="TONE[a.action]">{{ a.action }}</span></span>
        <span class="det">
          {{ a.details }}
          <RouterLink v-if="a.studentId" :to="`/staff/students/${a.studentId}`" class="open">Open student</RouterLink>
        </span>
        <span class="who">{{ a.who }}</span>
      </li>
      <li v-if="!list.length" class="empty">No entries match.</li>
    </ol>
  </div>
</template>

<style scoped>
.wide {
  max-width: 1240px;
}

.lock {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  border-radius: 999px;
  background: var(--surface);
  border: 1px solid var(--line);
  font-size: 0.875rem;
  color: var(--ink-2);
  margin-bottom: 16px;
}

.filters {
  display: grid;
  grid-template-columns: minmax(200px, 1.6fr) repeat(2, minmax(0, 1fr)) repeat(2, minmax(0, 0.8fr));
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
.filters input {
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

.count {
  margin: 14px 0 8px;
  color: var(--ink-2);
}

.log {
  list-style: none;
  margin: 0;
  padding: 0;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-m);
  overflow: hidden;
}

.log li {
  display: grid;
  grid-template-columns: 110px 150px minmax(0, 1fr) 160px;
  gap: 14px;
  align-items: start;
  padding: 12px 18px;
  font-size: 0.9375rem;
}

.log li + li {
  border-top: 1px solid var(--line);
}

.when {
  display: flex;
  flex-direction: column;
  font-size: 0.8125rem;
  color: var(--muted);
  line-height: 1.3;
}

.when strong {
  color: var(--ink);
  font-weight: 600;
  font-size: 0.875rem;
}

.tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.8125rem;
  font-weight: 600;
  background: var(--paper);
  color: var(--ink-2);
}

.tag.ink { background: var(--ink); color: #fff; }
.tag.route { background: var(--route-soft); color: var(--route-ink); }
.tag.ok { background: var(--ok-soft); color: var(--ok); }
.tag.low { background: var(--low-soft); color: var(--low); }
.tag.high { background: var(--high-soft); color: var(--high); }

.det {
  line-height: 1.45;
}

.open {
  margin-left: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
  white-space: nowrap;
}

.who {
  color: var(--ink-2);
  font-size: 0.875rem;
}

.empty {
  display: block !important;
  text-align: center;
  color: var(--muted);
  padding: 24px !important;
}

@media (max-width: 1100px) {
  .filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .search {
    grid-column: 1 / -1;
  }
}

@media (max-width: 760px) {
  .log li {
    grid-template-columns: minmax(0, 1fr) auto;
    grid-template-areas: 'when act' 'det det' 'who who';
    gap: 6px 10px;
    padding: 12px 14px;
  }
  .when { grid-area: when; flex-direction: row; gap: 6px; align-items: baseline; }
  .act { grid-area: act; }
  .det { grid-area: det; }
  .who { grid-area: who; font-size: 0.8125rem; }
}
</style>
