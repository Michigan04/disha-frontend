<script setup>
import { computed } from 'vue'

// Term GPA (dots) and CGPA after each term (line), on a 5 to 10 scale.
const props = defineProps({ terms: { type: Array, required: true } })

const W = 640
const H = 240
const pad = { l: 40, r: 44, t: 24, b: 40 }
const yMin = 5
const yMax = 10

const rows = computed(() => props.terms.filter((t) => t.cgpaAfter != null))
const x = (i) => pad.l + (rows.value.length < 2 ? (W - pad.l - pad.r) / 2 : (i * (W - pad.l - pad.r)) / (rows.value.length - 1))
const y = (v) => pad.t + (1 - (v - yMin) / (yMax - yMin)) * (H - pad.t - pad.b)
const line = computed(() => rows.value.map((t, i) => `${i ? 'L' : 'M'}${x(i)} ${y(t.cgpaAfter)}`).join(' '))
const ticks = [5, 6, 7, 8, 9, 10]
const summary = computed(() => rows.value.map((t) => `${t.term}: term GPA ${t.termGpa ?? 'none'}, CGPA ${t.cgpaAfter}`).join('; '))
</script>

<template>
  <figure class="chart">
    <svg :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="`CGPA by term. ${summary}`">
      <g v-for="t in ticks" :key="t">
        <line :x1="pad.l" :x2="W - pad.r" :y1="y(t)" :y2="y(t)" stroke="var(--line)" />
        <text :x="pad.l - 10" :y="y(t) + 4" text-anchor="end" class="tick">{{ t }}</text>
      </g>
      <path :d="line" fill="none" stroke="var(--route)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
      <g v-for="(t, i) in rows" :key="t.term">
        <circle v-if="t.termGpa != null" :cx="x(i)" :cy="y(t.termGpa)" r="5" fill="var(--surface)" stroke="var(--muted)" stroke-width="2" />
        <circle :cx="x(i)" :cy="y(t.cgpaAfter)" r="6" fill="var(--route)" />
        <text :x="x(i)" :y="y(t.cgpaAfter) - 14" text-anchor="middle" class="val">{{ t.cgpaAfter.toFixed(2) }}</text>
        <text :x="x(i)" :y="H - 12" text-anchor="middle" class="tick">{{ t.term }}</text>
      </g>
    </svg>
    <figcaption>
      <span><i class="key line"></i>CGPA after each term</span>
      <span><i class="key dot"></i>Term GPA</span>
    </figcaption>
  </figure>
</template>

<style scoped>
.chart {
  margin: 0;
}

svg {
  width: 100%;
  height: auto;
  display: block;
}

.tick {
  font-size: 13px;
  fill: var(--muted);
}

.val {
  font-size: 14px;
  font-weight: 600;
  fill: var(--route-ink);
}

figcaption {
  display: flex;
  gap: 20px;
  font-size: 0.875rem;
  color: var(--muted);
  margin-top: 6px;
}

.key {
  display: inline-block;
  vertical-align: middle;
  margin-right: 8px;
}

.key.line {
  width: 18px;
  height: 3px;
  border-radius: 2px;
  background: var(--route);
}

.key.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--muted);
}
</style>
