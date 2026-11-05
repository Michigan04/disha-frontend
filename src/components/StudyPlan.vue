<script setup>
import { computed, reactive, ref } from 'vue'
import Icon from './Icon.vue'

// A week-by-week plan for clearing a course the student failed before.
// Ticked tasks are remembered in this browser only.
const props = defineProps({
  plan: { type: Object, required: true },
  insight: { type: Object, default: null },
  currentWeek: { type: Number, required: true },
  storageKey: { type: String, required: true },
})

function load() {
  try {
    const saved = JSON.parse(localStorage.getItem(props.storageKey) || 'null')
    if (Array.isArray(saved)) return saved
  } catch {
    /* storage unavailable */
  }
  // Default: tasks in past weeks are done.
  return props.plan.weeks.filter((w) => w.w < props.currentWeek).flatMap((w) => w.tasks.map((_, i) => `${w.w}-${i}`))
}

const done = reactive(new Set(load()))
const open = ref(props.currentWeek)

function toggle(id) {
  done.has(id) ? done.delete(id) : done.add(id)
  try {
    localStorage.setItem(props.storageKey, JSON.stringify([...done]))
  } catch {
    /* storage unavailable: ticks last for this visit */
  }
}

const total = computed(() => props.plan.weeks.reduce((s, w) => s + w.tasks.length, 0))
const doneCount = computed(() => done.size)
const pct = computed(() => Math.round((doneCount.value / total.value) * 100))
const weekDone = (w) => w.tasks.every((_, i) => done.has(`${w.w}-${i}`))
const weekCount = (w) => w.tasks.filter((_, i) => done.has(`${w.w}-${i}`)).length
const passPct = computed(() => (props.insight ? Math.round((props.insight.passedNext / props.insight.failedOnce) * 100) : null))

const R = 30
const C = 2 * Math.PI * R
</script>

<template>
  <div class="plan">
    <div class="head">
      <div class="ring" role="img" :aria-label="`${doneCount} of ${total} tasks done`">
        <svg viewBox="0 0 72 72" width="88" height="88">
          <circle cx="36" cy="36" :r="R" fill="none" stroke="var(--line)" stroke-width="8" />
          <circle cx="36" cy="36" :r="R" fill="none" stroke="var(--route)" stroke-width="8" stroke-linecap="round"
            :stroke-dasharray="C" :stroke-dashoffset="C * (1 - pct / 100)" transform="rotate(-90 36 36)" />
        </svg>
        <span class="pct num">{{ pct }}%</span>
      </div>
      <dl class="facts">
        <div><dt>Goal</dt><dd>{{ plan.goal }}</dd></div>
        <div><dt>Time</dt><dd>About {{ plan.hoursPerWeek }} hours a week</dd></div>
        <div><dt>Done</dt><dd class="num">{{ doneCount }} of {{ total }} tasks</dd></div>
      </dl>
      <div v-if="insight" class="proof">
        <span class="pv num">{{ passPct }}%</span>
        <span>of {{ insight.failedOnce }} students who failed once passed next time with a plan like this</span>
      </div>
    </div>

    <ol class="weeks">
      <li v-for="w in plan.weeks" :key="w.w" :class="{ past: w.w < currentWeek, now: w.w === currentWeek, complete: weekDone(w), isopen: open === w.w }">
        <button type="button" class="wk" :aria-expanded="open === w.w" @click="open = open === w.w ? null : w.w">
          <span class="badge num">
            <Icon v-if="weekDone(w)" name="check" :size="16" />
            <template v-else>{{ w.w }}</template>
          </span>
          <span class="wt">
            <strong>Week {{ w.w }}<template v-if="w.w === currentWeek"> (this week)</template></strong>
            <span>{{ w.focus }}</span>
          </span>
          <span class="meta">
            <span v-if="w.checkpoint" class="chip high">{{ w.checkpoint }}</span>
            <span class="chip">{{ w.hours }} h</span>
            <span class="count num">{{ weekCount(w) }}/{{ w.tasks.length }}</span>
            <Icon name="chevron" :size="18" class="chev" />
          </span>
        </button>
        <ul v-if="open === w.w" class="tasks">
          <li v-for="(t, i) in w.tasks" :key="t">
            <label>
              <input type="checkbox" :checked="done.has(`${w.w}-${i}`)" @change="toggle(`${w.w}-${i}`)" />
              <span>{{ t }}</span>
            </label>
          </li>
        </ul>
      </li>
    </ol>

    <section v-if="insight" class="helped" aria-labelledby="helped-h">
      <h3 id="helped-h">What helped students who failed once</h3>
      <ul>
        <li v-for="h in insight.whatHelped" :key="h.text">
          <div class="ht"><span>{{ h.text }}</span><strong class="num">{{ h.share }}%</strong></div>
          <div class="meter"><span :style="{ width: `${h.share}%` }"></span></div>
        </li>
      </ul>
    </section>
    <p class="note">Ticks are saved in this browser. Plan built from anonymised records of past students; figures are sample data.</p>
  </div>
