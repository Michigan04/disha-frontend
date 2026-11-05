<script setup>
import { computed } from 'vue'

// A small line chart: one line per series, labelled at its end (no legend needed).
const props = defineProps({
  labels: { type: Array, required: true },
  series: { type: Array, required: true }, // [{ name, values, color }]
  height: { type: Number, default: 200 },
})

const W = 560
const pad = { l: 34, r: 92, t: 14, b: 28 }
const max = computed(() => Math.max(4, ...props.series.flatMap((s) => s.values)))
const niceMax = computed(() => Math.ceil(max.value / 4) * 4)
const x = (i) => pad.l + (i * (W - pad.l - pad.r)) / Math.max(1, props.labels.length - 1)
const y = (v) => props.height - pad.b - (v / niceMax.value) * (props.height - pad.t - pad.b)
const ticks = computed(() => [0, 1, 2, 3, 4].map((k) => (niceMax.value / 4) * k))
const path = (vals) => vals.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
const desc = computed(() => props.series.map((s) => `${s.name}: ${s.values.join(', ')}`).join('; '))
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${height}`" class="trend" role="img" :aria-label="`By ${labels[0]} to ${labels.at(-1)}. ${desc}`">
    <g class="grid">
      <g v-for="t in ticks" :key="t">
        <line :x1="pad.l" :x2="W - pad.r" :y1="y(t)" :y2="y(t)" />
        <text :x="pad.l - 8" :y="y(t) + 4" text-anchor="end">{{ t }}</text>
      </g>
      <text v-for="(l, i) in labels" :key="l" :x="x(i)" :y="height - 8" text-anchor="middle">{{ l }}</text>
    </g>
    <g v-for="s in series" :key="s.name">
      <path :d="path(s.values)" fill="none" :stroke="s.color" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" />
      <circle v-for="(v, i) in s.values" :key="i" :cx="x(i)" :cy="y(v)" :r="i === s.values.length - 1 ? 4.5 : 2.5" :fill="s.color" />
      <text class="end" :x="x(s.values.length - 1) + 10" :y="y(s.values.at(-1)) + 4" :fill="s.color">{{ s.values.at(-1) }} {{ s.name }}</text>
    </g>
  </svg>
</template>

<style scoped>
.trend {
  width: 100%;
  height: auto;
  display: block;
}

.grid line {
  stroke: var(--line);
  stroke-width: 1;
}

.grid text {
  font-size: 11px;
  fill: var(--muted);
}

.end {
  font-size: 12.5px;
  font-weight: 600;
}
</style>
