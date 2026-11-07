<script setup>
import { computed } from 'vue'

// One bar split into coloured parts, each with its own count.
const props = defineProps({
  parts: { type: Array, required: true }, // [{ value, cls, label }]
  max: { type: Number, default: null },
  height: { type: Number, default: 12 },
  showValues: { type: Boolean, default: false },
})
const total = computed(() => props.parts.reduce((s, p) => s + p.value, 0))
const scale = computed(() => props.max || total.value || 1)
const label = computed(() => props.parts.filter((p) => p.value).map((p) => `${p.label}: ${p.value}`).join(', '))
</script>

<template>
  <div class="stack" role="img" :aria-label="label" :style="{ height: `${height}px` }">
    <span
      v-for="p in parts.filter((x) => x.value)"
      :key="p.label"
      class="seg"
      :class="p.cls"
      :style="{ width: `${(p.value / scale) * 100}%` }"
      :title="`${p.label}: ${p.value}`"
    ><template v-if="showValues && height >= 18">{{ p.value }}</template></span>
  </div>
</template>

<style scoped>
.stack {
  display: flex;
  gap: 2px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--line);
}

.seg {
  display: grid;
  place-items: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: #fff;
  min-width: 3px;
}

.seg.high { background: var(--viz-critical); }
.seg.low { background: var(--viz-warning); color: var(--ink); }
.seg.ok,
.seg.ontrack { background: var(--viz-good); }
.seg.active,
.seg.route { background: var(--viz-active); }
.seg.pred { background: var(--viz-pred); }
.seg.muted { background: var(--viz-neutral); color: var(--ink); }
</style>
