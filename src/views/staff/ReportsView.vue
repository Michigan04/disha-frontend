<script setup>
import { computed, ref } from 'vue'
import { useStaffStore } from '../../stores/staff'
import { INTERVENTION_TYPES, OUTCOMES } from '../../data/actions'
import Icon from '../../components/Icon.vue'
import Kpi from '../../components/staff/Kpi.vue'
import Donut from '../../components/staff/Donut.vue'
import { VIZ } from '../../utils/viz'

// Outcome reporting (US-11) and the program progress overview (US-13). Totals only.
const staff = useStaffStore()
const level = ref('all')
const rows = computed(() => staff.rows.filter((r) => level.value === 'all' || r.level === level.value))
const ids = computed(() => new Set(rows.value.map((r) => r.id)))
const items = computed(() => staff.interventions.filter((i) => ids.value.has(i.studentId)))

const DAY = 864e5
const firstContact = computed(() => {
  const out = []
  for (const r of rows.value) {
    const h = staff.historyOf(r.id)
    if (h.length && r.meta.flaggedOn) out.push((h.at(-1).at - r.meta.flaggedOn) / DAY)
  }
  return out
})
const avgFirst = computed(() => (firstContact.value.length ? (firstContact.value.reduce((a, b) => a + b, 0) / firstContact.value.length).toFixed(1) : '–'))
const resolvedDays = computed(() => {
  const out = []
  for (const r of rows.value) {
    const h = staff.historyOf(r.id)
    if (h[0]?.outcome === 'resolved' && r.meta.flaggedOn) out.push((h[0].at - r.meta.flaggedOn) / DAY)
  }
  return out
})
const avgResolve = computed(() => (resolvedDays.value.length ? Math.round(resolvedDays.value.reduce((a, b) => a + b, 0) / resolvedDays.value.length) : '–'))
const withCase = computed(() => new Set(items.value.map((i) => i.studentId)).size)

// Risk level by term: Sep 2026 from today's data, earlier terms are sample history
const byTerm = computed(() => {
  const h = rows.value.filter((r) => r.risk.level === 'high').length
  const l = rows.value.filter((r) => r.risk.level === 'low').length
  const n = rows.value.length
  const make = (term, hh, ll, nn) => ({ term, high: hh, low: ll, ok: nn - hh - ll, n: nn })
  return [
    make('Jan 2026', Math.round(h * 0.5), Math.round(l * 0.7), Math.round(n * 0.78)),
    make('May 2026', Math.round(h * 0.75), Math.round(l * 1.15), Math.round(n * 0.9)),
    make('Sep 2026', h, l, n),
  ]
})
// Each term as a KPI pie: share at risk, with the change from the term before in points
const termKpis = computed(() =>
  byTerm.value.map((t, i, all) => {
    const pct = pctOf(t.high + t.low, t.n)
    const prev = i ? pctOf(all[i - 1].high + all[i - 1].low, all[i - 1].n) : null
    return {
      ...t,
      pct,
      delta: prev == null ? null : pct - prev,
      parts: [
        { key: 'high', label: 'High risk', value: t.high, color: VIZ.critical },
        { key: 'low', label: 'Low risk', value: t.low, color: VIZ.warning },
        { key: 'ok', label: 'On track', value: t.ok, color: VIZ.good },
      ],
    }
  }),
)
const signedPts = (d) => (d > 0 ? `+${d} pts` : d < 0 ? `\u2212${-d} pts` : 'no change')

// Outcome colours carry meaning: red escalated, mustard no response, blue under way, green resolved
const OUTCOME_COLOR = { escalated: VIZ.critical, no_response: VIZ.warning, in_progress: VIZ.active, resolved: VIZ.good }
const cohortPie = (c) => [
  { key: 'behind', label: 'Behind a milestone', value: c.behind, color: VIZ.critical },
  { key: 'risk', label: 'At risk', value: c.risk, color: VIZ.warning },
  { key: 'ok', label: 'On track', value: c.ok, color: VIZ.good },
]

const byType = computed(() =>
  Object.entries(INTERVENTION_TYPES).map(([key, t]) => {
    const list = items.value.filter((i) => i.type === key)
    return {
      key,
      label: t.label,
      icon: t.icon,
      n: list.length,
      resolved: list.filter((i) => i.outcome === 'resolved').length,
      parts: ['escalated', 'no_response', 'in_progress', 'resolved'].map((o) => ({ key: o, value: list.filter((i) => i.outcome === o).length, color: OUTCOME_COLOR[o], label: OUTCOMES[o].label })),
    }
  }),
)
const pctOf = (a, b) => (b ? Math.round((a / b) * 100) : 0)

