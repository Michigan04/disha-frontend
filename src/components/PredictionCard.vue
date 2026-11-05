<script setup>
import { computed, ref } from 'vue'
import { predict, gradeFor } from '../utils/predict'
import { GRADE_BANDS } from '../data/schemes'

// Predicted final score for a course in progress, why it is what it is,
// and a slider to see what more effort would change.
const props = defineProps({
  student: { type: Object, required: true },
  courseId: { type: String, required: true },
  attempt: { type: Object, required: true },
})

const base = computed(() => predict(props.student, props.courseId, props.attempt))
const effort = ref(props.attempt.assignmentAvg)
const what = computed(() => predict(props.student, props.courseId, props.attempt, effort.value))
const changed = computed(() => Math.abs(effort.value - props.attempt.assignmentAvg) >= 1)
const delta = computed(() => Math.round((what.value.score - base.value.score) * 10) / 10)

const bands = [...GRADE_BANDS].reverse().map((b, i, arr) => ({ ...b, max: arr[i + 1]?.min ?? 100 }))
const pass = computed(() => Math.round(base.value.score) >= 40)
const maxFactor = computed(() => Math.max(4, ...base.value.factors.map((f) => Math.abs(f.delta))))
const remainingWeeks = computed(() => props.attempt.weeks - props.attempt.week)

const STATUS = { known: 'so far', missed: 'not taken', upcoming: 'expected' }
</script>

<template>
  <section v-if="base" class="pred" aria-labelledby="pred-h">
    <div class="top">
      <div>
        <h2 id="pred-h">Predicted score</h2>
        <p class="muted">If you keep going as you are</p>
      </div>
      <div class="result">
        <span class="score num">{{ Math.round(base.score) }}<small>/100</small></span>
        <span class="grade" :class="{ fail: !pass, low: pass && Math.round(base.score) < 60 }">{{ base.grade }}</span>
      </div>
    </div>

    <!-- grade scale with the likely range -->
    <div class="scale" role="img" :aria-label="`Predicted ${base.score} out of 100, likely between ${base.low} and ${base.high}, grade ${base.grade}`">
      <div class="bands">
        <span v-for="b in bands" :key="b.grade" class="band" :class="{ u: b.grade === 'U' }" :style="{ left: `${b.min}%`, width: `${b.max - b.min}%` }">{{ b.grade }}</span>
      </div>
      <div class="track">
        <span class="range" :style="{ left: `${base.low}%`, width: `${base.high - base.low}%` }"></span>
        <span v-if="changed" class="mark ghost" :style="{ left: `${what.score}%` }"></span>
        <span class="mark" :style="{ left: `${base.score}%` }"></span>
      </div>
      <div class="ticks num"><span>0</span><span style="left: 40%">40</span><span style="left: 60%">60</span><span style="left: 80%">80</span><span style="left: 100%">100</span></div>
    </div>
    <p class="range-text muted">Likely between <strong>{{ Math.round(base.low) }}</strong> and <strong>{{ Math.round(base.high) }}</strong>. The range narrows as more results come in.</p>

    <!-- parts of the final score -->
    <ul class="parts">
      <li v-for="p in base.parts" :key="p.key" :class="p.status">
        <span class="w num">{{ p.weight }}%</span>
        <span class="pl">{{ p.label }}</span>
        <span class="pv num">{{ p.status === 'missed' ? 0 : Math.round(p.shown) }}</span>
        <span class="ps">{{ STATUS[p.status] }}</span>
      </li>
    </ul>

    <!-- what is moving the prediction -->
    <h3>Compared with a typical student</h3>
    <ul class="factors">
      <li v-for="f in base.factors" :key="f.label">
        <div class="fl">
          <span>{{ f.label }}</span>
          <span class="muted">{{ f.detail }}</span>
        </div>
        <div class="fbar" aria-hidden="true">
          <span class="axis"></span>
          <span class="fill" :class="f.delta < 0 ? 'neg' : 'pos'" :style="f.delta < 0 ? { right: '50%', width: `${(Math.abs(f.delta) / maxFactor) * 50}%` } : { left: '50%', width: `${(f.delta / maxFactor) * 50}%` }"></span>
        </div>
        <span class="fd num" :class="f.delta < 0 ? 'neg' : 'pos'">{{ f.delta > 0 ? '+' : '' }}{{ f.delta }}</span>
      </li>
    </ul>

    <!-- what if -->
    <div v-if="remainingWeeks > 0" class="whatif">
      <label for="effort">
        <strong>What if</strong> you average <strong class="num">{{ effort }}</strong> in the remaining {{ remainingWeeks }} weekly assignments?
      </label>
      <input id="effort" v-model.number="effort" type="range" min="0" max="100" step="1" />
      <p class="wi-result" aria-live="polite">
        <span>Predicted</span>
        <strong class="num">{{ Math.round(what.score) }}</strong>
        <span class="grade sm" :class="{ fail: Math.round(what.score) < 40, low: Math.round(what.score) >= 40 && Math.round(what.score) < 60 }">{{ gradeFor(Math.round(what.score)) }}</span>
        <span v-if="changed" class="chg num" :class="delta < 0 ? 'neg' : 'pos'">{{ delta > 0 ? '+' : '' }}{{ delta }}</span>
      </p>
    </div>

    <p class="note">Worked out from your scores so far and how students with similar scores did last term. Sample grading weights.</p>
  </section>
