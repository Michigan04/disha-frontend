<script setup>
import { computed } from 'vue'
import { useStudentStore } from '../stores/student'
import { calendarConfigured, useCalendar } from '../services/calendar'
import MeetingList from '../components/MeetingList.vue'
import Icon from '../components/Icon.vue'
import { daysUntil, formatDate, formatTime, relativeDay, startOfDay } from '../utils/dates'

const store = useStudentStore()
const { state, connect, disconnect } = useCalendar()

const groups = computed(() => {
  const map = new Map()
  for (const e of state.events) {
    const key = startOfDay(e.start).getTime()
    if (!map.has(key)) map.set(key, { day: new Date(key), events: [] })
    map.get(key).events.push(e)
  }
  return [...map.values()]
})
</script>

<template>
  <div class="page">
    <header class="page-head">
      <h1>Meetings</h1>
      <p>Live sessions, check-ins and exam slots from your Google Calendar, so you do not miss any of them.</p>
    </header>

    <section class="connect" :class="{ on: state.connected }" aria-live="polite">
      <div class="g"><Icon name="google" :size="26" /></div>
      <div class="txt">
        <template v-if="state.connected">
          <h2>Google Calendar is connected</h2>
          <p class="muted">Last synced {{ relativeDay(state.syncedAt).toLowerCase() }} at {{ formatTime(state.syncedAt) }}. New events appear on your home page too.</p>
        </template>
        <template v-else>
          <h2>Connect your Google Calendar</h2>
          <p class="muted">Disha reads your upcoming events (read-only) and shows the next ones on your home page. It never changes your calendar.</p>
        </template>
        <p v-if="state.error" class="err" role="alert">{{ state.error }}</p>
      </div>
      <div class="act">
        <button v-if="!state.connected" class="btn" type="button" :disabled="state.loading" @click="connect(store.student)">
          {{ state.loading ? 'Connecting' : 'Connect Google Calendar' }}
        </button>
        <button v-else class="btn quiet" type="button" @click="disconnect(store.student)">Disconnect</button>
      </div>
    </section>
    <p v-if="!calendarConfigured" class="note demo">Demo mode: the events below are sample data for {{ store.student.firstName }}.</p>

    <section class="days" aria-label="Upcoming meetings">
      <div v-for="g in groups" :key="g.day.getTime()" class="day">
        <h2 class="dh">
          <template v-if="daysUntil(g.day) < 7">{{ relativeDay(g.day) }} <span class="muted">{{ formatDate(g.day, { weekday: 'long' }) }}</span></template>
          <template v-else>{{ formatDate(g.day, { weekday: 'long' }) }}</template>
        </h2>
        <div class="panel">
          <MeetingList :events="g.events" />
        </div>
      </div>
      <div v-if="!groups.length" class="panel empty">
        <p>No meetings in the next 30 days. Live sessions your course team adds to the calendar will show up here.</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.connect {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 16px;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-l);
  padding: 20px 22px;
  max-width: 860px;
}

.connect.on {
  background: var(--ok-soft);
  border-color: transparent;
}

.g {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--paper);
  color: var(--route-ink);
}

.connect.on .g {
  background: var(--surface);
  color: var(--ok);
}

.txt p {
  margin-top: 2px;
  max-width: 60ch;
}

.err {
  color: var(--high);
  margin-top: 6px;
}

.demo {
  max-width: 860px;
}

.days {
  margin-top: 26px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  max-width: 860px;
}

.dh {
  font-size: 1.0625rem;
  margin-bottom: 8px;
  display: flex;
  gap: 8px;
  align-items: baseline;
}

.dh .muted {
  font-weight: 400;
  font-size: 0.9375rem;
}

@media (max-width: 640px) {
  .connect {
    grid-template-columns: auto 1fr;
  }
  .act {
    grid-column: 1 / -1;
  }
}
</style>
