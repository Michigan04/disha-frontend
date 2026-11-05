<script setup>
import Icon from '../Icon.vue'

// One headline number with what it means, optionally a link to the list behind it.
defineProps({
  value: { type: [Number, String], required: true },
  label: { type: String, required: true },
  sub: { type: String, default: '' },
  icon: { type: String, default: '' },
  tone: { type: String, default: '' },
  to: { type: [String, Object], default: null },
})
</script>

<template>
  <component :is="to ? 'RouterLink' : 'div'" :to="to" class="kpi" :class="tone">
    <span v-if="icon" class="ic"><Icon :name="icon" :size="18" /></span>
    <span class="v num">{{ value }}</span>
    <span class="l">{{ label }}</span>
    <span v-if="sub" class="s">{{ sub }}</span>
  </component>
</template>

<style scoped>
.kpi {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 16px 18px;
  border-radius: var(--r-m);
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--ink);
  text-decoration: none;
  line-height: 1.3;
  min-width: 0;
  --tone: var(--route);
  --tone-soft: var(--route-soft);
}

a.kpi:hover {
  border-color: var(--line-2);
  box-shadow: 0 2px 10px rgba(20, 26, 50, 0.06);
}

.kpi.high { --tone: var(--high); --tone-soft: var(--high-soft); }
.kpi.low { --tone: var(--low); --tone-soft: var(--low-soft); }
.kpi.ok { --tone: var(--ok); --tone-soft: var(--ok-soft); }

.ic {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: var(--tone-soft);
  color: var(--tone);
  margin-bottom: 8px;
}

.v {
  font-size: 2rem;
  font-weight: 600;
  line-height: 1.05;
  color: var(--tone);
  letter-spacing: -0.01em;
}

.kpi:not(.high):not(.low):not(.ok) .v {
  color: var(--ink);
}

.l {
  font-weight: 500;
}

.s {
  font-size: 0.8125rem;
  color: var(--muted);
}
</style>
