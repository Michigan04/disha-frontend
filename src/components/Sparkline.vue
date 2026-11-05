<script setup>
import { computed } from 'vue'

const props = defineProps({
  values: { type: Array, required: true },
  min: { type: Number, default: 5 },
  max: { type: Number, default: 10 },
  label: { type: String, default: '' },
})

const W = 132
const H = 44
const pts = computed(() => {
  const v = props.values.filter((x) => x != null)
  if (v.length < 2) return []
  // Fit the range to the data so small changes stay visible.
  const lo = Math.max(props.min, Math.min(...v) - 0.4)
  const hi = Math.min(props.max, Math.max(...v) + 0.4)
  return v.map((y, i) => [
    4 + (i * (W - 8)) / (v.length - 1),
    H - 4 - ((y - lo) / (hi - lo || 1)) * (H - 8),
  ])
})
const path = computed(() => pts.value.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' '))
</script>

<template>
  <svg v-if="pts.length" :viewBox="`0 0 ${W} ${H}`" :width="W" :height="H" role="img" :aria-label="label">
    <path :d="path" fill="none" stroke="var(--route)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
    <circle :cx="pts.at(-1)[0]" :cy="pts.at(-1)[1]" r="3.5" fill="var(--route)" />
  </svg>
</template>
