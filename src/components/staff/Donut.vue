<script setup>
import { computed, ref, useId } from 'vue'

// Part-to-whole pie ring. Each part can have a legend row with its count and share, so
// colour is never the only way to tell parts apart. Parts marked `hatch` get diagonal
// stripes as a second cue (for two parts that share a status colour).
const props = defineProps({
  parts: { type: Array, required: true }, // [{ key, label, value, color, hatch?, to? }]
  center: { type: [String, Number], default: '' },
  centerSub: { type: String, default: '' },
  size: { type: Number, default: 176 },
  thickness: { type: Number, default: 26 },
  legend: { type: Boolean, default: true },
})

const VB = 200
const RM = computed(() => 96 - props.thickness / 2 - 4) // radius to the middle of the ring
const uid = useId()

const total = computed(() => props.parts.reduce((s, p) => s + p.value, 0))
const pct = (v) => (total.value ? Math.round((v / total.value) * 100) : 0)

const arcs = computed(() => {
  const shown = props.parts.filter((p) => p.value > 0)
  if (!total.value) return []
  const gap = shown.length > 1 ? 2.5 / RM.value : 0 // 2px-ish surface gap between parts
  let a = -Math.PI / 2
  return shown.map((p) => {
    const span = (p.value / total.value) * Math.PI * 2
    const a0 = a + gap / 2
    const a1 = a + span - gap / 2
    a += span
    return { ...p, d: arcPath(a0, a1), mid: (a0 + a1) / 2, pid: `h-${uid}-${p.key}` }
  })
})

function arcPath(a0, a1) {
  if (a1 - a0 >= Math.PI * 2 - 0.001) a1 = a0 + Math.PI * 2 - 0.001
  const c = VB / 2
  const r = RM.value
  const x0 = c + r * Math.cos(a0)
  const y0 = c + r * Math.sin(a0)
  const x1 = c + r * Math.cos(a1)
  const y1 = c + r * Math.sin(a1)
  const large = a1 - a0 > Math.PI ? 1 : 0
  return `M${x0.toFixed(2)} ${y0.toFixed(2)} A${r} ${r} 0 ${large} 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`
}

const hover = ref(null)
const tip = computed(() => {
  const a = arcs.value.find((x) => x.key === hover.value)
  if (!a) return null
  const c = VB / 2
  const r = RM.value
  return { ...a, left: ((c + r * Math.cos(a.mid)) / VB) * 100, top: ((c + r * Math.sin(a.mid)) / VB) * 100 }
})
const desc = computed(() => props.parts.map((p) => `${p.label}: ${p.value} (${pct(p.value)}%)`).join(', '))
const small = computed(() => props.size < 130)
const paint = (a) => (a.hatch ? `url(#${a.pid})` : a.color)
</script>

<template>
  <div class="donut" :class="{ 'no-legend': !legend }">
    <div class="ring" :class="{ small }" :style="{ width: `${size}px`, height: `${size}px` }">
      <svg :viewBox="`0 0 ${VB} ${VB}`" role="img" :aria-label="desc">
        <defs>
          <pattern v-for="a in arcs.filter((x) => x.hatch)" :id="a.pid" :key="a.pid" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width="8" height="8" :style="{ fill: a.color }" />
            <rect width="3" height="8" fill="var(--surface)" opacity="0.55" />
          </pattern>
        </defs>
        <circle :cx="VB / 2" :cy="VB / 2" :r="RM" fill="none" class="track" :stroke-width="thickness" />
        <path
          v-for="a in arcs"
          :key="a.key"
          :d="a.d"
          fill="none"
          :style="{ stroke: paint(a) }"
          :stroke-width="hover === a.key ? thickness + 6 : thickness"
          class="arc"
          :class="{ dim: hover && hover !== a.key }"
          tabindex="0"
          :aria-label="`${a.label}: ${a.value}, ${pct(a.value)}%`"
          @pointerenter="hover = a.key"
          @pointerleave="hover = null"
          @focus="hover = a.key"
          @blur="hover = null"
        />
      </svg>
      <div class="mid">
        <span class="mv num">{{ center }}</span>
        <span v-if="centerSub" class="ms">{{ centerSub }}</span>
      </div>
      <div v-if="tip" class="tip" :style="{ left: `${tip.left}%`, top: `${tip.top}%` }" role="tooltip">
        <strong class="num">{{ tip.value }}</strong> <span>{{ tip.label }}, {{ pct(tip.value) }}%</span>
      </div>
    </div>

    <ul v-if="legend" class="legend">
      <li v-for="p in parts" :key="p.key" :class="{ on: hover === p.key }" @pointerenter="hover = p.key" @pointerleave="hover = null">
        <component :is="p.to ? 'RouterLink' : 'span'" :to="p.to" class="row">
          <i :class="{ hatch: p.hatch }" :style="{ background: p.color }"></i>
          <span class="lab">{{ p.label }}</span>
          <strong class="num">{{ p.value }}</strong>
          <span class="pc num">{{ pct(p.value) }}%</span>
        </component>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.donut {
  display: flex;
  align-items: center;
  gap: 28px;
}

.donut.no-legend {
  display: inline-flex;
}

.ring {
  position: relative;
  flex: none;
}

.ring svg {
  width: 100%;
  height: 100%;
  display: block;
  overflow: visible;
}

.track {
  stroke: var(--viz-track);
}

.arc {
  cursor: pointer;
  transition: stroke-width 0.15s, opacity 0.15s;
  outline: none;
}

.arc.dim {
  opacity: 0.4;
}

.mid {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  line-height: 1.1;
  text-align: center;
}

.mv {
  font-size: 2rem;
  font-weight: 700;
  color: var(--ink);
}

.ms {
  font-size: 0.8125rem;
  color: var(--muted);
  margin-top: 2px;
}

.small .mv {
  font-size: 1.25rem;
}

.small .ms {
  font-size: 0.6875rem;
  margin-top: 0;
}

.tip {
  position: absolute;
  transform: translate(-50%, -130%);
  white-space: nowrap;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--ink);
  color: #fff;
  font-size: 0.8125rem;
  pointer-events: none;
  box-shadow: 0 4px 14px rgba(28, 25, 23, 0.18);
  z-index: 3;
}

.tip strong {
  font-size: 0.9375rem;
}

.tip span {
  color: var(--on-dark-2);
}

.legend {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.row {
  display: grid;
  grid-template-columns: 12px minmax(0, 1fr) auto 44px;
  gap: 10px;
  align-items: center;
  padding: 7px 10px;
  border-radius: var(--r-s);
  color: var(--ink);
  text-decoration: none;
  font-size: 0.9375rem;
}

.legend li.on .row,
a.row:hover {
  background: var(--paper);
}

.row i {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.row i.hatch {
  background-image: repeating-linear-gradient(135deg, transparent 0 2px, rgba(255, 255, 255, 0.55) 2px 4px) !important;
}

.row strong {
  font-weight: 600;
}

.pc {
  text-align: right;
  color: var(--muted);
  font-size: 0.875rem;
}

@media (max-width: 520px) {
  .donut:not(.no-legend) {
    flex-direction: column;
    align-items: stretch;
  }
  .ring {
    align-self: center;
  }
}
</style>
