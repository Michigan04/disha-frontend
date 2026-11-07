<script setup>
import Icon from '../Icon.vue'
import { INTERVENTION_TYPES, OUTCOMES } from '../../data/actions'
import { STAFF } from '../../data/staff'
import { COURSES } from '../../data/courses'
import { formatDate, relativeDay } from '../../utils/dates'

// Intervention history, newest first (US-06).
defineProps({ items: { type: Array, required: true } })
const name = (id) => STAFF[id]?.name || id
const overdue = (d) => d && d < new Date(new Date().setHours(0, 0, 0, 0))
</script>

<template>
  <ol v-if="items.length" class="tl">
    <li v-for="i in items" :key="i.id" :class="i.type">
      <span class="ic"><Icon :name="INTERVENTION_TYPES[i.type].icon" :size="16" /></span>
      <div class="body">
        <div class="top">
          <strong>{{ INTERVENTION_TYPES[i.type].label }}<template v-if="i.referralTo"> to {{ name(i.referralTo) }}</template></strong>
          <span class="chip" :class="OUTCOMES[i.outcome].cls">{{ OUTCOMES[i.outcome].label }}</span>
        </div>
        <p>{{ i.notes }}</p>
        <p class="meta">
          {{ name(i.by) }}, {{ formatDate(i.at) }}<template v-if="i.courseId"> · {{ COURSES[i.courseId]?.name }}</template>
        </p>
        <p v-if="i.followUp && i.outcome !== 'resolved'" class="fu" :class="{ late: overdue(i.followUp) }">
          <Icon name="clock" :size="14" /> Follow up {{ relativeDay(i.followUp).toLowerCase() }}<template v-if="overdue(i.followUp)">, overdue</template>
        </p>
      </div>
    </li>
  </ol>
  <p v-else class="empty">No interventions yet.</p>
</template>

<style scoped>
.tl {
  list-style: none;
  margin: 0;
  padding: 0;
  position: relative;
}

.tl::before {
  content: '';
  position: absolute;
  left: 15px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: var(--line);
}

.tl li {
  position: relative;
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr);
  gap: 12px;
  padding-bottom: 18px;
}

.tl li:last-child {
  padding-bottom: 0;
}

.ic {
  position: relative;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--route-soft);
  color: var(--route-ink);
  border: 3px solid var(--surface);
}

.referral .ic { background: var(--low-soft); color: var(--low); }
.meeting .ic { background: var(--ok-soft); color: var(--ok); }

.top {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 6px 10px;
  align-items: center;
}

.top strong {
  font-weight: 600;
}

.body p {
  margin-top: 4px;
  font-size: 0.9375rem;
}

.meta {
  color: var(--muted);
  font-size: 0.8125rem !important;
}

.fu {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.8125rem !important;
  font-weight: 500;
  color: var(--route-ink);
}

.fu.late {
  color: var(--high);
}

.empty {
  color: var(--muted);
}
</style>
