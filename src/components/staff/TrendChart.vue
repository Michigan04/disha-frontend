<script setup>
import { computed, ref } from 'vue'

// A small line chart: one line per series, a legend, the latest value labelled at the
// end of each line, and a crosshair that shows every series for the week under the pointer.
const props = defineProps({
  labels: { type: Array, required: true },
  series: { type: Array, required: true }, // [{ name, values, color }]
  height: { type: Number, default: 200 },
  area: { type: Boolean, default: false },
})

const W = 560
const pad = { l: 34, r: 74, t: 14, b: 28 }
const max = computed(() => Math.max(4, ...props.series.flatMap((s) => s.values)))
const niceMax = computed(() => Math.ceil(max.value / 4) * 4)
const x = (i) => pad.l + (i * (W - pad.l - pad.r)) / Math.max(1, props.labels.length - 1)
const y = (v) => props.height - pad.b - (v / niceMax.value) * (props.height - pad.t - pad.b)
const ticks = computed(() => [0, 1, 2, 3, 4].map((k) => (niceMax.value / 4) * k))
const path = (vals) => vals.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
const areaPath = (vals) => `${path(vals)} L${x(vals.length - 1).toFixed(1)},${y(0)} L${x(0).toFixed(1)},${y(0)} Z`
const desc = computed(() => props.series.map((s) => `${s.name}: ${s.values.join(', ')}`).join('; '))

const svg = ref(null)
const at = ref(null)
function move(e) {
  const box = svg.value.getBoundingClientRect()
  const vx = ((e.clientX - box.left) / box.width) * W
  const step = (W - pad.l - pad.r) / Math.max(1, props.labels.length - 1)
  at.value = Math.max(0, Math.min(props.labels.length - 1, Math.round((vx - pad.l) / step)))
}
function key(e) {
  const n = props.labels.length - 1
  if (e.key === 'ArrowRight') at.value = Math.min(n, (at.value ?? -1) + 1)
  else if (e.key === 'ArrowLeft') at.value = Math.max(0, (at.value ?? n + 1) - 1)
  else return
  e.preventDefault()
}
const tipLeft = computed(() => (at.value == null ? 0 : (x(at.value) / W) * 100))
</script>

<template>
  <div class="tc">
    <ul class="legend" aria-hidden="true">
      <li v-for="s in series" :key="s.name"><i :style="{ background: s.color }"></i>{{ s.name }}</li>
    </ul>
    <div class="plot">
      <svg
        ref="svg"
        :viewBox="`0 0 ${W} ${height}`"
        class="trend"
        role="img"
        tabindex="0"
        :aria-label="`By ${labels[0]} to ${labels.at(-1)}. ${desc}`"
        @pointermove="move"
        @pointerleave="at = null"
        @keydown="key"
        @blur="at = null"
      >
        <g class="grid">
          <g v-for="t in ticks" :key="t">
            <line :x1="pad.l" :x2="W - pad.r" :y1="y(t)" :y2="y(t)" />
            <text :x="pad.l - 8" :y="y(t) + 4" text-anchor="end">{{ t }}</text>
          </g>
          <text v-for="(l, i) in labels" :key="l" :x="x(i)" :y="height - 8" text-anchor="middle" :class="{ on: at === i }">{{ l }}</text>
        </g>
        <line v-if="at != null" class="cross" :x1="x(at)" :x2="x(at)" :y1="pad.t" :y2="height - pad.b" />
        <g v-for="s in series" :key="s.name">
          <path v-if="area" :d="areaPath(s.values)" :fill="s.color" opacity="0.1" />
          <path :d="path(s.values)" fill="none" :stroke="s.color" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
          <circle
            v-for="(v, i) in s.values"
            :key="i"
            :cx="x(i)"
            :cy="y(v)"
            :r="i === s.values.length - 1 || at === i ? 4.5 : 2.5"
            :fill="s.color"
            stroke="var(--surface)"
            stroke-width="2"
          />
          <text class="end" :x="x(s.values.length - 1) + 10" :y="y(s.values.at(-1)) + 4">{{ s.values.at(-1) }} {{ s.name }}</text>
        </g>
        <rect :x="pad.l - 10" :y="0" :width="W - pad.l - pad.r + 20" :height="height" fill="transparent" />
      </svg>
      <div v-if="at != null" class="tip" :class="{ start: tipLeft < 18, end: tipLeft > 82 }" :style="{ left: `${tipLeft}%` }" role="tooltip">
        <span class="tl">{{ labels[at] }}</span>
        <span v-for="s in series" :key="s.name" class="tr">
          <i :style="{ background: s.color }"></i><strong class="num">{{ s.values[at] }}</strong> {{ s.name }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.legend {
  list-style: none;
  margin: 0 0 6px;
  padding: 0;
  display: flex;
  gap: 16px;
  font-size: 0.8125rem;
  color: var(--ink-2);
}

.legend li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend i {
  width: 14px;
  height: 2px;
  border-radius: 2px;
}

.plot {
  position: relative;
}

.trend {
  width: 100%;
  height: auto;
  display: block;
  outline: none;
}

.trend:focus-visible {
  outline: 2px solid var(--route);
  outline-offset: 4px;
}

.grid line {
  stroke: var(--line);
  stroke-width: 1;
}

.grid text {
  font-size: 11px;
  fill: var(--muted);
}

.grid text.on {
  fill: var(--ink);
  font-weight: 600;
}

.cross {
  stroke: var(--line-2);
  stroke-width: 1;
}

.end {
  font-size: 12.5px;
  font-weight: 600;
  fill: var(--ink-2);
}

.tip {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--surface);
  border: 1px solid var(--line);
  box-shadow: 0 6px 18px rgba(28, 25, 23, 0.12);
  font-size: 0.8125rem;
  color: var(--ink-2);
  pointer-events: none;
  white-space: nowrap;
}

.tip.start {
  transform: translateX(-12px);
}

.tip.end {
  transform: translateX(calc(-100% + 12px));
}

.tl {
  color: var(--muted);
  font-size: 0.75rem;
}

.tr {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tr i {
  width: 12px;
  height: 2px;
  border-radius: 2px;
}

.tr strong {
  color: var(--ink);
  font-size: 0.9375rem;
}
</style>
