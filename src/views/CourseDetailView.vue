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
import AiMark from '../components/AiMark.vue'

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
    <div v-if="tab === 'overview'" class="overview" role="tabpanel">
      <section v-if="needsHelp && status.fails >= 2 && support" class="support" aria-labelledby="sup-h">
        <span class="sup-ic"><Icon name="person" :size="22" /></span>
        <div class="sup-text">
          <p class="tag">High risk: instructor support</p>
          <h2 id="sup-h">{{ support.instructor }} is working with you on this course</h2>
        </div>
        <div class="next">
          <span class="muted">Next check-in</span>
          <strong>{{ relativeDay(support.meetingAt) }}, {{ formatDate(support.meetingAt, { weekday: 'long' }) }}, {{ formatTime(support.meetingAt) }}</strong>
        </div>
        <a class="btn" :href="support.link" target="_blank" rel="noopener"><Icon name="video" :size="16" /> Join check-in</a>
      </section>

      <button v-if="needsHelp && plan && status.fails === 1" type="button" class="callout" @click="go('plan')">
        <Icon name="spark" :size="22" />
        <span>
          <strong>Your study plan for this course is ready</strong>
          <span>12 weeks, about {{ plan.hoursPerWeek }} hours a week, built from how past students passed it</span>
        </span>
        <Icon name="chevron" :size="20" />
      </button>

      <div v-if="current" class="stats" aria-label="This term so far">
        <div class="stat">
          <span class="s-l">This term so far</span>
          <span class="s-v num">Week {{ current.week }}<small> of {{ current.weeks }}</small></span>
          <div class="meter" role="img" :aria-label="`Week ${current.week} of ${current.weeks}`">
            <span :style="{ width: `${(current.week / current.weeks) * 100}%` }"></span>
          </div>
        </div>
        <div class="stat">
          <span class="s-l">Weekly assignments</span>
          <span class="s-v num" :class="{ warn: current.assignmentAvg < 40 }">{{ current.assignmentAvg }}<small>/100</small></span>
          <span class="s-n">{{ current.assignmentAvg < 40 ? 'Below 40, the OPPE threshold' : 'Average so far' }}</span>
        </div>
        <div v-if="current.quiz1 != null" class="stat">
          <span class="s-l">Quiz 1</span>
          <span class="s-v num" :class="{ warn: current.quiz1 < 40 }">{{ current.quiz1 }}<small>/100</small></span>
        </div>
      </div>

      <PredictionCard v-if="current" :student="store.student" :course-id="course.id" :attempt="current" />

      <section v-if="status.state === 'passed'" class="panel">
        <h2>You passed this course</h2>
        <p class="muted">Grade {{ status.grade }} in {{ status.term }}. It counts towards your CGPA and milestones.</p>
      </section>

      <section v-if="status.state === 'not_started'" class="panel">
        <h2>Not started yet</h2>
        <p class="muted">You can register for it in a coming term.<template v-if="guide"> See the course guide for how students got through it.</template></p>
      </section>

      <div class="foot" :class="{ solo: !oppe.length }">
        <section v-if="oppe.length" class="panel" aria-labelledby="op-h">
          <div class="panel-head">
            <h2 id="op-h">OPPE</h2>
            <RouterLink to="/oppe">Details</RouterLink>
          </div>
          <OppeList :items="oppe" />
        </section>

        <nav class="links" aria-label="More for this course">
          <button v-if="needsHelp && plan" type="button" class="link-card" @click="go('plan')">
            <span class="lc-ic"><Icon name="spark" :size="20" /></span>
            <span class="lc-t"><strong>Your study plan</strong><span>Week by week, about {{ plan.hoursPerWeek }} hours a week</span></span>
            <Icon name="chevron" :size="18" />
          </button>
          <button v-if="guide" type="button" class="link-card" @click="go('guide')">
            <span class="lc-ic"><Icon name="courses" :size="20" /></span>
            <span class="lc-t"><strong>Course guide</strong><span>How students who took it last term passed</span></span>
            <Icon name="chevron" :size="18" />
          </button>
          <RouterLink class="link-card" :to="{ path: '/ask', query: { q: `How do I do well in ${course.name}?` } }">
            <AiMark :size="40" />
            <span class="lc-t"><strong>Ask Disha about this course</strong><span>What to focus on, OPPE rules</span></span>
            <Icon name="chevron" :size="18" />
          </RouterLink>
        </nav>
      </div>
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

