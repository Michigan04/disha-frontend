<script setup>
import Icon from '../Icon.vue'

// A KPI tile: the headline number, a signed change against a named period, and a
// small pie ring on the right that shows the share behind the number.
defineProps({
  value: { type: [Number, String], required: true },
  label: { type: String, required: true },
  sub: { type: String, default: '' },
  icon: { type: String, default: '' },
  tone: { type: String, default: '' }, // high | low | ok | pred
  delta: { type: String, default: '' },
  deltaGood: { type: Boolean, default: null },
  to: { type: [String, Object], default: null },
})
</script>

<template>
  <component :is="to ? 'RouterLink' : 'div'" :to="to" class="kc" :class="[tone, { 'has-viz': $slots.default }]">
    <div class="txt">
      <div class="kc-top">
        <span v-if="icon" class="ic"><Icon :name="icon" :size="16" /></span>
        <span class="l">{{ label }}</span>
      </div>
      <div class="kc-mid">
        <span class="v num">{{ value }}</span>
        <span v-if="delta" class="delta num" :class="deltaGood === true ? 'good' : deltaGood === false ? 'bad' : ''">{{ delta }}</span>
      </div>
      <span v-if="sub" class="s">{{ sub }}</span>
    </div>
    <div v-if="$slots.default" class="viz"><slot /></div>
  </component>
</template>

<style scoped>
.kc {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 16px 16px 18px;
  border-radius: var(--r-m);
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--ink);
  text-decoration: none;
  min-width: 0;
  overflow: hidden;
  --tone: var(--ink-2);
  --tone-soft: var(--paper);
}

a.kc:hover {
  border-color: var(--line-2);
  box-shadow: 0 4px 14px rgba(28, 25, 23, 0.08);
}

.kc.high { --tone: var(--viz-critical); --tone-soft: var(--high-soft); }
.kc.low { --tone: var(--viz-warning); --tone-soft: var(--low-soft); }
.kc.ok { --tone: var(--viz-good); --tone-soft: var(--ok-soft); }
.kc.pred { --tone: var(--viz-pred); --tone-soft: var(--pred-soft); }

.txt {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kc-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ic {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  display: grid;
  place-items: center;
  background: var(--tone-soft);
  color: var(--tone);
  flex: none;
}

.kc.low .ic {
  color: var(--low);
}

.l {
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--ink-2);
  line-height: 1.25;
}

.kc-mid {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 4px 8px;
  margin-top: 4px;
}

.v {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.01em;
  color: var(--ink);
}

.delta {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 1px 7px;
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
  font-size: 0.75rem;
  color: var(--muted);
  line-height: 1.3;
}

.viz {
  flex: none;
}
</style>
