<script setup>
import { computed, ref } from 'vue'

// Part-to-whole ring for a few parts (three risk levels). Each part has a legend row
// with its count and share, so colour is never the only way to tell them apart.
const props = defineProps({
  parts: { type: Array, required: true }, // [{ key, label, value, color, to? }]
  center: { type: [String, Number], default: '' },
  centerSub: { type: String, default: '' },
  size: { type: Number, default: 176 },
})

const VB = 200
const RM = 78 // radius to the middle of the ring
const TH = 24 // ring thickness
const GAP = 2.5 / RM // 2px-ish surface gap between parts, in radians

const total = computed(() => props.parts.reduce((s, p) => s + p.value, 0) || 1)
const pct = (v) => Math.round((v / total.value) * 100)

const arcs = computed(() => {
  let a = -Math.PI / 2
  const shown = props.parts.filter((p) => p.value > 0)
  return shown.map((p) => {
    const span = (p.value / total.value) * Math.PI * 2
    const a0 = a + (shown.length > 1 ? GAP / 2 : 0)
    const a1 = a + span - (shown.length > 1 ? GAP / 2 : 0)
    a += span
    const mid = (a0 + a1) / 2
    return { ...p, d: arcPath(a0, a1), mid }
  })
})

function arcPath(a0, a1) {
  if (a1 - a0 >= Math.PI * 2 - 0.001) a1 = a0 + Math.PI * 2 - 0.001
  const c = VB / 2
  const x0 = c + RM * Math.cos(a0)
  const y0 = c + RM * Math.sin(a0)
  const x1 = c + RM * Math.cos(a1)
  const y1 = c + RM * Math.sin(a1)
  const large = a1 - a0 > Math.PI ? 1 : 0
  return `M${x0.toFixed(2)} ${y0.toFixed(2)} A${RM} ${RM} 0 ${large} 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`
}

const hover = ref(null)
const tip = computed(() => {
  const a = arcs.value.find((x) => x.key === hover.value)
  if (!a) return null
  const c = VB / 2
  const r = RM + TH / 2 + 6
  return { ...a, left: ((c + r * Math.cos(a.mid)) / VB) * 100, top: ((c + r * Math.sin(a.mid)) / VB) * 100 }
})
const desc = computed(() => props.parts.map((p) => `${p.label}: ${p.value} (${pct(p.value)}%)`).join(', '))
</script>

<template>
  <div class="donut">
    <div class="ring" :style="{ width: `${size}px`, height: `${size}px` }">
      <svg :viewBox="`0 0 ${VB} ${VB}`" role="img" :aria-label="desc">
        <circle :cx="VB / 2" :cy="VB / 2" :r="RM" fill="none" stroke="var(--line)" :stroke-width="TH" v-if="!arcs.length" />
        <path
          v-for="a in arcs"
          :key="a.key"
          :d="a.d"
          fill="none"
          :stroke="a.color"
          :stroke-width="hover === a.key ? TH + 6 : TH"
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
        <span class="ms">{{ centerSub }}</span>
      </div>
      <div v-if="tip" class="tip" :style="{ left: `${tip.left}%`, top: `${tip.top}%` }" role="tooltip">
        <strong class="num">{{ tip.value }}</strong> <span>{{ tip.label }}, {{ pct(tip.value) }}%</span>
      </div>
    </div>

    <ul class="legend">
      <li v-for="p in parts" :key="p.key" :class="{ on: hover === p.key }" @pointerenter="hover = p.key" @pointerleave="hover = null">
        <component :is="p.to ? 'RouterLink' : 'span'" :to="p.to" class="row">
          <i :style="{ background: p.color }"></i>
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

.arc {
  cursor: pointer;
  transition: stroke-width 0.15s, opacity 0.15s;
  outline: none;
}

.arc.dim {
  opacity: 0.45;
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
}

.mv {
  font-size: 2rem;
  font-weight: 600;
  color: var(--ink);
}

.ms {
  font-size: 0.8125rem;
  color: var(--muted);
  margin-top: 2px;
}

.tip {
  position: absolute;
  transform: translate(-50%, -50%);
  white-space: nowrap;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--ink);
  color: #fff;
  font-size: 0.8125rem;
  pointer-events: none;
  box-shadow: 0 4px 14px rgba(20, 26, 50, 0.18);
  z-index: 2;
}

.tip strong {
  font-size: 0.9375rem;
}

.tip span {
  color: #d5d8e6;
}

.legend {
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.row {
  display: grid;
  grid-template-columns: 12px minmax(0, 1fr) auto 44px;
  gap: 10px;
  align-items: center;
  padding: 8px 10px;
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

.row strong {
  font-weight: 600;
}

.pc {
  text-align: right;
  color: var(--muted);
  font-size: 0.875rem;
}

@media (max-width: 520px) {
  .donut {
    flex-direction: column;
    align-items: stretch;
  }
  .ring {
    align-self: center;
  }
}
</style>
