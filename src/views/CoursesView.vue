<script setup>
import { computed, ref } from 'vue'
import { useStudentStore } from '../stores/student'
import StatusChip from '../components/StatusChip.vue'
import Icon from '../components/Icon.vue'

const store = useStudentStore()

const FILTERS = [
  { id: 'all', label: 'All', test: () => true },
  { id: 'now', label: 'This term', test: (c) => c.status.state === 'in_progress' },
  { id: 'attention', label: 'Needs attention', test: (c) => c.status.fails > 0 && c.status.state !== 'passed' },
  { id: 'done', label: 'Completed', test: (c) => c.status.state === 'passed' },
  { id: 'later', label: 'Not started', test: (c) => c.status.state === 'not_started' },
]
const active = ref('all')
const list = computed(() => store.courses.filter(FILTERS.find((f) => f.id === active.value).test))
const count = (f) => store.courses.filter(f.test).length

function detail(c) {
  const s = c.status
  if (s.state === 'passed') return `Passed in ${s.term}${s.fails ? ` after ${s.fails + 1} attempts` : ''}`
  if (s.state === 'in_progress') return `Week ${s.current.week} of ${s.current.weeks}, assignment average ${s.current.assignmentAvg}`
  if (s.state === 'not_cleared') return 'Register again in a later term'
  return c.course.type === 'project' ? 'Project' : `${c.course.credits} credits`
}
</script>

<template>
  <div class="page">
    <header class="page-head">
      <h1>Courses</h1>
      <p>Every {{ store.rule.label }} course and where you stand in it. Open a course to see your attempts and, if you need it, a plan to clear it.</p>
    </header>

    <div class="filters" role="tablist" aria-label="Filter courses">
      <button
        v-for="f in FILTERS"
        :key="f.id"
        type="button"
        role="tab"
        :aria-selected="active === f.id"
        :class="{ on: active === f.id }"
        @click="active = f.id"
      >
        {{ f.label }} <span class="n num">{{ count(f) }}</span>
      </button>
    </div>

    <ul class="list">
      <li v-for="c in list" :key="c.course.id">
        <RouterLink :to="`/courses/${c.course.id}`" class="row" :class="{ flag: c.status.fails > 0 && c.status.state !== 'passed' }">
          <div class="main">
            <strong>{{ c.course.name }}</strong>
            <span class="muted">{{ detail(c) }}</span>
          </div>
          <StatusChip :status="c.status" />
          <Icon name="chevron" class="go" />
        </RouterLink>
      </li>
      <li v-if="!list.length" class="empty">
        <p>No courses here. <button type="button" class="link" @click="active = 'all'">Show all courses</button></p>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 18px;
}

.filters button {
  border: 1px solid var(--line-2);
  background: var(--surface);
  border-radius: 999px;
  padding: 6px 14px;
  cursor: pointer;
  font-weight: 500;
  color: var(--ink-2);
}

.filters button.on {
  background: var(--ink);
  border-color: var(--ink);
  color: #fff;
}

.filters .n {
  margin-left: 4px;
  opacity: 0.7;
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-m);
  overflow: hidden;
}

.list li + li {
  border-top: 1px solid var(--line);
}

.row {
  display: grid;
  grid-template-columns: 1fr auto 20px;
  gap: 16px;
  align-items: center;
  padding: 16px 20px;
  color: inherit;
  text-decoration: none;
}

.row:hover {
  background: var(--paper);
}

.row.flag {
  box-shadow: inset 3px 0 0 var(--low);
}

.main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.main strong {
  font-weight: 600;
}

.main .muted {
  font-size: 0.9375rem;
}

.go {
  color: var(--muted);
}

.empty {
  padding: 20px;
}

.link {
  border: 0;
  background: none;
  color: var(--route-ink);
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
}

@media (max-width: 560px) {
  .row {
    grid-template-columns: 1fr 20px;
  }
  .row .chip {
    grid-column: 1;
    justify-self: start;
  }
  .go {
    grid-row: 1 / span 2;
    grid-column: 2;
  }
}
</style>
