<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student'
import { useCalendar } from '../services/calendar'
import RouteTrack from '../components/RouteTrack.vue'
import RiskPanel from '../components/RiskPanel.vue'
import MeetingList from '../components/MeetingList.vue'
import OppeList from '../components/OppeList.vue'
import Sparkline from '../components/Sparkline.vue'
import StatusChip from '../components/StatusChip.vue'
import Icon from '../components/Icon.vue'
import TodayCard from '../components/TodayCard.vue'
import { greeting, isToday } from '../utils/dates'
import { predict } from '../utils/predict'

const store = useStudentStore()
const { state: cal } = useCalendar()
const router = useRouter()

const s = computed(() => store.student)
const left = computed(() => store.rule.limitTerms - store.termNumber)
const doneTotal = computed(() => store.done.courses + store.done.projects)

const summary = computed(() => {
  const m = store.nextMilestone
  const head = `You have completed ${doneTotal.value} of ${store.done.total} ${store.rule.label} ${store.rule.unit}, with ${left.value} ${left.value === 1 ? 'term' : 'terms'} left.`
  if (!m) return `${head} Every milestone at this level is met.`
  const need = [m.needCourses && `${m.needCourses} more ${m.needCourses === 1 ? 'course' : 'courses'}`, m.needProjects && `${m.needProjects} more ${m.needProjects === 1 ? 'project' : 'projects'}`].filter(Boolean).join(' and ')
  return `${head} Next milestone: ${need} by term ${m.byTerm} (${m.termLabel}).`
})

const trend = computed(() => store.terms.map((t) => t.cgpaAfter))
const lastTerm = computed(() => [...store.terms].reverse().find((t) => !t.inProgress))
const upcoming = computed(() => cal.events.filter((e) => e.start > new Date() && !isToday(e.start)).slice(0, 3))
const predicted = (c) => predict(s.value, c.course.id, c.attempt)
const gradeCls = (p) => (Math.round(p.score) < 40 ? 'high' : Math.round(p.score) < 60 ? 'low' : 'ok')

const prompts = [
  'Am I eligible for my next OPPE?',
  'Will I pass my courses this term?',
  'What should I focus on this week?',
]
function ask(q) {
  router.push({ path: '/ask', query: { q } })
}
</script>