const REASON_LABEL = {
  failed_twice: 'Same course failed twice',
  failed_once: 'A course failed once',
  oppe_not_eligible: 'Not eligible for an OPPE',
  low_prediction: 'Predicted to fail a course',
  plan_inactive: 'Study plan not opened for a week',
  behind_milestone: 'Missed a milestone',
  data_issue: 'Data to check',
}
const reasons = computed(() => {
  const count = {}
  for (const r of rows.value) for (const x of r.reasons) count[x.key] = (count[x.key] || 0) + 1
  return Object.entries(count).map(([key, n]) => ({ key, n, label: REASON_LABEL[key] })).sort((a, b) => b.n - a.n)
})
const reasonMax = computed(() => Math.max(1, ...reasons.value.map((r) => r.n)))

// Progress by level and admission cohort
const cohorts = computed(() => {
  const map = {}
  for (const r of rows.value) {
    const k = `${r.levelLabel}|${r.cohort}`
    map[k] = map[k] || { level: r.levelLabel, cohort: r.cohort, ok: 0, risk: 0, behind: 0, n: 0 }
    const m = map[k]
    m.n += 1
    if (r.milestones.some((x) => x.state === 'missed')) m.behind += 1
    else if (r.risk.level !== 'none') m.risk += 1
    else m.ok += 1
  }
  const order = (c) => ['Jan', 'May', 'Sep'].indexOf(c.split(' ')[0]) + Number(c.split(' ')[1]) * 3
  return Object.values(map).sort((a, b) => a.level.localeCompare(b.level) * -1 || order(b.cohort) - order(a.cohort))
})
</script>

<template>
  <div class="page wide">
    <header class="page-head">
      <h1>Reports</h1>
      <p>Risk trends, what was done, and what happened next. Totals only: no student names on this page.</p>
    </header>

    <div class="seg" role="group" aria-label="Level">
      <button v-for="o in [['all', 'All levels'], ['foundation', 'Foundation'], ['diploma', 'Diploma']]" :key="o[0]" type="button" :class="{ on: level === o[0] }" :aria-pressed="level === o[0]" @click="level = o[0]">{{ o[1] }}</button>
    </div>

    <div class="kpis">
      <Kpi :value="withCase" label="Students with an intervention" :sub="`${items.length} interventions logged`" icon="board" />
      <Kpi :value="avgFirst" label="Days to first contact" sub="Average, from the risk flag" icon="clock" />
      <Kpi :value="avgResolve" label="Days to resolution" :sub="`${resolvedDays.length} resolved ${resolvedDays.length === 1 ? 'case' : 'cases'}`" icon="check" tone="ok" />
      <Kpi value="41%" label="Risk fell within a term" sub="May 2026 cases with an intervention (sample)" icon="progress" tone="ok" />
    </div>
    <p class="caveat"><Icon name="alert" :size="16" /> “Risk fell within a term” is a recorded outcome. It does not prove the intervention caused it.</p>

    <div class="grid">
      <section class="panel" aria-labelledby="term-h">
        <div class="panel-head">
          <h2 id="term-h">Risk level by term</h2>
          <span class="muted small">Students</span>
        </div>
        <ul class="term-kpis">
          <li v-for="(t, i) in termKpis" :key="t.term" :class="{ now: i === termKpis.length - 1 }">
            <span class="tk-term">{{ t.term }}<span v-if="i === termKpis.length - 1" class="now-tag">Now</span></span>
            <Donut :parts="t.parts" :center="`${t.pct}%`" center-sub="at risk" :size="116" :thickness="24" :legend="false" />
            <span v-if="t.delta != null" class="tk-delta num" :class="t.delta > 0 ? 'bad' : t.delta < 0 ? 'good' : ''">{{ signedPts(t.delta) }} vs last term</span>
            <span v-else class="tk-delta num">First term shown</span>
            <span class="muted num small">{{ t.high }} High · {{ t.low }} Low of {{ t.n }}</span>
          </li>
        </ul>
        <p class="legend"><span><i class="sw high"></i>High</span><span><i class="sw low"></i>Low</span><span><i class="sw ok"></i>On track</span></p>
        <p class="note">Sep 2026 is today’s data; earlier terms are sample history.</p>
      </section>

      <section class="panel" aria-labelledby="type-h">
        <div class="panel-head">
          <h2 id="type-h">Outcomes by intervention type</h2>
        </div>
        <ul class="pies four">
          <li v-for="t in byType" :key="t.key">
            <Donut :parts="t.parts" :center="t.n ? `${pctOf(t.resolved, t.n)}%` : '–'" center-sub="resolved" :size="96" :thickness="22" :legend="false" />
            <span class="pn"><Icon :name="t.icon" :size="15" /> {{ t.label }}</span>
            <span class="muted num small">{{ t.n }} logged</span>
          </li>
        </ul>
        <p class="legend"><span><i class="sw high"></i>Escalated</span><span><i class="sw low"></i>No response</span><span><i class="sw active"></i>In progress</span><span><i class="sw ok"></i>Resolved</span></p>
      </section>

      <section class="panel" aria-labelledby="why-h">
        <div class="panel-head">
          <h2 id="why-h">Most common risk reasons</h2>
        </div>
        <ul class="reasons">
          <li v-for="r in reasons" :key="r.key">
            <span>{{ r.label }}</span>
            <div class="rb"><span :style="{ width: `${(r.n / reasonMax) * 100}%` }"></span></div>
            <strong class="num">{{ r.n }}</strong>
          </li>
        </ul>
      </section>

      <section class="panel" aria-labelledby="co-h">
        <div class="panel-head">
          <h2 id="co-h">Progress by level and admission cohort</h2>
        </div>
        <ul class="pies">
          <li v-for="c in cohorts" :key="c.level + c.cohort">
            <Donut :parts="cohortPie(c)" :center="`${pctOf(c.ok, c.n)}%`" center-sub="on track" :size="104" :thickness="22" :legend="false" />
            <span class="pc"><strong>{{ c.level }}</strong>, {{ c.cohort }}</span>
            <span class="muted num small">{{ c.n }} students</span>
          </li>
        </ul>
        <p class="legend"><span><i class="sw high"></i>Behind a milestone</span><span><i class="sw low"></i>At risk</span><span><i class="sw ok"></i>On track</span></p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.wide {
  max-width: 1240px;
}

