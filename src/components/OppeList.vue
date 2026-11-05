<script setup>
import { COURSES } from '../data/courses'
import { daysUntil, formatDate, relativeDay } from '../utils/dates'
import { meets, oppeStatus } from '../utils/progress'

defineProps({ items: { type: Array, required: true } })

const LABEL = { eligible: 'Eligible', not_eligible: 'Not eligible', pending: 'Not decided yet' }
const CLS = { eligible: 'ok', not_eligible: 'high', pending: 'route' }

function reason(o) {
  const st = oppeStatus(o)
  if (st === 'not_eligible') {
    const c = o.criteria.find((x) => x.final && !meets(x))
    return typeof c.required === 'boolean' ? c.label : `Assignment average ${c.actual}, needs ${c.required}`
  }
  if (st === 'pending') {
    const c = o.criteria.find((x) => !x.final)
    return `Decided on ${formatDate(c.finalOn)}`
  }
  return 'All conditions met'
}
</script>

<template>
  <ul class="oppe-list">
    <li v-for="o in items" :key="o.id">
      <div class="what">
        <strong>{{ COURSES[o.courseId].name }}, {{ o.title }}</strong>
        <span class="muted">{{ daysUntil(o.date) < 7 ? `${relativeDay(o.date)}, ${formatDate(o.date)}` : formatDate(o.date) }}</span>
      </div>
      <div class="state">
        <span class="chip" :class="CLS[oppeStatus(o)]">{{ LABEL[oppeStatus(o)] }}</span>
        <span class="why">{{ reason(o) }}</span>
      </div>
    </li>
    <li v-if="!items.length" class="empty muted">No OPPE in your courses this term.</li>
  </ul>
</template>

<style scoped>
.oppe-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

li {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
  border-top: 1px solid var(--line);
}

li:first-child {
  border-top: 0;
  padding-top: 0;
}

.what {
  display: flex;
  flex-direction: column;
}

.what strong {
  font-weight: 600;
}

.what span {
  font-size: 0.875rem;
}

.state {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  text-align: right;
}

.why {
  font-size: 0.8125rem;
  color: var(--muted);
}

@media (max-width: 520px) {
  li {
    flex-direction: column;
    gap: 6px;
  }
  .state {
    align-items: flex-start;
    text-align: left;
  }
}
</style>
