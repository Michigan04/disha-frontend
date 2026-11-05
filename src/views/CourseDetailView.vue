<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student'
import { COURSES } from '../data/courses'
import { PAST_STUDENT_INSIGHTS } from '../data/insights'
import { COURSE_GUIDES } from '../data/guides'
import { STUDY_PLANS } from '../data/plans'
import { attemptsFor, courseStatus, isFail } from '../utils/progress'
import { formatDate, formatTime, relativeDay } from '../utils/dates'
import StatusChip from '../components/StatusChip.vue'
import OppeList from '../components/OppeList.vue'
import PredictionCard from '../components/PredictionCard.vue'
import CourseGuide from '../components/CourseGuide.vue'
import StudyPlan from '../components/StudyPlan.vue'
import Icon from '../components/Icon.vue'

const route = useRoute()
const router = useRouter()
const store = useStudentStore()

const course = computed(() => COURSES[route.params.id])
const status = computed(() => course.value && courseStatus(store.student, course.value.id))
const attempts = computed(() => (course.value ? attemptsFor(store.student, course.value.id) : []))
const oppe = computed(() => store.student.oppe.filter((o) => o.courseId === course.value?.id))
const guide = computed(() => course.value && COURSE_GUIDES[course.value.id])
const plan = computed(() => course.value && STUDY_PLANS[course.value.id])
const insight = computed(() => course.value && PAST_STUDENT_INSIGHTS[course.value.id])
const support = computed(() => {
  const iv = store.student.intervention
  return iv && iv.courseId === course.value?.id ? iv : null
})
const needsHelp = computed(() => status.value && status.value.state !== 'passed' && status.value.fails > 0)
const current = computed(() => status.value?.current || null)

const tabs = computed(() => {
  const t = [{ id: 'overview', label: 'Overview' }]
  if (guide.value) t.push({ id: 'guide', label: 'Course guide' })
  if (needsHelp.value && plan.value) t.push({ id: 'plan', label: 'Study plan' })
  t.push({ id: 'attempts', label: `Attempts (${attempts.value.length})` })
  return t
})
const tab = computed(() => (tabs.value.some((t) => t.id === route.query.tab) ? route.query.tab : 'overview'))
const go = (id) => router.replace({ query: { ...route.query, tab: id } })

function attemptResult(a) {
  if (a.inProgress) return { text: 'In progress', cls: 'route' }
  if (isFail(a)) return { text: 'Not cleared', cls: 'low' }
  return { text: `Passed, grade ${a.grade}`, cls: 'ok' }
}
</script>

<template>
  <div v-if="course" class="page">
    <RouterLink to="/courses" class="back"><Icon name="back" :size="18" /> Courses</RouterLink>

    <header class="head">
      <h1>{{ course.name }}</h1>
      <p class="sub">
        <StatusChip :status="status" />
        <span class="muted">{{ course.type === 'project' ? 'Project' : `${course.credits} credits` }}<template v-if="current">, week {{ current.week }} of {{ current.weeks }}</template></span>
      </p>
    </header>

    <div class="tabs" role="tablist" aria-label="Course sections">
      <button v-for="t in tabs" :key="t.id" type="button" role="tab" :aria-selected="tab === t.id" :class="{ on: tab === t.id }" @click="go(t.id)">
        {{ t.label }}
        <span v-if="t.id === 'plan'" class="dot" aria-hidden="true"></span>
      </button>
    </div>

    <!-- OVERVIEW -->
    <div v-if="tab === 'overview'" class="layout" role="tabpanel">
      <div class="col-main">
        <section v-if="needsHelp && status.fails >= 2 && support" class="support" aria-labelledby="sup-h">
          <p class="tag"><Icon name="person" :size="18" /> High risk: instructor support</p>
          <h2 id="sup-h">{{ support.instructor }} is working with you on this course</h2>
          <div class="next">
            <div>
              <span class="muted">Next check-in</span>
              <strong>{{ relativeDay(support.meetingAt) }}, {{ formatDate(support.meetingAt, { weekday: 'long' }) }} at {{ formatTime(support.meetingAt) }}</strong>
            </div>
            <a class="btn" :href="support.link" target="_blank" rel="noopener"><Icon name="video" :size="16" /> Join check-in</a>
          </div>
          <div class="sup-grid">
            <div>
              <h3>Support plan</h3>
              <ul class="ticks">
                <li v-for="p in support.plan" :key="p"><Icon name="check" :size="18" /> {{ p }}</li>
              </ul>
            </div>
            <div>
              <h3>Bring to the check-in</h3>
              <ul class="ticks soft">
                <li v-for="b in support.bring" :key="b"><Icon name="courses" :size="18" /> {{ b }}</li>
              </ul>
            </div>
          </div>
        </section>

        <PredictionCard v-if="current" :student="store.student" :course-id="course.id" :attempt="current" />

        <button v-if="needsHelp && plan && status.fails === 1" type="button" class="callout" @click="go('plan')">
          <Icon name="spark" :size="22" />
          <span>
            <strong>Your study plan for this course is ready</strong>
            <span>12 weeks, about {{ plan.hoursPerWeek }} hours a week, built from how past students passed it</span>
          </span>
          <Icon name="chevron" :size="20" />
        </button>

        <section v-if="status.state === 'passed'" class="panel">
          <h2>You passed this course</h2>
          <p class="muted">Grade {{ status.grade }} in {{ status.term }}. It counts towards your CGPA and milestones.</p>
        </section>

        <section v-if="status.state === 'not_started'" class="panel">
          <h2>Not started yet</h2>
          <p class="muted">You can register for it in a coming term.<template v-if="guide"> See the course guide for how students got through it.</template></p>
        </section>
      </div>

      <aside class="col-side">
        <section v-if="current" class="panel stats" aria-labelledby="now-h">
          <h2 id="now-h">This term so far</h2>
          <div class="meter" role="img" :aria-label="`Week ${current.week} of ${current.weeks}`">
            <span :style="{ width: `${(current.week / current.weeks) * 100}%` }"></span>
          </div>
          <p class="muted wk">Week {{ current.week }} of {{ current.weeks }}</p>
          <dl>
            <div><dt>Weekly assignments</dt><dd class="num" :class="{ warn: current.assignmentAvg < 40 }">{{ current.assignmentAvg }}</dd></div>
            <div v-if="current.quiz1 != null"><dt>Quiz 1</dt><dd class="num" :class="{ warn: current.quiz1 < 40 }">{{ current.quiz1 }}</dd></div>
          </dl>
        </section>

        <section v-if="oppe.length" class="panel" aria-labelledby="op-h">
          <div class="panel-head">
            <h2 id="op-h">OPPE</h2>
            <RouterLink to="/oppe">Details</RouterLink>
          </div>
          <OppeList :items="oppe" />
        </section>

        <RouterLink class="ask" :to="{ path: '/ask', query: { q: `How do I do well in ${course.name}?` } }">
          <Icon name="chat" :size="20" />
          <span>Ask Disha about this course</span>
        </RouterLink>
      </aside>
    </div>

    <!-- COURSE GUIDE -->
    <div v-else-if="tab === 'guide'" role="tabpanel">
      <CourseGuide :guide="guide" :current-week="current?.week ?? null" />
    </div>

    <!-- STUDY PLAN -->
    <div v-else-if="tab === 'plan'" role="tabpanel">
      <StudyPlan
        :plan="plan"
        :insight="insight"
        :current-week="current?.week ?? 1"
        :storage-key="`disha.plan.${store.student.id}.${course.id}`"
      />
    </div>

    <!-- ATTEMPTS -->
    <div v-else role="tabpanel">
      <section class="panel attempts-panel">
        <ol v-if="attempts.length" class="attempts">
          <li v-for="(a, i) in attempts" :key="a.term">
            <span class="n num">{{ i + 1 }}</span>
            <div>
              <strong>{{ a.term }}</strong>
              <span class="chip" :class="attemptResult(a).cls">{{ attemptResult(a).text }}</span>
            </div>
          </li>
        </ol>
        <p v-else class="muted">No attempts yet.</p>
      </section>
    </div>
  </div>

  <div v-else class="page">
    <h1>Course not found</h1>
    <p class="muted" style="margin-top: 8px">This course is not part of your level. <RouterLink to="/courses">Go to your courses</RouterLink></p>
  </div>
