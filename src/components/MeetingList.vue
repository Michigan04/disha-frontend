<script setup>
import Icon from './Icon.vue'
import { formatTime, relativeDay, weekday } from '../utils/dates'

defineProps({
  events: { type: Array, required: true },
  compact: { type: Boolean, default: false },
})
</script>

<template>
  <ul class="meetings" :class="{ compact }">
    <li v-for="e in events" :key="e.id" :class="{ important: e.important }">
      <div class="when" :aria-label="`${relativeDay(e.start)}`">
        <span class="d num">{{ e.start.getDate() }}</span>
        <span class="w">{{ weekday(e.start) }}</span>
      </div>
      <div class="what">
        <strong>{{ e.title }}</strong>
        <span class="muted">
          {{ relativeDay(e.start) }}, {{ formatTime(e.start) }}<template v-if="!compact && e.organizer">. {{ e.organizer }}</template>
        </span>
        <span v-if="!compact && e.location" class="muted loc">{{ e.location }}</span>
      </div>
      <a v-if="e.link" class="join" :href="e.link" target="_blank" rel="noopener">
        <Icon name="video" :size="16" /> Join
      </a>
    </li>
    <li v-if="!events.length" class="empty muted">No meetings in the next 30 days.</li>
  </ul>
</template>

<style scoped>
.meetings {
  list-style: none;
  margin: 0;
  padding: 0;
}

li {
  display: grid;
  grid-template-columns: 48px 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 12px 0;
  border-top: 1px solid var(--line);
}

li:first-child {
  border-top: 0;
  padding-top: 0;
}

li.empty {
  display: block;
}

.when {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.1;
  padding: 6px 0;
  border-radius: var(--r-s);
  background: var(--route-soft);
  color: var(--route-ink);
}

.important .when {
  background: var(--route);
  color: #fff;
}

.d {
  font-size: 1.25rem;
  font-weight: 600;
}

.w {
  font-size: 0.75rem;
}

.what {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.what strong {
  font-weight: 600;
  line-height: 1.35;
}

.what span {
  font-size: 0.875rem;
}

.join {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--line-2);
}

.join:hover {
  background: var(--route-soft);
}
</style>
