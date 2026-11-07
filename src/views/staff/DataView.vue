<script setup>
import { computed, ref } from 'vue'
import { useStaffStore } from '../../stores/staff'
import { CATEGORIES, SAMPLE_FILES, parseCsv, templateCsv, validate } from '../../utils/csv'
import { formatDate, formatTime, relativeDay } from '../../utils/dates'
import Icon from '../../components/Icon.vue'

// Data uploads (US-09) and system status (US-15). Files are read in the browser only.
const staff = useStaffStore()
const cat = ref('scores')
const fileName = ref('')
const result = ref(null)
const error = ref('')
const over = ref(false)
const done = ref(null)
const input = ref(null)

async function readFile(file) {
  if (!file) return
  error.value = ''
  done.value = null
  if (!/\.csv$/i.test(file.name)) return (error.value = 'Choose a .csv file.')
  if (file.size > 5 * 1024 * 1024) return (error.value = 'That file is over 5 MB. Split it into smaller files.')
  check(file.name, await file.text())
}

function check(name, text) {
  fileName.value = name
  const res = validate(parseCsv(text), cat.value)
  if (res.error) {
    result.value = null
    error.value = res.error
  } else result.value = res
}

function useSample() {
  cat.value = 'scores'
  done.value = null
  error.value = ''
  check('sample_week8_scores.csv', SAMPLE_FILES.scores)
}

function onDrop(e) {
  over.value = false
  readFile(e.dataTransfer.files[0])
}