<template>
  <div class="page dash">
    <div class="head-row">
      <header class="head">
        <p class="where">{{ s.program }}, {{ store.termLabel }} term</p>
        <h1>{{ greeting() }}, {{ s.firstName }}</h1>
        <p class="summary">{{ summary }}</p>
      </header>
      <TodayCard class="today" :events="cal.events" />
    </div>

    <section class="hero" aria-label="Your route through the degree">
      <RouteTrack
        :limit="store.rule.limitTerms"
        :current="store.termNumber"
        :first-term="s.terms[0]"
        :milestones="store.milestones"
        :level-label="store.rule.label"
      />
    </section>

    <div class="sections">
      <div class="row status-row">
        <RiskPanel :risk="store.risk" :student="s" />

        <section class="panel cgpa-card" aria-labelledby="cgpa-h">
          <div class="panel-head">
            <h2 id="cgpa-h">CGPA</h2>
            <RouterLink to="/progress">Details</RouterLink>
          </div>
          <span class="big num">{{ store.cgpa?.toFixed(2) ?? 'None yet' }}</span>
          <Sparkline class="cgpa-line" :values="trend" :w="300" :h="64" fluid label="CGPA by term" />
          <p class="muted small">
            From {{ doneTotal }} completed {{ doneTotal === 1 ? 'course' : 'courses' }}.
            <template v-if="lastTerm && lastTerm.fails">{{ lastTerm.term }}: {{ lastTerm.fails }} course not cleared.</template>
          </p>
        </section>
      </div>

      <section aria-labelledby="term-h">
        <div class="sec-head">
          <h2 id="term-h">This term</h2>
          <RouterLink to="/courses">All courses</RouterLink>
        </div>
        <ul class="courses" :class="`n${Math.min(store.current.length, 4)}`">
          <li v-for="c in store.current" :key="c.course.id" class="course">
            <div class="c-top">
              <div class="c-name">
                <RouterLink :to="`/courses/${c.course.id}`" class="c-title">{{ c.course.name }}</RouterLink>
                <StatusChip :status="c.status" />
              </div>
              <div v-if="predicted(c)" class="c-grade" :class="gradeCls(predicted(c))" :aria-label="`Predicted grade ${predicted(c).grade}`">
                <span class="pg">{{ predicted(c).grade }}</span>
                <span class="pl">predicted<br />grade</span>
              </div>
            </div>

            <div class="c-week">
              <div class="c-wk-row">
                <span>Week {{ c.attempt.week }} of {{ c.attempt.weeks }}</span>
                <span class="muted">{{ c.attempt.weeks - c.attempt.week }} {{ c.attempt.weeks - c.attempt.week === 1 ? 'week' : 'weeks' }} left</span>
              </div>
              <div class="meter" role="img" :aria-label="`Week ${c.attempt.week} of ${c.attempt.weeks}`">
                <span :style="{ width: `${(c.attempt.week / c.attempt.weeks) * 100}%` }"></span>
              </div>
            </div>

            <dl class="c-stats">
              <div>
                <dt>Assignment average</dt>
                <dd class="num" :class="{ warn: c.attempt.assignmentAvg < 40 }">{{ c.attempt.assignmentAvg }}</dd>
              </div>
              <div v-if="predicted(c)">
                <dt>Predicted score</dt>
                <dd class="num" :class="gradeCls(predicted(c))">{{ Math.round(predicted(c).score) }}<small>/100</small></dd>
              </div>
            </dl>

            <RouterLink class="guide-link" :to="{ path: `/courses/${c.course.id}`, query: { tab: c.status.fails ? 'plan' : 'guide' } }">
              <Icon name="spark" :size="16" /> {{ c.status.fails ? 'Your study plan' : 'How others passed it' }}
              <Icon name="chevron" :size="16" class="go" />
            </RouterLink>
          </li>
        </ul>
      </section>

      <div class="row two">
        <section class="panel" aria-labelledby="meet-h">
          <div class="panel-head">
            <h2 id="meet-h">Coming up</h2>
            <RouterLink to="/meetings">See all</RouterLink>
          </div>
          <MeetingList compact :events="upcoming" />
          <p class="note">
            <template v-if="cal.connected && cal.source === 'google'">Synced from Google Calendar.</template>
            <template v-else-if="cal.connected">Demo connection: sample meetings shown.</template>
            <template v-else>Sample meetings. <RouterLink to="/meetings">Connect Google Calendar</RouterLink> to see your own.</template>
          </p>
        </section>

        <section class="panel oppe-card" aria-labelledby="oppe-h">
          <div class="panel-head">
            <h2 id="oppe-h">OPPE eligibility</h2>
            <RouterLink to="/oppe">Details</RouterLink>
          </div>
          <OppeList :items="s.oppe" />
          <p class="oppe-rule">
            <Icon name="oppe" :size="18" />
            <span>To sit an OPPE you need a weekly assignment average of at least 40 in that course. Each OPPE is decided on a set date before the exam.</span>
          </p>
        </section>
      </div>

      <section class="ask" aria-labelledby="ask-h">
        <div class="ask-text">
          <span class="ask-ic"><Icon name="chat" :size="22" /></span>
          <div>
            <h2 id="ask-h">Questions about your degree?</h2>
            <p>Disha answers from your own record and the program rules.</p>
          </div>
        </div>
        <div class="prompts">
          <button v-for="p in prompts" :key="p" type="button" @click="ask(p)">{{ p }}</button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.head-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 28px;
  align-items: start;
}

.head {
  max-width: 70ch;
}

.where {
  color: var(--muted);
  font-weight: 500;
  margin-bottom: 4px;
}

.summary {
  margin-top: 10px;
  font-size: 1.125rem;
  color: var(--ink-2);
}

.hero {
  margin: 30px 0 38px;
  padding: 8px 0 4px;
}

.sections {
  display: flex;
  flex-direction: column;
  gap: 36px;
}

.row {
  display: grid;
  gap: 24px;
  align-items: stretch;
}

.status-row {
  grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr);
}

.row.two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.sections .panel {
  padding: 24px 28px;
}

.sec-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.sec-head a {
  font-size: 0.9375rem;
  font-weight: 500;
  text-decoration: none;
}

.sec-head a:hover {
  text-decoration: underline;
}

/* CGPA */
.cgpa-card {
  display: flex;
  flex-direction: column;
}

