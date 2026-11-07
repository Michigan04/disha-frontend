<script setup>
import { computed } from 'vue'
import Icon from './Icon.vue'

// How students who took the course last term got through it: effort, hard weeks, habits.
const props = defineProps({
  guide: { type: Object, required: true },
  currentWeek: { type: Number, default: null },
})

const heavy = computed(() => props.guide.weeks.filter((w) => w.load === 3))
const thisWeek = computed(() => props.guide.weeks.find((w) => w.w === props.currentWeek))
const maxHours = computed(() => props.guide.hours.top)
const LOAD = { 1: 'Light', 2: 'Medium', 3: 'Heavy' }
const RES_ICON = { practice: 'oppe', video: 'video', notes: 'courses' }
const effort = computed(() => [
  { label: 'Top grades (S, A)', hours: props.guide.hours.top, cls: 'top' },
  { label: 'Passed', hours: props.guide.hours.passed, cls: 'pass' },
  { label: 'Did not pass', hours: props.guide.hours.notPassed, cls: 'fail' },
])
</script>

<template>
  <div class="guide">
    <div class="tiles">
      <div class="tile">
        <span class="v num">{{ guide.passRate }}%</span>
        <span class="l">passed in {{ guide.lastTerm }}</span>
        <span class="s muted">{{ guide.students.toLocaleString('en-IN') }} students</span>
      </div>
      <div class="tile">
        <span class="v num">{{ guide.hours.passed }}<small> h</small></span>
        <span class="l">a week, by students who passed</span>
        <span class="s muted">Top scorers: {{ guide.hours.top }} h</span>
      </div>
      <div class="tile">
        <span class="v num">{{ heavy.length }}</span>
        <span class="l">heavy weeks to plan for</span>
        <span class="s muted">Weeks {{ heavy.map((w) => w.w).join(', ') }}</span>
      </div>
    </div>

    <section class="block" aria-labelledby="wk-h">
      <div class="block-head">
        <h3 id="wk-h">Week by week</h3>
        <span class="legend"><i class="l1"></i>Light <i class="l2"></i>Medium <i class="l3"></i>Heavy</span>
      </div>
      <ol class="strip">
        <li v-for="w in guide.weeks" :key="w.w" :class="[`l${w.load}`, { now: w.w === currentWeek }]" :title="`Week ${w.w}: ${w.topic} (${LOAD[w.load]})`">
          <span class="wn num">{{ w.w }}</span>
          <span class="sr-only">Week {{ w.w }}: {{ w.topic }}, {{ LOAD[w.load] }}</span>
        </li>
      </ol>
      <div class="heavy">
        <div v-if="thisWeek" class="this">
          <span class="chip calm">This week</span>
          <strong>Week {{ thisWeek.w }}: {{ thisWeek.topic }}</strong>
          <span class="muted">{{ LOAD[thisWeek.load] }}</span>
        </div>
        <ul>
          <li v-for="w in heavy" :key="w.w"><span class="dot l3"></span>Week {{ w.w }}: {{ w.topic }}</li>
        </ul>
      </div>
    </section>

    <div class="two">
      <section class="block" aria-labelledby="ef-h">
        <h3 id="ef-h">Hours a week that paid off</h3>
        <ul class="effort">
          <li v-for="e in effort" :key="e.label">
            <span class="el">{{ e.label }}</span>
            <span class="eb"><span :class="e.cls" :style="{ width: `${(e.hours / maxHours) * 100}%` }"></span></span>
            <strong class="num">{{ e.hours }} h</strong>
          </li>
        </ul>
      </section>

      <section class="block" aria-labelledby="sl-h">
        <h3 id="sl-h">Common slip-ups</h3>
        <ul class="slips">
          <li v-for="s in guide.slips" :key="s"><Icon name="cross" :size="16" />{{ s }}</li>
        </ul>
      </section>
    </div>

    <section class="block" aria-labelledby="hb-h">
      <h3 id="hb-h">What students who passed did</h3>
      <ul class="habits">
        <li v-for="h in guide.habits" :key="h.text">
          <div class="ht"><span>{{ h.text }}</span><strong class="num">{{ h.share }}%</strong></div>
          <div class="meter"><span :style="{ width: `${h.share}%` }"></span></div>
        </li>
      </ul>
    </section>

    <section class="block" aria-labelledby="rs-h">
      <h3 id="rs-h">Resources they used</h3>
      <ul class="res">
        <li v-for="r in guide.resources" :key="r.title"><span class="ri"><Icon :name="RES_ICON[r.type]" :size="18" /></span>{{ r.title }}</li>
      </ul>
    </section>

    <p class="note">Anonymised records from last term. Figures shown here are sample data.</p>
  </div>