.overview {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.support {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  gap: 18px 22px;
  align-items: center;
  border-radius: var(--r-l);
  padding: 22px 26px;
  background: var(--high-soft);
}

.sup-ic {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--surface);
  color: var(--high);
}

.tag {
  font-weight: 600;
  font-size: 0.9375rem;
  color: var(--high);
  margin-bottom: 2px;
}

.support h2 {
  font-size: 1.1875rem;
}

.next {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
  padding-left: 22px;
  border-left: 1px solid var(--high-mid);
}

.next .muted {
  font-size: 0.875rem;
}

.next strong {
  font-weight: 600;
  white-space: nowrap;
}

.callout {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 14px;
  align-items: center;
  text-align: left;
  border: 1px solid var(--calm-light);
  cursor: pointer;
  padding: 18px 22px;
  border-radius: var(--r-m);
  background: var(--calm-soft);
  color: var(--ink);
}

.callout > svg:first-child {
  color: var(--calm);
}

.callout span {
  display: flex;
  flex-direction: column;
}

.callout strong {
  font-weight: 600;
  color: var(--calm-ink);
}

.callout span span {
  font-size: 0.9375rem;
  color: var(--ink-2);
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 20px 22px;
  border-radius: var(--r-m);
  background: var(--surface);
  border: 1px solid var(--line);
}

.s-l {
  color: var(--ink-2);
  font-size: 0.9375rem;
}

.s-v {
  font-size: 1.75rem;
  font-weight: 600;
  line-height: 1.15;
}

.s-v small {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--muted);
}

.s-n {
  font-size: 0.8125rem;
  color: var(--muted);
}

.stat .meter {
  margin-top: 8px;
  height: 8px;
}

.warn {
  color: var(--high);
}

.foot {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  gap: 24px;
  align-items: stretch;
}

.foot.solo {
  grid-template-columns: minmax(0, 1fr);
  max-width: 520px;
}

.foot .panel {
  padding: 22px 26px;
}

.links {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.link-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  width: 100%;
  padding: 16px 18px;
  border-radius: var(--r-m);
  background: var(--calm-soft);
  border: 1px solid var(--calm-light);
  color: var(--ink);
  text-decoration: none;
  text-align: left;
  cursor: pointer;
}

.link-card:hover {
  border-color: var(--calm-mid);
  background: var(--calm-soft);
}

.lc-ic {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--surface);
  color: var(--calm);
}

.lc-t {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.lc-t strong {
  font-weight: 600;
  color: var(--calm-ink);
}

.lc-t span {
  font-size: 0.875rem;
  color: var(--ink-2);
}

.link-card > svg:last-child {
  color: var(--calm);
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
  .support {
    grid-template-columns: auto minmax(0, 1fr);
  }
  .next {
    grid-column: 1 / -1;
    padding-left: 0;
    border-left: 0;
  }
  .support .btn {
    grid-column: 1 / -1;
    justify-self: start;
  }
  .foot {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .support {
    padding: 18px 20px;
  }
  .sup-ic {
    width: 40px;
    height: 40px;
  }
  .stats {
    grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
    gap: 8px;
  }
  .stat {
    padding: 12px 12px 14px;
  }
  .s-l {
    font-size: 0.8125rem;
    line-height: 1.25;
  }
  .s-v {
    font-size: 1.25rem;
    white-space: nowrap;
  }
  .s-n {
    display: none;
  }
  .next strong {
    white-space: normal;
  }
}
</style>
