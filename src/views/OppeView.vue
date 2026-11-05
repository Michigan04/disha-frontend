<script setup>
import { computed } from 'vue'
import { useStudentStore } from '../stores/student'
import { COURSES } from '../data/courses'
import { meets, oppeStatus } from '../utils/progress'
import { daysUntil, formatDate, formatTime, relativeDay } from '../utils/dates'
import Icon from '../components/Icon.vue'

const store = useStudentStore()
const items = computed(() => [...store.student.oppe].sort((a, b) => a.date - b.date))

const HEAD = {
  eligible: { cls: 'ok', text: 'Eligible', icon: 'check' },
  not_eligible: { cls: 'high', text: 'Not eligible', icon: 'cross' },
  pending: { cls: 'route', text: 'Not decided yet', icon: 'clock' },
}

function value(c) {
  if (typeof c.required === 'boolean') return c.actual == null ? 'Not yet' : c.actual ? 'Yes' : 'No'
  return c.actual == null ? 'Not yet' : String(c.actual)
}
function needed(c) {
  return typeof c.required === 'boolean' ? (c.required ? 'Yes' : 'No') : `${c.required} or more`
}
function rowState(c) {
  if (!c.final) return 'pending'
  return meets(c) ? 'met' : 'unmet'
}
</script>

<template>
  <div class="page">
    <header class="page-head">
      <h1>OPPE eligibility</h1>
      <p>To sit an Online Proctored Programming Exam you must meet each condition below before its deadline. Eligibility is checked from your weekly assignment scores.</p>
    </header>

    <div class="cards">
      <article v-for="o in items" :key="o.id" class="oppe" :class="oppeStatus(o)">
        <header>
          <div>
            <h2>{{ COURSES[o.courseId].name }}, {{ o.title }}</h2>
            <p class="muted"><Icon name="calendar" :size="16" /> {{ daysUntil(o.date) < 7 ? `${relativeDay(o.date)}, ` : '' }}{{ formatDate(o.date, { weekday: 'long' }) }} at {{ formatTime(o.date) }}</p>
          </div>
          <span class="state" :class="HEAD[oppeStatus(o)].cls">
            <Icon :name="HEAD[oppeStatus(o)].icon" :size="18" /> {{ HEAD[oppeStatus(o)].text }}
          </span>
        </header>

        <table>
          <thead>
            <tr>
              <th scope="col">Condition</th>
              <th scope="col" class="r">Needed</th>
              <th scope="col" class="r">Yours</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in o.criteria" :key="c.label" :class="rowState(c)">
              <th scope="row">
                <span class="mark" aria-hidden="true"><Icon :name="rowState(c) === 'met' ? 'check' : rowState(c) === 'unmet' ? 'cross' : 'clock'" :size="16" /></span>
                <span>
                  {{ c.label }}
                  <span v-if="!c.final" class="muted when">Final on {{ formatDate(c.finalOn) }}</span>
                </span>
              </th>
              <td class="r">{{ needed(c) }}</td>
              <td class="r num"><strong>{{ value(c) }}</strong></td>
            </tr>
          </tbody>
        </table>

        <p v-if="oppeStatus(o) === 'not_eligible'" class="advice">
          <Icon name="alert" :size="18" />
          {{ o.ifNotEligible || 'Talk to your course team about the next OPPE date and what you need to qualify for it.' }}
        </p>
        <p v-else-if="oppeStatus(o) === 'pending'" class="advice soft">
          <Icon name="clock" :size="18" />
          You meet the conditions so far. Keep submitting weekly assignments until the deadline to stay eligible.
        </p>
      </article>

      <p v-if="!items.length" class="panel muted">None of your courses this term has an OPPE.</p>
    </div>
  </div>
</template>

<style scoped>
.cards {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 860px;
}

.oppe {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-m);
  padding: 22px 24px;
  border-top: 4px solid var(--route);
}

.oppe.eligible {
  border-top-color: var(--ok);
}

.oppe.not_eligible {
  border-top-color: var(--high);
}

.oppe > header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.oppe header p {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.state {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 999px;
  white-space: nowrap;
}

.state.ok {
  background: var(--ok-soft);
  color: var(--ok);
}

.state.high {
  background: var(--high-soft);
  color: var(--high);
}

.state.route {
  background: var(--route-soft);
  color: var(--route-ink);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  text-align: left;
  padding: 10px 0;
  border-top: 1px solid var(--line);
  vertical-align: top;
}

thead th {
  border-top: 0;
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--muted);
  padding-top: 0;
}

tbody th {
  font-weight: 400;
  display: flex;
  gap: 10px;
  padding-right: 16px;
}

.r {
  text-align: right;
  white-space: nowrap;
  padding-left: 16px;
}

.mark {
  flex: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--paper);
  color: var(--muted);
}

.met .mark {
  background: var(--ok-soft);
  color: var(--ok);
}

.unmet .mark {
  background: var(--high-soft);
  color: var(--high);
}

.unmet td strong {
  color: var(--high);
}

.when {
  display: block;
  font-size: 0.875rem;
}

.advice {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: var(--r-s);
  background: var(--high-soft);
  color: var(--ink);
}

.advice svg {
  flex: none;
  margin-top: 3px;
  color: var(--high);
}

.advice.soft {
  background: var(--route-soft);
}

.advice.soft svg {
  color: var(--route);
}

@media (max-width: 560px) {
  .oppe > header {
    flex-direction: column;
  }
}
</style>
