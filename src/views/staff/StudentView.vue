<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useStaffStore } from '../../stores/staff'
import { STAFF, SUPPORT_STAFF } from '../../data/staff'
import { CATEGORIES, OUTCOMES, SUGGESTED_ACTIONS } from '../../data/actions'
import { LEVEL_COURSES, COURSES } from '../../data/courses'
import { LEVEL_RULES } from '../../data/rules'
import { attemptsFor } from '../../utils/progress'
import { formatDate, relativeDay } from '../../utils/dates'
import Icon from '../../components/Icon.vue'
import RouteTrack from '../../components/RouteTrack.vue'
import StatusChip from '../../components/StatusChip.vue'
import RiskChip from '../../components/staff/RiskChip.vue'
import Person from '../../components/staff/Person.vue'
import Timeline from '../../components/staff/Timeline.vue'
import InterventionForm from '../../components/staff/InterventionForm.vue'

const auth = useAuthStore()
const staff = useStaffStore()
const route = useRoute()
const id = computed(() => String(route.params.id))
const r = computed(() => staff.row(id.value))
const history = computed(() => staff.historyOf(id.value))
const status = computed(() => staff.statusOf(id.value))
const isAdmin = computed(() => auth.role === 'admin')

const RULE_TEXT = computed(() => ({
  failed_twice: `High risk: the same course failed ${staff.rules.highFails} or more times (rules v${staff.rules.version})`,
  failed_once: `Low risk: a course failed ${staff.rules.lowFails === 1 ? 'once' : `${staff.rules.lowFails} times`} (rules v${staff.rules.version})`,
  oppe_not_eligible: `OPPE needs an assignment average of ${staff.rules.oppeMin} or more`,
  low_prediction: 'Model estimate from scores so far; not a risk level',
  plan_inactive: 'From the student’s study plan activity',
  behind_milestone: 'Milestone rules for this level',
  data_issue: 'Flagged during the last data import',
}))
const REASON_ICON = { failed_twice: 'alert', failed_once: 'flag', oppe_not_eligible: 'oppe', low_prediction: 'spark', plan_inactive: 'clock', behind_milestone: 'progress', data_issue: 'file' }

const sharedKey = (reason, action) => `${reason.key}:${reason.courseId || ''}:${action.key}`
const isShared = (reason, action) => (staff.shared[id.value] || []).includes(sharedKey(reason, action))

// Course history: every course with at least one attempt
const history2 = computed(() => {
  if (!r.value) return []
  return LEVEL_COURSES[r.value.level]
    .map((cid) => ({ course: COURSES[cid], attempts: attemptsFor(r.value.student, cid) }))
    .filter((x) => x.attempts.length)
})

// Logging an intervention
const showForm = ref(false)
const preset = ref('call')
const saved = ref('')
function openForm(type) {
  preset.value = type
  showForm.value = false
  requestAnimationFrame(() => {
    showForm.value = true
    requestAnimationFrame(() => document.getElementById('form-h')?.scrollIntoView({ behavior: 'smooth', block: 'center' }))
  })
}
function save(rec) {
  staff.logIntervention(rec)
  showForm.value = false
  saved.value = 'Saved to the intervention history and the audit log.'
  setTimeout(() => (saved.value = ''), 4000)
}

// Reassigning (administrators)
const re = reactive({ open: false, owner: '', reason: '', error: '' })
function reassign() {
  re.error = ''
  if (!re.owner) return (re.error = 'Choose a staff member.')
  if (re.reason.trim().length < 4) return (re.error = 'Give a reason; it is kept with the owner history.')
  staff.assign([id.value], re.owner, re.reason.trim())
  Object.assign(re, { open: false, owner: '', reason: '' })
}

const topFactor = (p) => [...p.factors].sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))[0]
const planFor = (c) => r.value.risk.level === 'low' && r.value.risk.focus?.course.id === c.course.id ? r.value.meta.plan : null
</script>