function download() {
  try {
    const blob = new Blob([templateCsv(cat.value)], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `disha_template_${cat.value}.csv`
    a.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch {
    error.value = 'The template could not be downloaded in this browser.'
  }
}

function confirm() {
  done.value = staff.confirmImport(fileName.value, result.value)
  result.value = null
  if (input.value) input.value.value = ''
}

function cancel() {
  result.value = null
  fileName.value = ''
  if (input.value) input.value.value = ''
}

const FRESHNESS = computed(() => [
  { label: 'Term results', last: 'May 2026', ok: true, note: 'Latest finished term' },
  { label: 'Course registrations', last: 'Sep 2026', ok: true, note: 'Current term' },
  { label: 'Weekly assignment scores', last: staff.imports.find((i) => i.category === 'Weekly assignment scores')?.term === 'Sep 2026' ? 'Sep 2026, week 7' : 'Sep 2026', ok: true, note: 'Up to date' },
  { label: 'Project stages', last: 'May 2026', ok: false, note: 'Not updated this term' },
])

const JOB = { succeeded: { label: 'Succeeded', cls: 'ok' }, failed: { label: 'Failed', cls: 'high' }, pending: { label: 'Scheduled', cls: 'route' }, running: { label: 'Running', cls: 'low' } }

const SAMPLES = ref([
  { id: 1, to: 'A Low-risk student, Statistics II', text: 'You are close to passing Statistics II. Students who passed after one failed attempt usually did two timed past papers before each quiz. This week, try the Week 7 practice set.', flagged: false },
  { id: 2, to: 'A High-risk student, Python', text: 'Your OPPE 1 eligibility depends on your weekly assignment average. Weeks 8 and 9 still count towards OPPE 2, so submitting both can make you eligible.', flagged: false },
])
</script>

<template>
  <div class="page wide">
    <header class="page-head">
      <h1>Data and system</h1>
      <p>Upload term data as CSV, check it before it counts, and see that imports, alerts and the AI parts are working.</p>
    </header>

    <section class="panel up" aria-labelledby="up-h">
      <div class="panel-head">
        <h2 id="up-h">Upload a file</h2>
        <button type="button" class="link" @click="download"><Icon name="download" :size="16" /> Download the template</button>
      </div>

      <div class="cats" role="radiogroup" aria-label="What the file contains">
        <label v-for="(c, key) in CATEGORIES" :key="key" :class="{ on: cat === key }">
          <input v-model="cat" type="radio" name="cat" :value="key" @change="cancel" />
          <strong>{{ c.label }}</strong>
          <code>{{ c.columns.join(', ') }}</code>
        </label>
      </div>

      <div
        v-if="!result"
        class="drop"
        :class="{ over }"
        @dragover.prevent="over = true"
        @dragleave="over = false"
        @drop.prevent="onDrop"
      >
        <span class="d-ic"><Icon name="upload" :size="26" /></span>
        <p><strong>Drop a CSV file here</strong> or</p>
        <div class="d-btns">
          <label class="btn">
            Choose file
            <input ref="input" type="file" accept=".csv,text/csv" class="sr-only" @change="readFile($event.target.files[0])" />
          </label>
          <button type="button" class="btn quiet" @click="useSample"><Icon name="file" :size="18" /> Try a sample file</button>
        </div>
        <p class="muted small">Checked in this browser. Nothing is uploaded in the demo.</p>
      </div>
      <p v-if="error" class="err" role="alert"><Icon name="alert" :size="18" /> {{ error }}</p>

      <div v-if="result" class="check" aria-live="polite">
        <div class="c-head">
          <span class="f"><Icon name="file" :size="18" /> {{ fileName }}</span>
          <span class="muted">{{ result.category }} · {{ result.terms.join(', ') || 'no term found' }}</span>
        </div>
        <div class="tiles">
          <div class="t"><span class="v num">{{ result.total }}</span><span>rows in the file</span></div>
          <div class="t ok"><span class="v num">{{ result.accepted.length }}</span><span>will be imported</span></div>
          <div class="t" :class="{ bad: result.rejected.length }"><span class="v num">{{ result.rejected.length }}</span><span>rejected</span></div>
        </div>
        <div class="ratio" role="img" :aria-label="`${result.accepted.length} accepted, ${result.rejected.length} rejected`">
          <span class="a" :style="{ flex: result.accepted.length }"></span>
          <span class="r" :style="{ flex: result.rejected.length }"></span>
        </div>
        <div v-if="result.rejected.length" class="rej">
          <h3>Rejected rows</h3>
          <ul>
            <li v-for="x in result.rejected" :key="x.line">
              <span class="ln num">Row {{ x.line }}</span>
              <span class="why">{{ x.reason }}</span>
              <code>{{ x.raw }}</code>
            </li>
          </ul>
        </div>
        <div class="c-actions">
          <button class="btn" type="button" :disabled="!result.accepted.length" @click="confirm"><Icon name="check" :size="18" /> Import {{ result.accepted.length }} rows and recalculate risk</button>
          <button class="btn quiet" type="button" @click="cancel">Cancel</button>
        </div>
      </div>

      <p v-if="done" class="toast" role="status"><Icon name="check" :size="18" /> Imported {{ done.accepted }} rows from {{ done.file }}. Risk recalculation has started; see System status below.</p>
    </section>

    <div class="grid">
      <section class="panel" aria-labelledby="hist-h">
        <div class="panel-head"><h2 id="hist-h">Import history</h2></div>
        <ul class="imports">
          <li v-for="i in staff.imports" :key="i.id">
            <span class="i-ic"><Icon name="file" :size="18" /></span>
            <span class="i-main">
              <strong>{{ i.category }}, {{ i.term }}</strong>
              <span class="muted">{{ i.file }} · {{ formatDate(i.at) }}, {{ formatTime(i.at) }} · {{ i.by }}</span>
            </span>
            <span class="i-n num"><b>{{ i.accepted.toLocaleString('en-IN') }}</b> in<template v-if="i.rejected">, <em>{{ i.rejected }} rejected</em></template></span>
          </li>
        </ul>
      </section>

      <section class="panel" aria-labelledby="fresh-h">
        <div class="panel-head"><h2 id="fresh-h">Data freshness</h2></div>
        <ul class="fresh">
          <li v-for="d in FRESHNESS" :key="d.label" :class="{ stale: !d.ok }">
            <span class="dot"></span>
            <span class="fm"><strong>{{ d.label }}</strong><span class="muted">{{ d.note }}</span></span>
            <span class="chip" :class="d.ok ? 'ok' : 'low'">{{ d.last }}</span>
          </li>
        </ul>
      </section>

      <section class="panel" aria-labelledby="sys-h">
        <div class="panel-head"><h2 id="sys-h">System status</h2></div>
        <ul class="jobs">
          <li v-for="j in staff.jobs.slice(0, 6)" :key="j.id">
            <span class="chip" :class="JOB[j.status].cls">{{ JOB[j.status].label }}</span>
            <span class="jm"><strong>{{ j.name }}</strong><span class="muted">{{ j.detail }}</span></span>
            <span class="muted when">{{ relativeDay(j.at) }}, {{ formatTime(j.at) }}</span>
          </li>
        </ul>
      </section>

      <section class="panel" aria-labelledby="ai-h">
        <div class="panel-head"><h2 id="ai-h">AI components</h2></div>
        <div class="model">
          <div>
            <strong>Score prediction model</strong>
            <span class="muted">Version 0.3 · recorded with every risk assessment</span>
          </div>
          <div class="acc" role="img" aria-label="81 percent accurate last term">
            <svg viewBox="0 0 36 36" width="56" height="56"><circle cx="18" cy="18" r="15" fill="none" stroke="var(--line)" stroke-width="5" /><circle cx="18" cy="18" r="15" fill="none" stroke="var(--ok)" stroke-width="5" stroke-dasharray="94.2" :stroke-dashoffset="94.2 * 0.19" transform="rotate(-90 18 18)" stroke-linecap="round" /></svg>
            <span><b class="num">81%</b> right about pass or fail last term</span>
          </div>
        </div>
        <div class="llm">
          <div>
            <strong>Language model for student messages</strong>
            <span class="muted">{{ staff.llmEnabled ? 'On: students get plain-language guidance written by the model.' : 'Off: students see the rule-based reasons only.' }}</span>
          </div>
          <button type="button" role="switch" class="switch" :aria-checked="staff.llmEnabled" @click="staff.setLLM(!staff.llmEnabled)">
            <span class="sr-only">Language model for student messages</span>
          </button>
        </div>
        <h3>Review a sample of messages</h3>
        <ul class="samples">
          <li v-for="m in SAMPLES" :key="m.id" :class="{ flagged: m.flagged }">
            <span class="muted to">To: {{ m.to }}</span>
            <p>{{ m.text }}</p>
            <button type="button" class="flag" :aria-pressed="m.flagged" @click="m.flagged = !m.flagged; staff.log('AI review', `Sample message ${m.flagged ? 'flagged' : 'unflagged'}: ${m.to}`)">
              <Icon name="flag" :size="15" /> {{ m.flagged ? 'Flagged for review' : 'Flag as wrong' }}
            </button>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style scoped>
.wide {
  max-width: 1240px;
}

.link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: none;
  color: var(--route-ink);
  font-weight: 500;
  cursor: pointer;
}

.small {
  font-size: 0.875rem;
}

.cats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.cats label {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--line-2);
  cursor: pointer;
  min-width: 0;
}

