<script setup>
import { computed, onMounted, ref } from 'vue'
import { termAfter } from '../utils/dates'

// The degree drawn as a route: every term is a station, milestones are marked stops,
// and the student's current term is "You are here".
const props = defineProps({
  limit: { type: Number, required: true },
  current: { type: Number, required: true },
  firstTerm: { type: String, required: true },
  milestones: { type: Array, required: true },
  levelLabel: { type: String, required: true },
})

const stations = computed(() =>
  Array.from({ length: props.limit }, (_, i) => {
    const n = i + 1
    return {
      n,
      label: termAfter(props.firstTerm, i),
      state: n < props.current ? 'past' : n === props.current ? 'current' : 'future',
      milestone: props.milestones.find((m) => m.byTerm === n) || null,
    }
  }),
)

const target = computed(() => (props.limit > 1 ? (props.current - 1) / (props.limit - 1) : 0))
const shown = ref(0)
const wrap = ref(null)
onMounted(() => {
  requestAnimationFrame(() => { shown.value = target.value })
  // On narrow screens the route scrolls sideways: bring "You are here" into view.
  const el = wrap.value?.querySelector('.station.current')
  if (el && wrap.value.scrollWidth > wrap.value.clientWidth) {
    wrap.value.scrollLeft = el.offsetLeft - wrap.value.clientWidth / 2 + el.clientWidth / 2
  }
})

const milestoneWord = { met: 'Done', due: 'Next', missed: 'Missed', upcoming: 'Later' }
</script>

<template>
  <div ref="wrap" class="route-wrap">
    <p class="sr-only">
      {{ levelLabel }} route: term {{ current }} of {{ limit }}.
      <template v-for="m in milestones" :key="m.byTerm">Milestone {{ m.text }} by term {{ m.byTerm }}: {{ milestoneWord[m.state] }}. </template>
    </p>
    <ol class="route" :style="{ '--n': limit, '--fill': shown }" aria-hidden="true">
      <li v-for="s in stations" :key="s.n" class="station" :class="s.state">
        <div class="flag-slot">
          <span v-if="s.milestone" class="flag" :class="s.milestone.state">
            <strong>{{ s.milestone.courses }} courses</strong>
            <em v-if="s.milestone.projects">+ {{ s.milestone.projects }} {{ s.milestone.projects === 1 ? 'project' : 'projects' }}</em>
            <span>{{ milestoneWord[s.milestone.state] }}</span>
          </span>
        </div>
        <span class="dot" :class="{ stop: s.milestone }"></span>
        <span class="tn">Term {{ s.n }}</span>
        <span class="tl">{{ s.label }}</span>
        <span v-if="s.state === 'current'" class="here">You are here</span>
      </li>
    </ol>
  </div>
</template>

<style scoped>
.route-wrap {
  position: relative;
  overflow-x: auto;
  padding: 4px 2px 8px;
  scrollbar-width: thin;
}

.route {
  --dot-y: 81px;
  position: relative;
  /* offsetLeft of stations is measured against this list */
  display: grid;
  grid-template-columns: repeat(var(--n), minmax(68px, 1fr));
  list-style: none;
  margin: 0;
  padding: 0;
  min-width: 640px;
}

/* the line itself */
.route::before,
.route::after {
  content: '';
  position: absolute;
  top: calc(var(--dot-y) - 2px);
  left: calc(100% / var(--n) / 2);
  height: 4px;
  border-radius: 4px;
}

.route::before {
  right: calc(100% / var(--n) / 2);
  background: repeating-linear-gradient(90deg, var(--line-2) 0 10px, transparent 10px 16px);
}

.route::after {
  width: calc((100% - 100% / var(--n)) * var(--fill));
  background: var(--route);
  transition: width 1.1s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.station {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  z-index: 1;
}

.flag-slot {
  height: 74px;
  display: flex;
  align-items: flex-end;
  padding-bottom: 6px;
}

.flag {
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.2;
  padding: 5px 10px 6px;
  border-radius: var(--r-s);
  font-size: 0.8125rem;
  background: var(--surface);
  border: 1px solid var(--line);
  white-space: nowrap;
}

.flag strong {
  font-weight: 600;
  font-size: 0.875rem;
}

.flag span {
  color: var(--muted);
}

.flag em {
  font-style: normal;
  font-size: 0.8125rem;
  color: var(--ink-2);
}

.flag.met {
  border-color: transparent;
  background: var(--ok-soft);
}
.flag.met span {
  color: var(--ok);
}
.flag.due {
  border-color: var(--route);
}
.flag.due span {
  color: var(--route-ink);
  font-weight: 500;
}
.flag.missed {
  background: var(--high-soft);
  border-color: transparent;
}
.flag.missed span {
  color: var(--high);
}

.dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--surface);
  border: 3px solid var(--line-2);
  margin: 0 0 10px;
}

.dot.stop {
  border-radius: 4px;
  transform: rotate(45deg);
}

.past .dot {
  background: var(--route);
  border-color: var(--route);
}

.current .dot {
  width: 26px;
  height: 26px;
  margin-top: -6px;
  margin-bottom: 4px;
  border: 4px solid var(--route);
  background: var(--surface);
  box-shadow: 0 0 0 5px var(--route-soft);
}

.current .dot.stop {
  transform: rotate(45deg);
}

.tn {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--ink-2);
}

.future .tn {
  color: var(--muted);
  font-weight: 500;
}

.tl {
  font-size: 0.8125rem;
  color: var(--muted);
}

.here {
  margin-top: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #fff;
  background: var(--route);
  border-radius: 999px;
  padding: 1px 10px;
  white-space: nowrap;
}
</style>
