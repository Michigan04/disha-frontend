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

    <div class="grid">
      <RiskPanel class="a-risk" :risk="store.risk" :student="s" />

      <section class="panel a-meet" aria-labelledby="meet-h">
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

      <section class="panel a-cgpa" aria-labelledby="cgpa-h">
        <div class="panel-head">
          <h2 id="cgpa-h">CGPA</h2>
          <RouterLink to="/progress">Details</RouterLink>
        </div>
        <div class="cgpa">
          <span class="big num">{{ store.cgpa?.toFixed(2) ?? 'None yet' }}</span>
          <Sparkline :values="trend" label="CGPA by term" />
        </div>
        <p class="muted small">
          From {{ doneTotal }} completed {{ doneTotal === 1 ? 'course' : 'courses' }}.
          <template v-if="lastTerm && lastTerm.fails">{{ lastTerm.term }}: {{ lastTerm.fails }} course not cleared.</template>
        </p>
      </section>

      <section class="panel a-oppe" aria-labelledby="oppe-h">
        <div class="panel-head">
          <h2 id="oppe-h">OPPE eligibility</h2>
          <RouterLink to="/oppe">Details</RouterLink>
        </div>
        <OppeList :items="s.oppe" />
      </section>

      <section class="panel a-term" aria-labelledby="term-h">
        <div class="panel-head">
          <h2 id="term-h">This term</h2>
          <RouterLink to="/courses">All courses</RouterLink>
        </div>
        <ul class="term">
          <li v-for="c in store.current" :key="c.course.id">
            <RouterLink :to="`/courses/${c.course.id}`" class="term-row">
              <div class="t-main">
                <strong>{{ c.course.name }}</strong>
                <StatusChip :status="c.status" />
              </div>
              <div v-if="predicted(c)" class="t-pred" :class="gradeCls(predicted(c))" :aria-label="`Predicted grade ${predicted(c).grade}, score ${Math.round(predicted(c).score)}`">
                <span class="pg">{{ predicted(c).grade }}</span>
                <span class="pl">predicted<br /><b class="num">{{ Math.round(predicted(c).score) }}</b>/100</span>
              </div>
              <div class="t-meta">
                <span class="muted">Week {{ c.attempt.week }} of {{ c.attempt.weeks }}</span>
                <div class="meter" role="img" :aria-label="`Week ${c.attempt.week} of ${c.attempt.weeks}`">
                  <span :style="{ width: `${(c.attempt.week / c.attempt.weeks) * 100}%` }"></span>
                </div>
                <span class="muted">Assignment average <strong class="num" :class="{ warn: c.attempt.assignmentAvg < 40 }">{{ c.attempt.assignmentAvg }}</strong></span>
              </div>
            </RouterLink>
            <RouterLink class="guide-link" :to="{ path: `/courses/${c.course.id}`, query: { tab: c.status.fails ? 'plan' : 'guide' } }">
              <Icon name="spark" :size="16" /> {{ c.status.fails ? 'Your study plan' : 'How others passed it' }}
            </RouterLink>
          </li>
        </ul>
      </section>

      <section class="ask a-ask" aria-labelledby="ask-h">
        <Icon name="chat" :size="24" />
        <h2 id="ask-h">Questions about your degree?</h2>
        <p>Disha answers from your own record and the program rules.</p>
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
  margin: 26px 0 30px;
  padding: 8px 0 4px;
}

.grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr);
  grid-template-areas:
    'risk meet'
    'cgpa meet'
    'oppe oppe'
    'term ask';
  gap: 20px;
  align-items: start;
}

.a-risk { grid-area: risk; }
.a-meet { grid-area: meet; }
.a-cgpa { grid-area: cgpa; }
.a-oppe { grid-area: oppe; }
.a-term { grid-area: term; }
.a-ask { grid-area: ask; }

.cgpa {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.big {
  font-size: 2.75rem;
  line-height: 1;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.small {
  font-size: 0.9375rem;
  margin-top: 10px;
}

.term {
  list-style: none;
  margin: 0;
  padding: 0;
}

.term li + li {
  border-top: 1px solid var(--line);
}

.term-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px 16px;
  padding: 14px 0 6px;
  color: inherit;
  text-decoration: none;
  align-items: center;
}

.term li:first-child .term-row {
  padding-top: 0;
}

.t-main {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  align-items: center;
}

.t-main strong {
  font-weight: 600;
}

.t-meta {
  grid-column: 1;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
  font-size: 0.875rem;
}

.t-meta strong {
  color: var(--ink);
}

.t-meta strong.warn {
  color: var(--high);
}

.t-pred {
  grid-row: 1 / span 2;
  grid-column: 2;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px 6px 6px;
  border-radius: 12px;
  background: var(--ok-soft);
  --tone: var(--ok);
}

.t-pred.low {
  background: var(--low-soft);
  --tone: var(--low);
}

.t-pred.high {
  background: var(--high-soft);
  --tone: var(--high);
}

.pg {
  width: 34px;
  height: 34px;
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

.pl b {
  font-size: 0.9375rem;
  color: var(--tone);
}

.guide-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 12px;
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
}

.guide-link:hover {
  text-decoration: underline;
}

.term-row:hover strong:first-child {
  color: var(--route-ink);
}

.ask {
  border-radius: var(--r-l);
  padding: 22px 24px;
  background: var(--ink);
  color: #fff;
}

.ask p {
  color: #c9cde0;
  margin: 4px 0 16px;
}

.ask h2 {
  margin-top: 10px;
}

.prompts {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prompts button {
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: transparent;
  color: #fff;
  border-radius: var(--r-s);
  padding: 9px 12px;
  cursor: pointer;
}

.prompts button:hover {
  background: rgba(255, 255, 255, 0.08);
}

@media (max-width: 1100px) {
  .head-row {
    grid-template-columns: 1fr;
    gap: 18px;
  }
}

@media (max-width: 1000px) {
  .grid {
    grid-template-columns: 1fr;
    grid-template-areas: 'risk' 'meet' 'oppe' 'cgpa' 'term' 'ask';
  }
}

@media (max-width: 560px) {
  .t-meta {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