.cats label.on {
  border-color: var(--route);
  background: var(--route-soft);
}

.cats label:focus-within {
  outline: 2px solid var(--route);
  outline-offset: 2px;
}

.cats input {
  position: absolute;
  opacity: 0;
}

.cats strong {
  font-weight: 600;
}

.cats code,
.rej code {
  font-family: ui-monospace, Menlo, monospace;
  font-size: 0.75rem;
  color: var(--muted);
  overflow-wrap: anywhere;
}

.drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 30px 20px;
  border: 2px dashed var(--line-2);
  border-radius: var(--r-m);
  text-align: center;
  background: var(--paper);
  transition: border-color 0.15s, background 0.15s;
}

.drop.over {
  border-color: var(--route);
  background: var(--route-soft);
}

.d-ic {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--surface);
  color: var(--route);
}

.d-btns {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.d-btns label.btn {
  cursor: pointer;
}

.d-btns label.btn:focus-within {
  outline: 2px solid var(--route);
  outline-offset: 2px;
}

.err {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--high-soft);
  color: var(--high);
}

.check {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.c-head {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  align-items: center;
}

.f {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.tiles {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.t {
  display: flex;
  flex-direction: column;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--paper);
  line-height: 1.3;
}

.t .v {
  font-size: 1.75rem;
  font-weight: 600;
}

.t.ok .v { color: var(--ok); }
.t.bad .v { color: var(--high); }

.ratio {
  display: flex;
  gap: 3px;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
}

.ratio .a { background: var(--ok); }
.ratio .r { background: var(--high); }

.rej h3 {
  font-size: 1rem;
  margin-bottom: 8px;
}

.rej ul {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
}

.rej li {
  display: grid;
  grid-template-columns: 70px minmax(0, 1.3fr) minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 8px 12px;
  font-size: 0.9375rem;
}

.rej li + li {
  border-top: 1px solid var(--line);
}

.ln {
  font-weight: 600;
  color: var(--high);
}

.c-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.toast {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding: 10px 14px;
  border-radius: var(--r-m);
  background: var(--ok-soft);
  color: var(--ok);
  font-weight: 500;
}

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  margin-top: 20px;
  align-items: start;
}

.imports,
.fresh,
.jobs,
.samples {
  list-style: none;
  margin: 0;
  padding: 0;
}

.imports li,
.jobs li {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 10px 0;
}

.imports li + li,
.jobs li + li,
.fresh li + li {
  border-top: 1px solid var(--line);
}

.i-ic {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: var(--route-soft);
  color: var(--route-ink);
}

.i-main,
.jm,
.fm {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  min-width: 0;
}

.i-main strong,
.jm strong,
.fm strong {
  font-weight: 600;
}

.i-main .muted,
.jm .muted,
.fm .muted {
  font-size: 0.8125rem;
}

.i-n {
  font-size: 0.875rem;
  text-align: right;
}

.i-n em {
  font-style: normal;
  color: var(--high);
}

.fresh li {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 10px 0;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--ok);
}