</template>

<style scoped>
.guide {
  display: flex;
  flex-direction: column;
  gap: 20px;
  --c-light: #e6f2ee;
  --c-mid: #bcdcd3;
  --c-heavy: #7db3a6;
}

.tiles {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.tile {
  display: flex;
  flex-direction: column;
  padding: 20px 22px;
  border-radius: var(--r-m);
  background: var(--calm-soft);
  border: 1px solid var(--calm-light);
  line-height: 1.3;
}

.v {
  font-size: 2rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--calm-ink);
}

.v small {
  font-size: 1rem;
}

.l {
  font-weight: 500;
}

.s {
  font-size: 0.875rem;
  margin-top: 2px;
}

.block {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-m);
  padding: 22px 24px;
}

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}

h3 {
  font-size: 1rem;
  margin-bottom: 12px;
}

.legend {
  font-size: 0.8125rem;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend i {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  margin-left: 6px;
  box-shadow: inset 0 0 0 1px rgba(43, 95, 86, 0.12);
}

.l1 { background: var(--c-light); }
.l2 { background: var(--c-mid); }
.l3 { background: var(--c-heavy); }

.strip {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 6px;
}

.strip li {
  height: 46px;
  border-radius: 8px;
  display: grid;
  place-items: end center;
  padding-bottom: 4px;
  position: relative;
}

.strip .wn {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--ink-2);
}

.strip .l3 .wn {
  color: var(--ink);
}

.strip li.now {
  outline: 2px solid var(--calm-ink);
  outline-offset: 3px;
}

.heavy {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 12px 24px;
  margin-top: 14px;
}

.this {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
}

.chip.calm {
  background: var(--calm-light);
  color: var(--calm-ink);
}

.this strong {
  font-weight: 600;
}

.heavy ul {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 0.9375rem;
  color: var(--ink-2);
}

.heavy li {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

.two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.effort {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.effort li {
  display: grid;
  grid-template-columns: 130px 1fr 44px;
  gap: 10px;
  align-items: center;
  font-size: 0.9375rem;
}

.eb {
  height: 12px;
  border-radius: 999px;
  background: var(--calm-soft);
  overflow: hidden;
}

.eb span {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.eb .top { background: var(--c-heavy); }
.eb .pass { background: var(--c-mid); }
.eb .fail { background: #d9d6cf; }

.effort strong {
  text-align: right;
  font-weight: 600;
}

.slips {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slips li {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 0.9375rem;
}

.slips svg {
  flex: none;
  margin-top: 3px;
  color: var(--clay);
}

.habits {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.habits .meter {
  height: 8px;
  background: var(--calm-soft);
}

.habits .meter > span {
  background: #5d9c8e;
}

.ht {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}

.ht strong {
  font-weight: 600;
}

.res {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}

.res li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--r-s);
  background: var(--calm-soft);
  font-size: 0.9375rem;
}

.ri {
  flex: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: var(--surface);
  color: var(--calm);
}

@media (max-width: 760px) {
  .tiles,
  .two {
    grid-template-columns: 1fr;
  }
  .tiles {
    gap: 8px;
  }
  .tile {
    display: grid;
    grid-template-columns: 72px 1fr;
    grid-template-areas: 'v l' 'v s';
    column-gap: 10px;
    align-items: center;
    padding: 12px 14px;
  }
  .tile .v { grid-area: v; }
  .tile .l { grid-area: l; align-self: end; }
  .tile .s { grid-area: s; align-self: start; }
  .strip li {
    height: 36px;
  }
}
</style>