</template>

<style scoped>
.pred {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-m);
  padding: 22px 24px;
}

.top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.top .muted {
  font-size: 0.9375rem;
}

.result {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score {
  font-size: 2.75rem;
  line-height: 1;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.score small {
  font-size: 1rem;
  color: var(--muted);
  font-weight: 500;
  letter-spacing: 0;
}

.grade {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1.375rem;
  background: var(--ok-soft);
  color: var(--ok);
}

.grade.low {
  background: var(--low-soft);
  color: var(--low);
}

.grade.fail {
  background: var(--high-soft);
  color: var(--high);
}

.grade.sm {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  font-size: 1rem;
}

.scale {
  margin: 22px 0 6px;
}

.bands,
.track,
.ticks {
  position: relative;
}

.bands {
  height: 22px;
}

.band {
  position: absolute;
  top: 0;
  text-align: center;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--muted);
}

.track {
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--high-soft) 0 40%, var(--line) 40% 100%);
}

.range {
  position: absolute;
  top: 0;
  bottom: 0;
  border-radius: 999px;
  background: rgba(59, 63, 196, 0.28);
}

.mark {
  position: absolute;
  top: 50%;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--route);
  border: 3px solid var(--surface);
  box-shadow: 0 0 0 1px var(--route);
  transform: translate(-50%, -50%);
}

.mark.ghost {
  background: var(--surface);
  border: 3px dashed var(--route);
  box-shadow: none;
}

.ticks {
  height: 18px;
  font-size: 0.75rem;
  color: var(--muted);
}

.ticks span {
  position: absolute;
  top: 2px;
  transform: translateX(-50%);
}

.ticks span:first-child {
  transform: none;
}

.ticks span:last-child {
  transform: translateX(-100%);
}

.range-text {
  font-size: 0.9375rem;
}

.range-text strong {
  color: var(--ink);
}

.parts {
  list-style: none;
  margin: 18px 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.parts li {
  flex: 1 1 92px;
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-areas: 'w w' 'pl pl' 'pv ps';
  gap: 0 8px;
  padding: 10px 12px;
  border-radius: var(--r-s);
  background: var(--paper);
  align-items: baseline;
}

.w { grid-area: w; font-size: 0.75rem; color: var(--muted); }
.pl { grid-area: pl; font-size: 0.875rem; font-weight: 500; line-height: 1.25; margin-bottom: 4px; }
.pv { grid-area: pv; font-size: 1.375rem; font-weight: 600; }
.ps { grid-area: ps; font-size: 0.75rem; color: var(--muted); }

.parts .upcoming {
  background: transparent;
  border: 1px dashed var(--line-2);
}

.parts .upcoming .pv {
  color: var(--ink-2);
}

.parts .missed {
  background: var(--high-soft);
}

.parts .missed .pv,
.parts .missed .ps {
  color: var(--high);
}

h3 {
  margin: 22px 0 10px;
  font-size: 1rem;
}

.factors {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.factors li {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr) 48px;
  gap: 12px;
  align-items: center;
}

.fl {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  font-size: 0.9375rem;
}

.fl .muted {
  font-size: 0.8125rem;
}

.fbar {
  position: relative;
  height: 12px;
}

.axis {
  position: absolute;
  left: 50%;
  top: -3px;
  bottom: -3px;
  width: 2px;
  background: var(--line-2);
}

.fill {
  position: absolute;
  top: 0;
  bottom: 0;
  border-radius: 3px;
}

.fill.pos { background: var(--ok); }
.fill.neg { background: var(--high); }

.fd {
  text-align: right;
  font-weight: 600;
}

.pos { color: var(--ok); }
.neg { color: var(--high); }

.whatif {
  margin-top: 22px;
  padding: 16px 18px;
  border-radius: var(--r-m);
  background: var(--route-soft);
}

.whatif label {
  display: block;
  margin-bottom: 8px;
}

.whatif input {
  width: 100%;
  accent-color: var(--route);
}

.wi-result {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 6px;
}

.wi-result strong {
  font-size: 1.5rem;
  font-weight: 600;
}

.chg {
  font-weight: 600;
}

@media (max-width: 560px) {
  .top {
    flex-direction: column;
  }
  .factors li {
    grid-template-columns: 1fr 48px;
  }
  .fbar {
    grid-column: 1 / -1;
    grid-row: 2;
  }
}
</style>