<template>
  <div v-if="r" class="page wide">
    <RouterLink to="/staff/students" class="back"><Icon name="back" :size="18" /> At-risk students</RouterLink>

    <header class="hero" :class="r.risk.level">
      <div class="id">
        <Person :name="r.name" :sub="`${r.rollNo} · ${r.student.program}`" :size="56" :tone="r.risk.level === 'none' ? 'ok' : r.risk.level" />
        <div class="tags">
          <RiskChip :level="r.risk.level" :is-new="r.isNew" />
          <span class="chip">{{ r.levelLabel }}, term {{ r.term }} of {{ LEVEL_RULES[r.level].limitTerms }}</span>
          <span class="chip">Admitted {{ r.cohort }}</span>
          <span v-if="r.meta.dataIssue" class="chip low"><Icon name="file" :size="14" /> Check data</span>
        </div>
      </div>
      <div class="owner">
        <span class="lbl">Owner</span>
        <strong v-if="r.owner">{{ STAFF[r.owner].name }}</strong>
        <strong v-else class="none">No owner yet</strong>
        <span v-if="status" class="chip" :class="OUTCOMES[status].cls">{{ OUTCOMES[status].label }}</span>
        <button v-if="isAdmin" type="button" class="link" @click="re.open = !re.open">{{ r.owner ? 'Reassign' : 'Assign' }}</button>
      </div>
      <div class="quick">
        <button class="btn" type="button" @click="openForm('call')"><Icon name="plus" :size="18" /> Log intervention</button>
        <button class="btn quiet" type="button" @click="openForm('email')"><Icon name="mail" :size="18" /> Email</button>
        <button class="btn quiet" type="button" @click="openForm('referral')"><Icon name="refer" :size="18" /> Refer</button>
      </div>
    </header>

    <div v-if="re.open" class="reassign">
      <select v-model="re.owner" aria-label="New owner">
        <option value="" disabled>Choose staff member</option>
        <option v-for="m in SUPPORT_STAFF" :key="m.id" :value="m.id" :disabled="m.id === r.owner">{{ m.name }} ({{ staff.caseload.find((x) => x.id === m.id).cases.length }} of {{ m.capacity }})</option>
      </select>
      <input v-model="re.reason" type="text" placeholder="Reason, for example: workload" aria-label="Reason" />
      <button class="btn" type="button" @click="reassign">Save</button>
      <p v-if="re.error" class="err" role="alert">{{ re.error }}</p>
    </div>

    <div class="layout">
      <div class="main">
        <section class="panel" aria-labelledby="why-h">
          <div class="panel-head">
            <h2 id="why-h">Why {{ r.student.firstName }} is flagged, and what to do</h2>
            <span class="muted small">Updated {{ relativeDay(r.student.updatedAt).toLowerCase() }}</span>
          </div>
          <p v-if="!r.reasons.length" class="muted">No risk reasons. {{ r.student.firstName }} is on track.</p>
          <ul class="reasons">
            <li v-for="reason in r.reasons" :key="reason.key + reason.courseId">
              <div class="rs-head">
                <span class="rs-ic" :class="reason.key"><Icon :name="REASON_ICON[reason.key]" :size="18" /></span>
                <div>
                  <strong>{{ reason.text }}</strong>
                  <span class="rule">{{ RULE_TEXT[reason.key] }}</span>
                </div>
              </div>
              <ul class="acts">
                <li v-for="act in SUGGESTED_ACTIONS[reason.key]" :key="act.key" :class="{ done: isShared(reason, act) }">
                  <span class="chip" :class="CATEGORIES[act.cat].cls">{{ CATEGORIES[act.cat].label }}</span>
                  <span class="at">{{ act.text }}</span>
                  <button type="button" class="share" :aria-pressed="isShared(reason, act)" @click="staff.toggleShared(r.id, sharedKey(reason, act), act.text)">
                    <Icon :name="isShared(reason, act) ? 'check' : 'plus'" :size="16" /> {{ isShared(reason, act) ? 'Shared' : 'Mark shared' }}
                  </button>
                </li>
              </ul>
            </li>
          </ul>
        </section>

        <section class="panel" aria-labelledby="route-h">
          <div class="panel-head">
            <h2 id="route-h">Route through the degree</h2>
            <span class="muted small">CGPA <strong class="num ink">{{ r.cgpa?.toFixed(2) ?? '–' }}</strong> · {{ r.done.courses + r.done.projects }} of {{ r.done.total }} done</span>
          </div>
          <RouteTrack :limit="LEVEL_RULES[r.level].limitTerms" :current="r.term" :first-term="r.student.terms[0]" :milestones="r.milestones" :level-label="r.levelLabel" />
        </section>

        <section class="panel" aria-labelledby="now-h">
          <div class="panel-head">
            <h2 id="now-h">This term</h2>
            <span class="muted small">Week 7 of 12</span>
          </div>
          <ul class="now">
            <li v-for="c in r.current" :key="c.course.id">
              <div class="n-top">
                <strong>{{ c.course.name }}</strong>
                <StatusChip :status="c.status" />
              </div>
              <div v-if="c.prediction" class="n-body">
                <div class="pred" :class="Math.round(c.prediction.score) < 40 ? 'fail' : Math.round(c.prediction.score) < 60 ? 'low' : 'ok'">
                  <span class="g">{{ c.prediction.grade }}</span>
                  <span class="pl">predicted<br /><b class="num">{{ Math.round(c.prediction.score) }}</b>/100</span>
                </div>
                <dl class="facts">
                  <div><dt>Assignments</dt><dd class="num" :class="{ bad: c.attempt.assignmentAvg < staff.rules.oppeMin }">{{ c.attempt.assignmentAvg }}</dd></div>
                  <div><dt>Quiz 1</dt><dd class="num">{{ c.attempt.quiz1 ?? 'Missing' }}</dd></div>
                  <div v-for="o in r.oppe.filter((x) => x.courseId === c.course.id)" :key="o.id"><dt>{{ o.title }}</dt><dd><span class="chip" :class="o.status === 'eligible' ? 'ok' : o.status === 'not_eligible' ? 'high' : 'route'">{{ o.status === 'eligible' ? 'Eligible' : o.status === 'not_eligible' ? 'Not eligible' : 'Pending' }}</span></dd></div>
                </dl>
              </div>
              <p v-if="c.prediction && topFactor(c.prediction)" class="factor">
                Biggest factor: {{ topFactor(c.prediction).label.toLowerCase() }} ({{ topFactor(c.prediction).detail }}),
                <strong :class="topFactor(c.prediction).delta < 0 ? 'neg' : 'pos'">{{ topFactor(c.prediction).delta > 0 ? '+' : '' }}{{ topFactor(c.prediction).delta }}</strong> points
              </p>
              <div v-if="planFor(c)" class="plan">
                <span>Study plan</span>
                <div class="meter"><span :style="{ width: `${(planFor(c).done / planFor(c).total) * 100}%` }"></span></div>
                <span class="num">{{ planFor(c).done }}/{{ planFor(c).total }} tasks · opened {{ relativeDay(planFor(c).lastActive).toLowerCase() }}</span>
              </div>
            </li>
          </ul>
          <p class="note">Predictions are estimates from scores so far, shown to help staff; they are not a risk level.</p>
        </section>

        <section class="panel" aria-labelledby="hist-h">
          <div class="panel-head"><h2 id="hist-h">Course attempts</h2></div>
          <ul class="attempts">
            <li v-for="h in history2" :key="h.course.id">
              <span class="an">{{ h.course.name }}</span>
              <span class="ats">
                <span v-for="(a, i) in h.attempts" :key="i" class="at-chip" :class="a.inProgress ? 'now' : a.grade === 'U' ? 'fail' : 'pass'" :title="a.term">
                  {{ a.inProgress ? 'Now' : a.grade }}<small>{{ a.term }}</small>
                </span>
              </span>
            </li>
          </ul>
        </section>
      </div>

      <aside class="side">
        <section v-if="showForm" class="panel form-panel" aria-labelledby="form-h">
          <div class="panel-head"><h2 id="form-h">Log intervention</h2></div>
          <InterventionForm :row="r" :preset-type="preset" @save="save" @cancel="showForm = false" />
        </section>
        <p v-if="saved" class="toast" role="status"><Icon name="check" :size="18" /> {{ saved }}</p>

        <section class="panel" aria-labelledby="tl-h">
          <div class="panel-head">
            <h2 id="tl-h">Interventions</h2>
            <button v-if="!showForm" type="button" class="link" @click="openForm('call')"><Icon name="plus" :size="16" /> Add</button>
          </div>
          <Timeline :items="history" />
        </section>

        <section v-if="r.meta.ownerHistory.length" class="panel" aria-labelledby="own-h">
          <div class="panel-head"><h2 id="own-h">Owner history</h2></div>
          <ul class="owners">
            <li v-for="(h, i) in [...r.meta.ownerHistory].reverse()" :key="i">
              <strong>{{ STAFF[h.owner].name }}</strong>
              <span class="muted">{{ formatDate(h.at) }} by {{ STAFF[h.by]?.name || h.by }}. {{ h.reason }}</span>
            </li>
          </ul>
        </section>
      </aside>
    </div>
  </div>
  <div v-else class="page">
    <h1>Student not found</h1>
    <p class="muted">This student is not in the demo cohort. <RouterLink to="/staff/students">Back to the list</RouterLink></p>
  </div>
