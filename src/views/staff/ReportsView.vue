<script setup>
import { computed, ref } from 'vue'
import { useStaffStore } from '../../stores/staff'
import { INTERVENTION_TYPES, OUTCOMES } from '../../data/actions'
import Icon from '../../components/Icon.vue'
import Kpi from '../../components/staff/Kpi.vue'
import StackBar from '../../components/staff/StackBar.vue'

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
const termMax = computed(() => Math.max(...byTerm.value.map((t) => t.n)))

const byType = computed(() =>
  Object.entries(INTERVENTION_TYPES).map(([key, t]) => {
    const list = items.value.filter((i) => i.type === key)
    return {
      key,
      label: t.label,
      icon: t.icon,
      n: list.length,
      parts: ['resolved', 'in_progress', 'no_response', 'escalated'].map((o) => ({ value: list.filter((i) => i.outcome === o).length, cls: { resolved: 'ok', in_progress: 'route', no_response: 'low', escalated: 'high' }[o], label: OUTCOMES[o].label })),
    }
  }),
)
const typeMax = computed(() => Math.max(1, ...byType.value.map((t) => t.n)))

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
        <div class="cols" role="img" :aria-label="byTerm.map((t) => `${t.term}: ${t.high} High, ${t.low} Low, ${t.ok} on track`).join('; ')">
          <div v-for="t in byTerm" :key="t.term" class="col">
            <div class="barwrap">
              <div class="stackv" :style="{ height: `${(t.n / termMax) * 180}px` }">
                <span class="ok" :style="{ flex: t.ok }"><b v-if="t.ok > 3">{{ t.ok }}</b></span>
                <span class="low" :style="{ flex: t.low }"><b v-if="t.low > 2">{{ t.low }}</b></span>
                <span class="high" :style="{ flex: t.high }"><b v-if="t.high > 2">{{ t.high }}</b></span>
              </div>
            </div>
            <span class="tl">{{ t.term }}</span>
          </div>
        </div>
        <p class="legend"><span><i class="sw high"></i>High</span><span><i class="sw low"></i>Low</span><span><i class="sw ok"></i>On track</span></p>
        <p class="note">Sep 2026 is today’s data; earlier terms are sample history.</p>
      </section>

      <section class="panel" aria-labelledby="type-h">
        <div class="panel-head">
          <h2 id="type-h">Outcomes by intervention type</h2>
        </div>
        <ul class="types">
          <li v-for="t in byType" :key="t.key">
            <span class="tn"><Icon :name="t.icon" :size="16" /> {{ t.label }} <span class="muted num">{{ t.n }}</span></span>
            <StackBar :parts="t.parts" :max="typeMax" :height="20" show-values />
          </li>
        </ul>
        <p class="legend"><span><i class="sw ok"></i>Resolved</span><span><i class="sw route"></i>In progress</span><span><i class="sw low"></i>No response</span><span><i class="sw high"></i>Escalated</span></p>
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
        <ul class="cohorts">
          <li v-for="c in cohorts" :key="c.level + c.cohort">
            <span class="cl"><strong>{{ c.level }}</strong>, {{ c.cohort }} <span class="muted num">({{ c.n }})</span></span>
            <StackBar
              :parts="[
                { value: c.ok, cls: 'ok', label: 'On track' },
                { value: c.risk, cls: 'low', label: 'At risk' },
                { value: c.behind, cls: 'high', label: 'Behind a milestone' },
              ]"
              :height="16"
            />
            <span class="pct num">{{ Math.round((c.ok / c.n) * 100) }}% on track</span>
          </li>
        </ul>
        <p class="legend"><span><i class="sw ok"></i>On track</span><span><i class="sw low"></i>At risk</span><span><i class="sw high"></i>Behind a milestone</span></p>
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

.cols {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
  padding: 0 12px;
}

.col {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.barwrap {
  width: 100%;
  height: 190px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  border-bottom: 1px solid var(--line-2);
}

.stackv {
  width: 100%;
  max-width: 88px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  border-radius: 8px 8px 0 0;
  overflow: hidden;
}

.stackv span {
  display: grid;
  place-items: center;
  min-height: 2px;
  font-size: 0.75rem;
}

.stackv b {
  font-weight: 700;
}

.stackv .ok { background: var(--ok); color: #fff; }
.stackv .low { background: #e0952b; color: var(--ink); }
.stackv .high { background: var(--high); color: #fff; }

.tl {
  font-size: 0.8125rem;
  color: var(--muted);
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  margin-top: 14px;
  font-size: 0.8125rem;
  color: var(--muted);
}

.types + .legend,
.cohorts + .legend {
  margin-top: 14px;
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

.sw.high { background: var(--high); }
.sw.low { background: #e0952b; }
.sw.ok { background: var(--ok); }
.sw.route { background: var(--route); }

.types,
.reasons,
.cohorts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tn {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  margin-bottom: 4px;
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
  background: var(--route);
  border-radius: inherit;
}

.reasons strong {
  text-align: right;
  font-weight: 600;
}

.cohorts li {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr) 100px;
  gap: 12px;
  align-items: center;
  font-size: 0.9375rem;
}

.cl strong {
  font-weight: 600;
}

.pct {
  font-size: 0.8125rem;
  color: var(--ink-2);
  text-align: right;
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
  .cohorts li,
  .reasons li {
    grid-template-columns: 1fr auto;
  }
  .cohorts li .stack,
  .reasons li .rb {
    grid-column: 1 / -1;
    grid-row: 2;
  }
  .pct {
    grid-row: 1;
    grid-column: 2;
  }
}
</style>