.stale .dot {
  background: var(--low-fill);
}

.when {
  font-size: 0.8125rem;
  text-align: right;
}

.model,
.llm {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  padding: 12px 0;
}

.model > div:first-child,
.llm > div:first-child {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.model strong,
.llm strong {
  font-weight: 600;
}

.model .muted,
.llm .muted {
  font-size: 0.875rem;
}

.llm {
  border-top: 1px solid var(--line);
}

.acc {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.8125rem;
  max-width: 190px;
  line-height: 1.3;
}

.acc b {
  font-size: 1rem;
}

.switch {
  position: relative;
  flex: none;
  width: 52px;
  height: 30px;
  border-radius: 999px;
  border: 0;
  background: var(--line-2);
  cursor: pointer;
  transition: background 0.15s;
}

.switch::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: transform 0.15s;
}

.switch[aria-checked='true'] {
  background: var(--ok);
}

.switch[aria-checked='true']::after {
  transform: translateX(22px);
}

.panel h3 {
  font-size: 0.9375rem;
  margin: 14px 0 8px;
}

.samples {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.samples li {
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--paper);
  font-size: 0.9375rem;
}

.samples li.flagged {
  background: var(--high-soft);
}

.to {
  font-size: 0.8125rem;
}

.flag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-top: 8px;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid var(--line-2);
  background: var(--surface);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
}

.flagged .flag {
  border-color: var(--high);
  color: var(--high);
}

@media (max-width: 1000px) {
  .grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 700px) {
  .cats {
    grid-template-columns: 1fr;
  }
  .rej li {
    grid-template-columns: 60px minmax(0, 1fr);
  }
  .rej code {
    grid-column: 1 / -1;
  }
  .imports li,
  .jobs li {
    grid-template-columns: auto minmax(0, 1fr);
  }
  .i-n,
  .when {
    grid-column: 2;
    text-align: left;
  }
  .model {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