</template>

<style scoped>
.wide {
  max-width: 1240px;
}

.back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  text-decoration: none;
  font-weight: 500;
  margin-bottom: 14px;
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-areas: 'id owner' 'quick quick';
  gap: 16px 24px;
  padding: 22px 24px;
  border-radius: var(--r-l);
  background: var(--surface);
  border: 1px solid var(--line);
  border-left: 6px solid var(--ok);
}

.hero.high { border-left-color: var(--high); }
.hero.low { border-left-color: #e0952b; }

.id { grid-area: id; display: flex; flex-direction: column; gap: 12px; }
.hero :deep(.person strong) { font-size: 1.5rem; }
.hero :deep(.person .txt > span) { font-size: 0.9375rem; }

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.owner {
  grid-area: owner;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  text-align: right;
}

.lbl {
  font-size: 0.8125rem;
  color: var(--muted);
}

.owner strong {
  font-weight: 600;
}

.owner .none {
  color: var(--high);
}

.quick {
  grid-area: quick;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 0;
  background: none;
  color: var(--route-ink);
  font-weight: 500;
  cursor: pointer;
  padding: 2px;
}

.reassign {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  padding: 12px;
  border-radius: var(--r-m);
  background: var(--route-soft);
}

.reassign select,
.reassign input {
  padding: 8px 12px;
  border: 1px solid var(--line-2);
  border-radius: 10px;
  background: var(--surface);
}

.reassign input {
  flex: 1 1 220px;
}

.err {
  flex-basis: 100%;
  color: var(--high);
  font-size: 0.875rem;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.75fr) minmax(0, 1fr);
  gap: 20px;
  margin-top: 20px;
  align-items: start;
}

