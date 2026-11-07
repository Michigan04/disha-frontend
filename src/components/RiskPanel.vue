<script setup>
import { computed } from 'vue'
import Icon from './Icon.vue'
import { formatTime, relativeDay } from '../utils/dates'

const props = defineProps({
  risk: { type: Object, required: true },
  student: { type: Object, required: true },
})

const view = computed(() => {
  const r = props.risk
  if (r.level === 'high') {
    const iv = props.student.intervention
    return {
      icon: 'person',
      title: 'Your instructor is supporting you',
      body: `${r.focus.course.name} has not been cleared in two attempts, so ${iv?.instructor || 'your instructor'} will work with you on a plan to pass it.`,
      next: iv ? `Next check-in: ${relativeDay(iv.meetingAt)}, ${formatTime(iv.meetingAt)}` : '',
      cta: { label: 'Open your study plan', to: { path: `/courses/${r.focus.course.id}`, query: { tab: 'plan' } } },
    }
  }
  if (r.level === 'low') {
    return {
      icon: 'spark',
      title: `One course to clear: ${r.focus.course.name}`,
      body: 'You did not pass it last time. Disha has a plan built from how past students passed it on their next attempt.',
      next: '',
      cta: { label: 'Open your study plan', to: { path: `/courses/${r.focus.course.id}`, query: { tab: 'plan' } } },
    }
  }
  return {
    icon: 'check',
    title: 'You are on track',
    body: 'You have not failed any course. Keep your weekly assignments up to date to stay eligible for every OPPE.',
    next: '',
    cta: { label: 'View your progress', to: '/progress' },
  }
})
</script>

<template>
  <section class="risk" :class="risk.level" aria-labelledby="risk-title">
    <div class="badge">
      <Icon :name="view.icon" :size="22" />
    </div>
    <div class="body">
      <p class="level">{{ risk.label }}<span v-if="risk.level !== 'none'">: {{ risk.rule.toLowerCase() }}</span></p>
      <h2 id="risk-title">{{ view.title }}</h2>
      <p class="text">{{ view.body }}</p>
      <p v-if="view.next" class="next"><Icon name="clock" :size="16" /> {{ view.next }}</p>
      <RouterLink class="btn" :to="view.cta.to">{{ view.cta.label }}</RouterLink>
    </div>
  </section>
</template>

<style scoped>
.risk {
  display: flex;
  gap: 16px;
  border-radius: var(--r-l);
  padding: 26px 28px;
  background: var(--ok-soft);
  --tone: var(--ok);
}

.risk.low {
  background: var(--low-soft);
  --tone: var(--low);
}

.risk.high {
  background: var(--high-soft);
  --tone: var(--high);
}

.badge {
  flex: none;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--surface);
  color: var(--tone);
}

.level {
  color: var(--tone);
  font-weight: 600;
  font-size: 0.9375rem;
}

h2 {
  margin-top: 2px;
}

.text {
  margin-top: 6px;
  color: var(--ink-2);
  max-width: 60ch;
}

.next {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  font-weight: 500;
  color: var(--ink);
}

.btn {
  margin-top: 18px;
  background: var(--ink);
}

.btn:hover {
  background: var(--ink-2);
}
</style>
