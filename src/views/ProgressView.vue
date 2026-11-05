<script setup>
import { computed } from 'vue'
import { useStudentStore } from '../stores/student'
import GpaChart from '../components/GpaChart.vue'
import { COURSES } from '../data/courses'
import { isFail } from '../utils/progress'

const store = useStudentStore()
const left = computed(() => store.rule.limitTerms - store.termNumber)
const used = computed(() => (store.termNumber / store.rule.limitTerms) * 100)
const doneTotal = computed(() => store.done.courses + store.done.projects)

const STATE_TEXT = { met: 'Met', due: 'Coming up', missed: 'Missed', upcoming: 'Later' }
const STATE_CLS = { met: 'ok', due: 'route', missed: 'high', upcoming: '' }

function result(a) {
  if (a.inProgress) return 'In progress'
  return isFail(a) ? 'Not cleared' : a.grade
}
</script>

<template>
  <div class="page">
    <header class="page-head">
      <h1>CGPA and terms</h1>
      <p>Your grades, how your CGPA has changed, and how much time you have for each milestone.</p>
    </header>

    <div class="top">
      <section class="panel cg" aria-labelledby="cg-h">
        <h2 id="cg-h">CGPA</h2>
        <p class="big num">{{ store.cgpa?.toFixed(2) ?? 'None yet' }}</p>
        <p class="muted">Credit-weighted average of the {{ doneTotal }} {{ doneTotal === 1 ? 'course' : 'courses' }} you have passed. Courses not yet cleared are not counted.</p>
        <GpaChart :terms="store.terms" />
      </section>

      <section class="panel tm" aria-labelledby="tm-h">
        <h2 id="tm-h">Terms</h2>
        <p class="big num">{{ store.termNumber }}<span class="of"> of {{ store.rule.limitTerms }}</span></p>
        <p class="muted">You are in term {{ store.termNumber }} ({{ store.termLabel }}). {{ left }} {{ left === 1 ? 'term' : 'terms' }} left to complete the {{ store.rule.label }} level.</p>
        <div class="meter big-meter" role="img" :aria-label="`${store.termNumber} of ${store.rule.limitTerms} terms used`">
          <span :style="{ width: `${used}%` }"></span>
        </div>

        <h3 class="mh">Milestones</h3>
        <ol class="miles">
          <li v-for="m in store.milestones" :key="m.byTerm" :class="m.state">
            <span class="pin" aria-hidden="true"></span>
            <div>
              <strong>{{ m.text }} by term {{ m.byTerm }}</strong>
              <span class="muted">{{ m.termLabel }}</span>
            </div>
            <span class="chip" :class="STATE_CLS[m.state]">
              {{ STATE_TEXT[m.state] }}<template v-if="!m.met && m.state !== 'missed'">: {{ m.needCourses }} {{ m.needCourses === 1 ? 'course' : 'courses' }}<template v-if="m.needProjects"> and {{ m.needProjects }} {{ m.needProjects === 1 ? 'project' : 'projects' }}</template> to go</template>
            </span>
          </li>
        </ol>
      </section>
    </div>

    <section class="panel" aria-labelledby="hist-h">
      <h2 id="hist-h">Term by term</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">Term</th>
              <th scope="col">Courses and results</th>
              <th scope="col" class="r">Term GPA</th>
              <th scope="col" class="r">CGPA after</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in store.terms" :key="t.term">
              <th scope="row">
                <strong>Term {{ t.number }}</strong>
                <span class="muted">{{ t.term }}</span>
              </th>
              <td>
                <ul class="res">
                  <li v-for="a in t.attempts" :key="a.courseId + a.term">
                    <RouterLink :to="`/courses/${a.courseId}`">{{ COURSES[a.courseId].name }}</RouterLink>
                    <span class="chip" :class="a.inProgress ? 'route' : isFail(a) ? 'low' : 'ok'">{{ result(a) }}</span>
                  </li>
                </ul>
              </td>
              <td class="r num">{{ t.termGpa?.toFixed(2) ?? (t.inProgress ? 'In progress' : 'None') }}</td>
              <td class="r num">{{ t.cgpaAfter?.toFixed(2) ?? '' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.top {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
  gap: 20px;
  margin-bottom: 20px;
  align-items: start;
}

.big {
  font-size: 3rem;
  line-height: 1.05;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 6px 0 6px;
}

.of {
  font-size: 1.25rem;
  color: var(--muted);
  font-weight: 500;
  letter-spacing: 0;
}

.cg .muted,
.tm > .muted {
  max-width: 52ch;
  margin-bottom: 16px;
}

.big-meter {
  height: 10px;
}

.mh {
  margin: 24px 0 10px;
}

.miles {
  list-style: none;
  margin: 0;
  padding: 0;
  position: relative;
}

.miles::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 10px;
  bottom: 10px;
  width: 3px;
  background: var(--line);
  border-radius: 3px;
}

.miles li {
  position: relative;
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 8px 0;
}

.miles li div {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.miles li strong {
  font-weight: 600;
}

.miles .muted {
  font-size: 0.875rem;
}

.miles .chip {
  white-space: normal;
  max-width: 22ch;
  text-align: center;
}

.pin {
  width: 15px;
  height: 15px;
  border-radius: 4px;
  transform: rotate(45deg);
  background: var(--surface);
  border: 3px solid var(--line-2);
  z-index: 1;
}

.met .pin {
  background: var(--ok);
  border-color: var(--ok);
}

.due .pin {
  border-color: var(--route);
}

.missed .pin {
  background: var(--high);
  border-color: var(--high);
}

.table-wrap {
  overflow-x: auto;
  margin-top: 12px;
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 560px;
}

th,
td {
  text-align: left;
  vertical-align: top;
  padding: 12px 12px 12px 0;
  border-top: 1px solid var(--line);
}

thead th {
  border-top: 0;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--muted);
  padding-top: 0;
}

tbody th {
  font-weight: 400;
  white-space: nowrap;
}

tbody th strong {
  display: block;
  font-weight: 600;
}

tbody th .muted {
  font-size: 0.875rem;
}

.r {
  text-align: right;
  padding-right: 0;
  white-space: nowrap;
}

.res {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.res li {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 10px;
  align-items: center;
}

.res a {
  color: var(--ink);
  text-decoration: none;
}

.res a:hover {
  color: var(--route-ink);
  text-decoration: underline;
}

@media (max-width: 1000px) {
  .top {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 520px) {
  .miles li {
    grid-template-columns: 16px minmax(0, 1fr);
  }
  .miles .chip {
    grid-column: 2;
    justify-self: start;
    max-width: none;
  }
}
</style>
