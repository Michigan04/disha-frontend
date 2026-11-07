<script setup>
import { computed } from 'vue'

// A single-ratio pie ring for KPI tiles: one coloured slice (value of max) on a pale
// track, with the share printed in the middle so the number never depends on colour.
const props = defineProps({
  value: { type: Number, required: true },
  max: { type: Number, required: true },
  color: { type: String, required: true },
  size: { type: Number, default: 58 },
  thickness: { type: Number, default: 10 },
  sub: { type: String, default: '' },
  label: { type: String, default: '' },
})

const r = computed(() => 50 - props.thickness / 2)
const circ = computed(() => 2 * Math.PI * r.value)
const ratio = computed(() => (props.max > 0 ? Math.min(1, Math.max(0, props.value / props.max)) : 0))
const pct = computed(() => Math.round(ratio.value * 100))
const dash = computed(() => `${(ratio.value * circ.value).toFixed(2)} ${circ.value.toFixed(2)}`)
const big = computed(() => props.size >= 120)
</script>

<template>
  <div class="ring" :class="{ big }" :style="{ width: `${size}px`, height: `${size}px` }" role="img" :aria-label="`${label}: ${value} of ${max}, ${pct}%`" :title="`${value} of ${max} (${pct}%)`">
    <svg viewBox="0 0 100 100">
      <circle cx="50" cy="50" :r="r" fill="none" class="track" :stroke-width="thickness" />
      <circle
        v-if="ratio > 0"
        cx="50"
        cy="50"
        :r="r"
        fill="none"
        :style="{ stroke: color }"
        :stroke-width="thickness"
        :stroke-dasharray="dash"
        :stroke-linecap="ratio < 1 ? 'round' : 'butt'"
        transform="rotate(-90 50 50)"
        class="fill"
      />
    </svg>
    <div class="mid">
      <span class="pv num">{{ pct }}<small>%</small></span>
      <span v-if="sub" class="ps num">{{ sub }}</span>
    </div>
  </div>
</template>

<style scoped>
.ring {
  position: relative;
  flex: none;
}

svg {
  display: block;
  width: 100%;
  height: 100%;
}

.track {
  stroke: var(--viz-track);
}

.fill {
  transition: stroke-dasharray 0.4s ease;
}

.mid {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  line-height: 1.05;
  pointer-events: none;
}

.pv {
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--ink);
}

.pv small {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--muted);
}

.big .pv {
  font-size: 2rem;
  font-weight: 600;
}

.big .pv small {
  font-size: 1rem;
}

.ps {
  font-size: 0.8125rem;
  color: var(--muted);
  margin-top: 2px;
}
</style>