.seg {
  display: inline-flex;
  padding: 4px;
  border-radius: 12px;
  background: var(--surface);
  border: 1px solid var(--line);
  margin-bottom: 18px;
}

.seg button {
  border: 0;
  background: none;
  padding: 7px 14px;
  border-radius: 9px;
  font-weight: 500;
  color: var(--ink-2);
  cursor: pointer;
}

.seg button.on {
  background: var(--ink);
  color: #fff;
}

.kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.caveat {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 0 20px;
  font-size: 0.875rem;
  color: var(--muted);
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  align-items: start;
}

.small {
  font-size: 0.875rem;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  margin-top: 14px;
  font-size: 0.8125rem;
  color: var(--muted);
}

.term-kpis {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.term-kpis li {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 8px 16px;
  border-radius: var(--r-m);
  border: 1px solid var(--line);
  background: var(--paper);
  text-align: center;
  font-size: 0.875rem;
  line-height: 1.3;
}

.term-kpis li.now {
  background: var(--surface);
  border-color: var(--route);
  box-shadow: inset 0 3px 0 var(--route);
}

.tk-term {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 0.9375rem;
}

.now-tag {
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--route);
  color: #fff;
}

.tk-delta {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--line);
  color: var(--ink-2);
}

.tk-delta.bad {
  background: var(--high-soft);
  color: var(--high);
}

.tk-delta.good {
  background: var(--ok-soft);
  color: var(--ok);
}

@media (max-width: 560px) {
  .term-kpis {
    grid-template-columns: 1fr;
  }
}

.term-kpis + .legend,
.pies + .legend {
  margin-top: 18px;
}

.pies {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 18px 12px;
}

.pies li {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 2px;
  font-size: 0.875rem;
  line-height: 1.3;
}

.pies li > :first-child {
  margin-bottom: 6px;
}

.pn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-weight: 500;
}

.pies.four {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.pc strong {
  font-weight: 600;
}

@media (max-width: 560px) {
  .pies.four {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.sw {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  display: inline-block;
}

.sw.high { background: var(--viz-critical); }
.sw.low { background: var(--viz-warning); }
.sw.ok { background: var(--viz-good); }
.sw.active { background: var(--viz-active); }

.reasons {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reasons li {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr) 28px;
  gap: 12px;
  align-items: center;
  font-size: 0.9375rem;
}

.rb {
  height: 10px;
  border-radius: 999px;
  background: var(--line);
  overflow: hidden;
}

.rb span {
  display: block;
  height: 100%;
  background: var(--ink-2);
  border-radius: inherit;
}

.reasons strong {
  text-align: right;
  font-weight: 600;
}

@media (max-width: 1000px) {
  .grid {
    grid-template-columns: 1fr;
  }
  .kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .reasons li {
    grid-template-columns: 1fr auto;
  }
  .reasons li .rb {
    grid-column: 1 / -1;
    grid-row: 2;
  }
}
</style>
