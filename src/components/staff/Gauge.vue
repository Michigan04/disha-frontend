<script setup>
import { computed } from 'vue'

// A half-circle meter: one ratio against a limit. The track is a lighter step of the
// fill's own colour, so the state reads across the whole arc.
const props = defineProps({
  value: { type: Number, required: true },
  max: { type: Number, required: true },
  tone: { type: String, default: 'ok' }, // ok | low | high | route | calm
  label: { type: String, default: '' },
})

const W = 200
const R = 80
const TH = 18
const ratio = computed(() => (props.max ? Math.min(1, props.value / props.max) : 0))
const pct = computed(() => Math.round(ratio.value * 100))
const point = (t) => {
  const a = Math.PI * (1 - t)
  return [W / 2 + R * Math.cos(a), 100 - R * Math.sin(a)]
}
const arc = (t0, t1) => {
  const [x0, y0] = point(t0)
  const [x1, y1] = point(t1)
  return `M${x0.toFixed(2)} ${y0.toFixed(2)} A${R} ${R} 0 0 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`
}
const track = arc(0, 1)
const fill = computed(() => (ratio.value > 0 ? arc(0, Math.max(0.005, ratio.value)) : ''))
</script>

<template>
  <div class="gauge" :class="tone" role="img" :aria-label="`${label}: ${value} of ${max}, ${pct}%`">
    <svg :viewBox="`0 0 ${W} 112`">
      <path :d="track" fill="none" class="track" :stroke-width="TH" stroke-linecap="round" />
      <path v-if="fill" :d="fill" fill="none" class="fill" :stroke-width="TH" stroke-linecap="round" />
    </svg>
    <div class="read">
      <span class="pv num">{{ pct }}<small>%</small></span>
      <span class="pl num">{{ value }} of {{ max }}</span>
    </div>
  </div>
</template>

<style scoped>
.gauge {
  position: relative;
  width: 100%;
  max-width: 240px;
  margin: 0 auto;
  --g: var(--ok);
  --g-soft: #d3eee2;
}

.gauge.low { --g: #d98a1c; --g-soft: #f8e6c8; }
.gauge.high { --g: var(--high); --g-soft: #f7d6d1; }
.gauge.route { --g: var(--route); --g-soft: #dcdef8; }
.gauge.calm { --g: var(--calm); --g-soft: var(--calm-light); }

svg {
  display: block;
  width: 100%;
  height: auto;
}

.track {
  stroke: var(--g-soft);
}

.fill {
  stroke: var(--g);
}

.read {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.1;
}

.pv {
  font-size: 2rem;
  font-weight: 600;
  color: var(--ink);
}

.pv small {
  font-size: 1rem;
  font-weight: 500;
  color: var(--muted);
}

.pl {
  font-size: 0.8125rem;
  color: var(--muted);
  margin-top: 2px;
}
</style>