.main,
.side {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.small {
  font-size: 0.875rem;
}

.ink {
  color: var(--ink);
}

.reasons {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reasons > li + li {
  border-top: 1px solid var(--line);
  padding-top: 16px;
}

.rs-head {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}

.rs-head strong {
  display: block;
  font-weight: 600;
}

.rule {
  font-size: 0.8125rem;
  color: var(--muted);
}

.rs-ic {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: var(--paper);
  color: var(--ink-2);
}

.rs-ic.failed_twice,
.rs-ic.oppe_not_eligible { background: var(--high-soft); color: var(--high); }
.rs-ic.failed_once,
.rs-ic.plan_inactive { background: var(--low-soft); color: var(--low); }
.rs-ic.low_prediction { background: var(--route-soft); color: var(--route-ink); }

.acts {
  list-style: none;
  margin: 10px 0 0 48px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.acts li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-areas: 'cat btn' 'txt btn';
  gap: 4px 12px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--paper);
}

.acts li.done {
  background: var(--ok-soft);
}

.acts .chip {
  grid-area: cat;
  justify-self: start;
  background: var(--surface);
}

.at {
  grid-area: txt;
  font-size: 0.9375rem;
}

.share {
  grid-area: btn;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--line-2);
  background: var(--surface);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
}

.done .share {
  border-color: var(--ok);
  color: var(--ok);
}

.now {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.now > li + li {
  border-top: 1px solid var(--line);
  padding-top: 14px;
}

.n-top {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 6px 10px;
  align-items: center;
}

.n-top strong {
  font-weight: 600;
}

.n-body {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 20px;
  align-items: center;
  margin-top: 10px;
}

.pred {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px 6px 6px;
  border-radius: 12px;
  background: var(--ok-soft);
  --tone: var(--ok);
}

.pred.low { background: var(--low-soft); --tone: var(--low); }
.pred.fail { background: var(--high-soft); --tone: var(--high); }

.g {
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

.facts {
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
}

.facts dt {
  font-size: 0.75rem;
  color: var(--muted);
}

.facts dd {
  margin: 0;
  font-weight: 600;
}

.facts dd.bad {
  color: var(--high);
}

.factor {
  margin-top: 8px;
  font-size: 0.875rem;
  color: var(--ink-2);
}

.neg { color: var(--high); }
.pos { color: var(--ok); }

.plan {
  display: grid;
  grid-template-columns: auto minmax(80px, 1fr) auto;
  gap: 10px;
  align-items: center;
  margin-top: 10px;
  font-size: 0.875rem;
}

.attempts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attempts li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.an {
  font-size: 0.9375rem;
}

.ats {
  display: flex;
  gap: 4px;
}

.at-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 54px;
  height: 40px;
  padding: 3px 6px;
  border-radius: 8px;
  font-weight: 700;
  line-height: 1.15;
  background: var(--ok-soft);
  color: var(--ok);
}

.at-chip small {
  font-size: 0.6875rem;
  font-weight: 500;
}

.at-chip.fail { background: var(--high-soft); color: var(--high); }
.at-chip.now { background: var(--route-soft); color: var(--route-ink); }

.form-panel {
  border-color: var(--route);
  box-shadow: 0 0 0 3px var(--route-soft);
}

.toast {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: var(--r-m);
  background: var(--ok-soft);
  color: var(--ok);
  font-weight: 500;
}

.owners {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.owners li {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.owners strong {
  font-weight: 600;
}

.owners .muted {
  font-size: 0.875rem;
}

@media (max-width: 1060px) {
  .layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .hero {
    grid-template-columns: 1fr;
    grid-template-areas: 'id' 'owner' 'quick';
    padding: 18px;
  }
  .owner {
    align-items: flex-start;
    text-align: left;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px 10px;
  }
  .acts {
    margin-left: 0;
  }
  .acts li {
    grid-template-columns: 1fr;
    grid-template-areas: 'cat' 'txt' 'btn';
  }
  .share {
    justify-self: start;
  }
  .attempts li {
    grid-template-columns: 1fr;
    gap: 4px;
  }
  .ats {
    flex-wrap: wrap;
  }
}
</style>
