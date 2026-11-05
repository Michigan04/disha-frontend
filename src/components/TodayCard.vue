<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import Icon from './Icon.vue'
import { formatDate, formatTime, isToday, minutesUntil, relativeDay } from '../utils/dates'

// Today's meetings from the calendar, shown at the top of the home page.
const props = defineProps({ events: { type: Array, required: true } })

const now = ref(new Date())
let timer
onMounted(() => { timer = setInterval(() => { now.value = new Date() }, 30000) })
onUnmounted(() => clearInterval(timer))

const today = computed(() => props.events.filter((e) => isToday(e.start, now.value)))
const nextLater = computed(() => props.events.find((e) => e.start > now.value && !isToday(e.start, now.value)))

function state(e) {
  if (e.end && e.end <= now.value) return 'done'
  if (e.start <= now.value) return 'live'
  return 'upcoming'
}
const firstUpcoming = computed(() => today.value.find((e) => state(e) !== 'done'))

function when(e) {
  const s = state(e)
  if (s === 'live') return 'Live now'
  if (s === 'done') return 'Finished'
  const m = minutesUntil(e.start, now.value)
  if (m < 60) return `In ${m} min`
  const h = Math.floor(m / 60)
  return `In ${h} h ${m % 60 ? `${m % 60} min` : ''}`.trim()
}
</script>

<template>
  <section class="today" aria-labelledby="today-h">
    <header>
      <h2 id="today-h">Today</h2>
      <span class="muted">{{ formatDate(now, { weekday: 'long' }) }}</span>
    </header>

    <ul v-if="today.length">
      <li v-for="e in today" :key="e.id" :class="[state(e), { next: e === firstUpcoming }]">
        <span class="time num">{{ formatTime(e.start) }}</span>
        <div class="what">
          <strong>{{ e.title }}</strong>
          <span class="when">
            <span v-if="state(e) === 'live'" class="pulse" aria-hidden="true"></span>{{ when(e) }}
          </span>
        </div>
        <a v-if="e.link && state(e) !== 'done'" class="join" :href="e.link" target="_blank" rel="noopener" :aria-label="`Join ${e.title}`">
          <Icon name="video" :size="16" /> Join
        </a>
      </li>
    </ul>
    <div v-else class="none">
      <p><strong>No meetings today</strong></p>
      <p v-if="nextLater" class="muted">Next: {{ nextLater.title }}, {{ relativeDay(nextLater.start).toLowerCase() }} at {{ formatTime(nextLater.start) }}</p>
    </div>
  </section>
</template>

<style scoped>
.today {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-m);
  padding: 14px 16px;
}

header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

h2 {
  font-size: 1.0625rem;
}

header .muted {
  font-size: 0.875rem;
}

ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

li {
  display: grid;
  grid-template-columns: 62px 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 8px 10px;
  border-radius: var(--r-s);
}

li.next,
li.live {
  background: var(--route-soft);
}

li.done {
  opacity: 0.55;
}

.time {
  font-weight: 600;
  font-size: 0.9375rem;
  color: var(--route-ink);
}

.what {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.3;
}

.what strong {
  font-weight: 600;
  font-size: 0.9375rem;
}

.when {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  color: var(--muted);
}

.next .when,
.live .when {
  color: var(--route-ink);
  font-weight: 600;
}

.pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--high);
  animation: pulse 1.6s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.join {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8125rem;
  font-weight: 600;
  text-decoration: none;
  color: #fff;
  background: var(--route);
  padding: 5px 10px;
  border-radius: 999px;
}

li:not(.next):not(.live) .join {
  background: transparent;
  color: var(--route-ink);
  border: 1px solid var(--line-2);
}

.none p + p {
  margin-top: 2px;
  font-size: 0.875rem;
}
</style>