.cgpa-card .panel-head {
  margin-bottom: 6px;
}

.big {
  font-size: 2.75rem;
  line-height: 1;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.cgpa-line {
  margin: 14px 0 0;
  max-height: 72px;
}

.small {
  font-size: 0.9375rem;
  margin-top: auto;
  padding-top: 12px;
}

/* This term: one card per course */
.courses {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}

.courses.n1 {
  grid-template-columns: minmax(0, 1fr);
  max-width: 560px;
}

.courses.n3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.course {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 26px 20px;
  border-radius: var(--r-m);
  background: var(--surface);
  border: 1px solid var(--line);
}

.c-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.c-name {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
}

.c-title {
  font-size: 1.125rem;
  font-weight: 600;
  line-height: 1.3;
  color: var(--ink);
  text-decoration: none;
}

.c-title:hover {
  color: var(--route-ink);
  text-decoration: underline;
}

.c-grade {
  flex: none;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px 6px 6px;
  border-radius: 12px;
  background: var(--ok-soft);
  --tone: var(--ok);
}

.c-grade.low,
dd.low {
  --tone: var(--low);
}

.c-grade.low {
  background: var(--low-soft);
}

.c-grade.high,
dd.high {
  --tone: var(--high);
}

.c-grade.high {
  background: var(--high-soft);
}

.pg {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: var(--surface);
  color: var(--tone);
  font-weight: 700;
  font-size: 1.125rem;
}

.pl {
  font-size: 0.75rem;
  line-height: 1.2;
  color: var(--ink-2);
}

.c-wk-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.9375rem;
  margin-bottom: 8px;
}

.c-week .meter {
  height: 8px;
}

.c-stats {
  margin: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.c-stats div {
  padding: 12px 14px;
  border-radius: var(--r-s);
  background: var(--paper);
}

.c-stats dt {
  font-size: 0.8125rem;
  color: var(--muted);
}

.c-stats dd {
  margin: 2px 0 0;
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.2;
  color: var(--ink);
}

.c-stats dd.ok,
.c-stats dd.low,
.c-stats dd.high {
  color: var(--tone);
}

.c-stats dd small {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--muted);
}

.c-stats dd.warn {
  color: var(--high);
}

.guide-link {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid var(--line);
  font-size: 0.9375rem;
  font-weight: 500;
  text-decoration: none;
  color: var(--calm-ink);
}

.guide-link .go {
  margin-left: auto;
}

.guide-link:hover {
  text-decoration: underline;
}

.oppe-card {
  display: flex;
  flex-direction: column;
}

.oppe-rule {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-top: auto;
  padding: 12px 14px;
  border-radius: var(--r-s);
  background: var(--calm-soft);
  color: var(--ink-2);
  font-size: 0.875rem;
  line-height: 1.45;
}

.oppe-card .oppe-list {
  margin-bottom: 20px;
}

.oppe-rule svg {
  flex: none;
  margin-top: 1px;
  color: var(--calm);
}

/* Ask Disha */
.ask {
  display: flex;
  flex-direction: column;
  gap: 18px;
  border-radius: var(--r-l);
  padding: 26px 28px;
  background: var(--calm-soft);
  border: 1px solid var(--calm-light);
}

.ask-text {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.ask-ic {
  flex: none;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--surface);
  color: var(--calm);
}

.ask h2 {
  color: var(--calm-ink);
}

.ask p {
  color: var(--ink-2);
  margin-top: 4px;
}

.prompts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.prompts button {
  border: 1px solid var(--calm-light);
  background: var(--surface);
  color: var(--calm-ink);
  border-radius: var(--r-s);
  padding: 11px 16px;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
}

.prompts button:hover {
  border-color: var(--calm-mid);
  background: #fff;
  box-shadow: 0 1px 6px rgba(43, 95, 86, 0.12);
}

@media (max-width: 1100px) {
  .head-row {
    grid-template-columns: 1fr;
    gap: 18px;
  }
  .courses.n3 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1000px) {
  .status-row,
  .row.two {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .sections {
    gap: 28px;
  }
  .courses,
  .courses.n3 {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  .course,
  .sections .panel {
    padding: 20px;
  }
  .ask {
    padding: 22px 20px;
  }
  .prompts {
    grid-template-columns: 1fr;
  }
}
</style>