</template>

<style scoped>
.plan {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.head {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 20px;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-m);
  padding: 18px 20px;
}

.ring {
  position: relative;
  width: 88px;
  height: 88px;
}

.ring circle:last-child {
  transition: stroke-dashoffset 0.4s ease;
}

.pct {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  font-weight: 600;
  font-size: 1.125rem;
}

.facts {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.facts div {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: 8px;
}

.facts dt {
  color: var(--muted);
  font-size: 0.875rem;
  padding-top: 2px;
}

.facts dd {
  margin: 0;
  font-weight: 500;
}

.proof {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 260px;
  padding: 12px 14px;
  border-radius: var(--r-m);
  background: var(--ok-soft);
  font-size: 0.875rem;
  line-height: 1.35;
}

.proof .pv {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--ok);
}

.weeks {
  list-style: none;
  margin: 0;
  padding: 0;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-m);
  overflow: hidden;
}

.weeks > li + li {
  border-top: 1px solid var(--line);
}

.wk {
  width: 100%;
  display: grid;
  grid-template-columns: 34px 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 12px 18px;
  border: 0;
  background: none;
  text-align: left;
  cursor: pointer;
}

.wk:hover {
  background: var(--paper);
}

.now > .wk {
  background: var(--route-soft);
}

.badge {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-weight: 600;
  font-size: 0.9375rem;
  background: var(--paper);
  color: var(--ink-2);
}

.now .badge {
  background: var(--route);
  color: #fff;
}

.complete .badge {
  background: var(--ok-soft);
  color: var(--ok);
}

.wt {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  min-width: 0;
}

.wt strong {
  font-weight: 600;
}

.wt span {
  color: var(--ink-2);
}

.past .wt span {
  color: var(--muted);
}

.meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.count {
  font-size: 0.875rem;
  color: var(--muted);
  min-width: 28px;
  text-align: right;
}

.chev {
  color: var(--muted);
  transition: transform 0.2s;
}

.isopen .chev {
  transform: rotate(90deg);
}

.tasks {
  list-style: none;
  margin: 0;
  padding: 4px 18px 16px 66px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tasks label {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  cursor: pointer;
  padding: 4px 0;
}

.tasks input {
  width: 18px;
  height: 18px;
  margin-top: 3px;
  accent-color: var(--route);
  flex: none;
}

.tasks input:checked + span {
  color: var(--muted);
  text-decoration: line-through;
}

.helped {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-m);
  padding: 18px 20px;
}

.helped h3 {
  font-size: 1rem;
  margin-bottom: 12px;
}

.helped ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
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

@media (max-width: 760px) {
  .head {
    grid-template-columns: auto 1fr;
  }
  .proof {
    grid-column: 1 / -1;
    max-width: none;
  }
  .wk {
    grid-template-columns: 34px 1fr;
  }
  .meta {
    grid-column: 2;
    flex-wrap: wrap;
  }
  .tasks {
    padding-left: 18px;
  }
}
</style>
