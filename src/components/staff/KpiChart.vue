<script setup>
import Icon from '../Icon.vue'

// A stat tile with a small chart: the number, a signed change against a named period,
// and a sparkline or meter in the slot underneath.
defineProps({
  value: { type: [Number, String], required: true },
  label: { type: String, required: true },
  sub: { type: String, default: '' },
  icon: { type: String, default: '' },
  tone: { type: String, default: '' }, // high | low | ok | route
  delta: { type: String, default: '' },
  deltaGood: { type: Boolean, default: null },
  to: { type: [String, Object], default: null },
})
</script>

<template>
  <component :is="to ? 'RouterLink' : 'div'" :to="to" class="kc" :class="tone">
    <div class="kc-top">
      <span v-if="icon" class="ic"><Icon :name="icon" :size="16" /></span>
      <span class="l">{{ label }}</span>
    </div>
    <div class="kc-mid">
      <span class="v num">{{ value }}</span>
      <span v-if="delta" class="delta num" :class="deltaGood === true ? 'good' : deltaGood === false ? 'bad' : ''">{{ delta }}</span>
    </div>
    <span v-if="sub" class="s">{{ sub }}</span>
    <div v-if="$slots.default" class="viz"><slot /></div>
  </component>
</template>

<style scoped>
.kc {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 18px 20px 16px;
  border-radius: var(--r-m);
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--ink);
  text-decoration: none;
  min-width: 0;
  --tone: var(--route);
  --tone-soft: var(--route-soft);
}

a.kc:hover {
  border-color: var(--line-2);
  box-shadow: 0 2px 10px rgba(20, 26, 50, 0.06);
}

.kc.high { --tone: var(--high); --tone-soft: var(--high-soft); }
.kc.low { --tone: var(--low); --tone-soft: var(--low-soft); }
.kc.ok { --tone: var(--ok); --tone-soft: var(--ok-soft); }

.kc-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ic {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: var(--tone-soft);
  color: var(--tone);
  flex: none;
}

.l {
  font-weight: 500;
  font-size: 0.9375rem;
  color: var(--ink-2);
  line-height: 1.25;
}

.kc-mid {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-top: 6px;
}

.v {
  font-size: 2.125rem;
  font-weight: 600;
  line-height: 1;
  letter-spacing: -0.01em;
  color: var(--ink);
}

.delta {
  font-size: 0.8125rem;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--paper);
  color: var(--ink-2);
  white-space: nowrap;
}

.delta.good {
  background: var(--ok-soft);
  color: var(--ok);
}

.delta.bad {
  background: var(--high-soft);
  color: var(--high);
}

.s {
  font-size: 0.8125rem;
  color: var(--muted);
}

.viz {
  margin-top: auto;
  padding-top: 10px;
}
</style>