</template>

<style scoped>
.back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  text-decoration: none;
  font-weight: 500;
  margin-bottom: 14px;
}

.head {
  margin-bottom: 18px;
}

.sub {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 22px;
  overflow-x: auto;
}

.tabs button {
  position: relative;
  border: 0;
  background: none;
  padding: 10px 14px;
  font-weight: 500;
  color: var(--muted);
  cursor: pointer;
  white-space: nowrap;
  border-bottom: 3px solid transparent;
  margin-bottom: -1px;
}

.tabs button:hover {
  color: var(--ink);
}

.tabs button.on {
  color: var(--route-ink);
  border-bottom-color: var(--route);
  font-weight: 600;
}

.tabs .dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--low);
  margin-left: 4px;
  vertical-align: middle;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.col-main,
.col-side {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 0.9375rem;
  color: var(--high);
  margin-bottom: 6px;
}

.support {
  border-radius: var(--r-l);
  padding: 22px 24px;
  background: var(--high-soft);
}

.next {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  margin: 16px 0 6px;
  padding: 14px 16px;
  border-radius: var(--r-m);
  background: var(--surface);
}

.next div {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.next strong {
  font-size: 1.0625rem;
  font-weight: 600;
}

.next .muted {
  font-size: 0.875rem;
}

.sup-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 20px;
}

.support h3 {
  margin: 14px 0 8px;
  font-size: 1rem;
}

.ticks {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ticks li {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 0.9375rem;
}

.ticks svg {
  flex: none;
  margin-top: 2px;
  color: var(--high);
}

.ticks.soft svg {
  color: var(--ink-2);
}

.callout {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 14px;
  align-items: center;
  text-align: left;
  border: 0;
  cursor: pointer;
  padding: 16px 20px;
  border-radius: var(--r-m);
  background: var(--low-soft);
  color: var(--ink);
}

.callout > svg:first-child {
  color: var(--low);
}

.callout span {
  display: flex;
  flex-direction: column;
}

.callout strong {
  font-weight: 600;
}

.callout span span {
  font-size: 0.9375rem;
  color: var(--ink-2);
}

.stats h2 {
  margin-bottom: 12px;
}

.stats .wk {
  font-size: 0.875rem;
  margin-top: 6px;
}

.stats dl {
  margin: 14px 0 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stats dl div {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  border-top: 1px solid var(--line);
  padding-top: 8px;
}

.stats dt {
  color: var(--ink-2);
}

.stats dd {
  margin: 0;
  font-size: 1.375rem;
  font-weight: 600;
}

.warn {
  color: var(--high);
}

.ask {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-radius: var(--r-m);
  background: var(--ink);
  color: #fff;
  text-decoration: none;
  font-weight: 500;
}

.ask:hover {
  background: var(--ink-2);
}

.attempts-panel {
  max-width: 560px;
}

.attempts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.attempts li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.attempts .n {
  flex: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--paper);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--ink-2);
}

.attempts div {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.attempts strong {
  font-weight: 600;
}

@media (max-width: 1000px) {
  .layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .sup-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }
}
</style>
