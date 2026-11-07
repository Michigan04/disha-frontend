<script setup>
import { computed } from 'vue'

const props = defineProps({
  values: { type: Array, required: true },
  min: { type: Number, default: 5 },
  max: { type: Number, default: 10 },
  label: { type: String, default: '' },
  w: { type: Number, default: 132 },
  h: { type: Number, default: 44 },
  fluid: { type: Boolean, default: false },
  color: { type: String, default: 'var(--route)' },
  fit: { type: Boolean, default: false }, // fit the range to any data, not a CGPA scale
})

const W = props.w
const H = props.h
const pts = computed(() => {
  const v = props.values.filter((x) => x != null)
  if (v.length < 2) return []
  // Fit the range to the data so small changes stay visible.
  const lo = props.fit ? Math.min(...v) - 1 : Math.max(props.min, Math.min(...v) - 0.4)
  const hi = props.fit ? Math.max(...v) + 1 : Math.min(props.max, Math.max(...v) + 0.4)
  return v.map((y, i) => [
    6 + (i * (W - 12)) / (v.length - 1),
    H - 6 - ((y - lo) / (hi - lo || 1)) * (H - 12),
  ])
})
const path = computed(() => pts.value.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' '))
</script>

<template>
  <svg v-if="pts.length" :viewBox="`0 0 ${W} ${H}`" :width="fluid ? '100%' : W" :height="fluid ? null : H" :class="{ fluid }" role="img" :aria-label="label">
    <path v-if="fluid" :d="`${path} L${pts.at(-1)[0].toFixed(1)} ${H} L${pts[0][0].toFixed(1)} ${H} Z`" :fill="color" opacity="0.1" />
    <path :d="path" fill="none" :stroke="color" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
    <circle :cx="pts.at(-1)[0]" :cy="pts.at(-1)[1]" r="4" :fill="color" stroke="var(--surface)" stroke-width="2" />
  </svg>
</template>

<style scoped>
.fluid {
  display: block;
  height: auto;
}
</style>
