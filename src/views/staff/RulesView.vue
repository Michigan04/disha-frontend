<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useStaffStore } from '../../stores/staff'
import { PERMISSIONS } from '../../data/staff'
import { ROLES } from '../../data/accounts'
import { LEVEL_RULES } from '../../data/rules'
import { formatDate } from '../../utils/dates'
import Icon from '../../components/Icon.vue'
import RiskChip from '../../components/staff/RiskChip.vue'

// Milestone and risk rules (US-09), and users and access (US-15).
const auth = useAuthStore()
const staff = useStaffStore()
const tab = ref('rules')

const draft = reactive(JSON.parse(JSON.stringify(staff.rules)))
const reason = ref('')
const preview = ref(null)
const applied = ref('')

watch(draft, () => (preview.value = null), { deep: true })
watch(reason, () => (preview.value = null))
const changed = computed(() => JSON.stringify({ ...draft, version: 0 }) !== JSON.stringify({ ...staff.rules, version: 0 }))

function check() {
  applied.value = ''
  preview.value = staff.previewRules(draft)
  if (reason.value.trim().length < 10) preview.value.problems.push('Write the reason for this change (10 characters or more). It is saved with the rule.')
}

function apply() {
  const changes = staff.applyRules(draft, reason.value.trim())
  applied.value = `Rules v${staff.rules.version} saved. ${changes.length} ${changes.length === 1 ? 'student changed' : 'students changed'} risk level at the recalculation.`
  preview.value = null
  reason.value = ''
}

function reset() {
  Object.assign(draft, JSON.parse(JSON.stringify(staff.rules)))
  reason.value = ''
  preview.value = null
}

const ROLE_KEYS = Object.keys(ROLES)
</script>

<template>
  <div class="page wide">
    <header class="page-head">
      <h1>Rules and access</h1>
      <p>Change when a student counts as at risk and what each milestone needs, without changing code. Manage who can see what.</p>
    </header>

    <div class="tabs" role="tablist">
      <button type="button" role="tab" :aria-selected="tab === 'rules'" :class="{ on: tab === 'rules' }" @click="tab = 'rules'"><Icon name="sliders" :size="18" /> Risk and milestone rules</button>
      <button type="button" role="tab" :aria-selected="tab === 'access'" :class="{ on: tab === 'access' }" @click="tab = 'access'"><Icon name="shield" :size="18" /> Users and access</button>
    </div>

    <template v-if="tab === 'rules'">
      <div class="current">
        <span class="ver num">v{{ staff.rules.version }}</span>
        <div>
          <strong>Rules in force from {{ staff.rules.effective }}</strong>
          <span class="muted">Last recalculated {{ formatDate(staff.lastRecalc) }}. A change applies from the next recalculation and keeps the old version in the history.</span>
        </div>
      </div>

      <p v-if="applied" class="toast" role="status"><Icon name="check" :size="18" /> {{ applied }}</p>

      <div class="layout">
        <div class="col">
          <section class="panel" aria-labelledby="risk-h">
            <div class="panel-head"><h2 id="risk-h">Risk levels</h2></div>
            <div class="rule high">
              <RiskChip level="high" />
              <span>when the same course is failed</span>
              <input v-model.number="draft.highFails" type="number" min="1" max="5" aria-label="Failed attempts for High risk" />
              <span>times</span>
            </div>
            <div class="rule low">
              <RiskChip level="low" />
              <span>when a course is failed</span>
              <input v-model.number="draft.lowFails" type="number" min="1" max="5" aria-label="Failed attempts for Low risk" />
              <span>{{ draft.lowFails === 1 ? 'time' : 'times' }}</span>
            </div>
            <div class="rule">
              <span class="chip route">OPPE</span>
              <span>eligible with a weekly assignment average of at least</span>
              <input v-model.number="draft.oppeMin" type="number" min="0" max="100" aria-label="OPPE assignment threshold" />
            </div>
          </section>

          <section v-for="(list, lv) in draft.milestones" :key="lv" class="panel" :aria-labelledby="`m-${lv}`">
            <div class="panel-head">
              <h2 :id="`m-${lv}`">{{ LEVEL_RULES[lv].label }} milestones</h2>
              <span class="muted small">Term limit {{ LEVEL_RULES[lv].limitTerms }}</span>
            </div>
            <div class="ms">
              <div class="ms-row th">
                <span>#</span><span>By term</span><span>Courses</span><span v-if="lv === 'diploma'">Projects</span>
              </div>
              <div v-for="(m, i) in list" :key="i" class="ms-row">
                <span class="n num">{{ i + 1 }}</span>
                <input v-model.number="m.byTerm" type="number" min="1" :max="LEVEL_RULES[lv].limitTerms" :aria-label="`Milestone ${i + 1}: by term`" />
                <input v-model.number="m.courses" type="number" min="0" :aria-label="`Milestone ${i + 1}: courses`" />
                <input v-if="lv === 'diploma'" v-model.number="m.projects" type="number" min="0" :aria-label="`Milestone ${i + 1}: projects`" />
              </div>
            </div>
          </section>
        </div>

        <div class="col">
          <section class="panel save" aria-labelledby="save-h">
            <div class="panel-head"><h2 id="save-h">Save a new version</h2></div>
            <label class="field">
              <span>In force from</span>
              <select v-model="draft.effective">
                <option>Sep 2026</option>
                <option>Jan 2027</option>
                <option>May 2027</option>
              </select>
            </label>
            <label class="field">
              <span>Reason, with the policy it follows</span>
              <textarea v-model="reason" rows="3" placeholder="For example: program office notice of 12 Oct 2026 on repeated failures"></textarea>
            </label>
            <div class="btns">
              <button class="btn quiet" type="button" :disabled="!changed" @click="check"><Icon name="eye" :size="18" /> Check the effect</button>
              <button class="btn" type="button" :disabled="!preview || preview.problems.length > 0" @click="apply"><Icon name="check" :size="18" /> Apply</button>
              <button v-if="changed" class="link" type="button" @click="reset">Undo changes</button>
            </div>
            <p v-if="!changed" class="muted small">Change a value on the left to start.</p>

            <div v-if="preview" class="preview" aria-live="polite">
              <ul v-if="preview.problems.length" class="problems">
                <li v-for="p in preview.problems" :key="p"><Icon name="cross" :size="16" /> {{ p }}</li>
              </ul>
              <template v-else>
                <p class="ok-line"><Icon name="check" :size="18" /> The rules are consistent.</p>
                <p v-if="!preview.changes.length" class="muted">No student would change risk level.</p>
                <template v-else>
                  <p><strong class="num">{{ preview.changes.length }}</strong> {{ preview.changes.length === 1 ? 'student would' : 'students would' }} change risk level:</p>
                  <ul class="moves">
                    <li v-for="c in preview.changes" :key="c.id">
                      <span>{{ c.name }}</span>
                      <RiskChip :level="c.from" /> <Icon name="chevron" :size="14" /> <RiskChip :level="c.to" />
                    </li>
                  </ul>
                </template>
              </template>
            </div>
          </section>

          <section class="panel" aria-labelledby="hist-h">
            <div class="panel-head"><h2 id="hist-h">Rule history</h2></div>
            <ol class="history">
              <li v-for="h in [...staff.ruleHistory].reverse()" :key="h.version" :class="{ cur: h.version === staff.rules.version }">
                <span class="hv num">v{{ h.version }}</span>
                <div>
                  <strong>From {{ h.effective }}</strong>
                  <p>{{ h.summary }}</p>
                  <span class="muted">{{ h.by }}, {{ formatDate(h.at) }}. Reason: {{ h.reason }}</span>
                </div>
              </li>
            </ol>
          </section>
        </div>
      </div>
    </template>

    <template v-else>
      <section class="panel" aria-labelledby="perm-h">
        <div class="panel-head"><h2 id="perm-h">What each role can do</h2></div>
        <div class="matrix" role="table" aria-label="Permissions by role">
          <div class="mx-row th" role="row">
            <span role="columnheader">Permission</span>
            <span v-for="k in ROLE_KEYS" :key="k" role="columnheader">{{ ROLES[k].label }}</span>
          </div>
          <div v-for="p in PERMISSIONS" :key="p.key" class="mx-row" role="row">
            <span role="cell">{{ p.label }}</span>
            <span v-for="k in ROLE_KEYS" :key="k" role="cell" class="mx-c">
              <span v-if="p.roles.includes(k)" class="yes" :aria-label="'Yes'"><Icon name="check" :size="16" /></span>
              <span v-else class="no" aria-label="No">–</span>
            </span>
          </div>
        </div>
        <p class="note">No student can see another student’s record. Instructors see only students referred to their own course.</p>
      </section>

      <section class="panel users" aria-labelledby="users-h">
        <div class="panel-head">
          <h2 id="users-h">Staff accounts</h2>
          <span class="muted small">Student accounts come from the registrations import ({{ staff.students.length }} in the demo)</span>
        </div>
        <ul>
          <li v-for="u in staff.users" :key="u.email" :class="{ off: !u.active }">
            <span class="u-main"><strong>{{ u.name }}</strong><span class="muted">{{ u.email }} · {{ u.title }}</span></span>
            <label>
              <span class="sr-only">Role for {{ u.name }}</span>
              <select :value="u.role" :disabled="u.email === `${auth.user.staffId}@disha.demo`" @change="staff.setUser(u.email, { role: $event.target.value })">
                <option v-for="k in ROLE_KEYS.filter((x) => x !== 'student')" :key="k" :value="k">{{ ROLES[k].label }}</option>
              </select>
            </label>
            <button type="button" class="btn quiet sm" :disabled="u.email === `${auth.user.staffId}@disha.demo`" @click="staff.setUser(u.email, { active: !u.active })">
              {{ u.active ? 'Deactivate' : 'Reactivate' }}
            </button>
          </li>
        </ul>
        <p class="note">Every change here is saved in the audit log.</p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.wide {
  max-width: 1240px;
}

.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 20px;
  overflow-x: auto;
}

.tabs button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
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

.tabs button.on {
  color: var(--route-ink);
  border-bottom-color: var(--route);
  font-weight: 600;
}

.current {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border-radius: var(--r-m);
  background: var(--surface);
  border: 1px solid var(--line);
  margin-bottom: 16px;
}

.current > div {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.current strong {
  font-weight: 600;
}

.current .muted {
  font-size: 0.875rem;
}

.ver,
.hv {
  flex: none;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: var(--ink);
  color: #fff;
  font-weight: 700;
  font-size: 1.125rem;
}

.toast {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 14px;
  border-radius: var(--r-m);
  background: var(--ok-soft);
  color: var(--ok);
  font-weight: 500;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.col {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.small {
  font-size: 0.875rem;
}

.rule {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--paper);
}

.rule + .rule {
  margin-top: 8px;
}

.rule input,
.ms input {
  width: 70px;
  padding: 7px 10px;
  border: 1px solid var(--line-2);
  border-radius: 9px;
  background: var(--surface);
  font-weight: 600;
  text-align: center;
}

.ms {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ms-row {
  display: grid;
  grid-template-columns: 28px repeat(3, 80px);
  gap: 10px;
  align-items: center;
}

.ms-row.th {
  font-size: 0.8125rem;
  color: var(--muted);
  font-weight: 600;
}

.ms .n {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--route-soft);
  color: var(--route-ink);
  font-weight: 600;
  font-size: 0.875rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-weight: 500;
  margin-bottom: 12px;
}

.field select,
.field textarea {
  padding: 9px 12px;
  border: 1px solid var(--line-2);
  border-radius: 10px;
  background: var(--surface);
  font-weight: 400;
}

.btns {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.link {
  border: 0;
  background: none;
  color: var(--route-ink);
  font-weight: 500;
  cursor: pointer;
}

.preview {
  margin-top: 14px;
  padding: 14px;
  border-radius: 12px;
  background: var(--paper);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.problems {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: var(--high);
}

.problems li {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.ok-line {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--ok);
  font-weight: 600;
}

.moves {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 240px;
  overflow: auto;
}

.moves li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  font-size: 0.9375rem;
}

.moves li > span:first-child {
  min-width: 150px;
  font-weight: 500;
}

.history {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.history li {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr);
  gap: 12px;
}

.history li:not(.cur) .hv {
  background: var(--paper);
  color: var(--ink-2);
}

.history strong {
  font-weight: 600;
}

.history p {
  font-size: 0.9375rem;
}

.history .muted {
  font-size: 0.8125rem;
}

.matrix {
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
}

.mx-row {
  display: grid;
  grid-template-columns: minmax(0, 2fr) repeat(4, minmax(70px, 1fr));
  gap: 8px;
  align-items: center;
  padding: 9px 14px;
  font-size: 0.9375rem;
}

.mx-row + .mx-row {
  border-top: 1px solid var(--line);
}

.mx-row.th {
  background: var(--paper);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--muted);
}

.mx-row.th span:not(:first-child),
.mx-c {
  text-align: center;
}

.yes {
  display: inline-grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--ok-soft);
  color: var(--ok);
}

.no {
  color: var(--line-2);
  font-weight: 600;
}

.users {
  margin-top: 20px;
}

.users ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.users li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px auto;
  gap: 12px;
  align-items: center;
  padding: 10px 0;
}

.users li + li {
  border-top: 1px solid var(--line);
}

.users li.off .u-main {
  opacity: 0.55;
}

.u-main {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  min-width: 0;
}

.u-main strong {
  font-weight: 600;
}

.u-main .muted {
  font-size: 0.8125rem;
  overflow-wrap: anywhere;
}

.users select {
  width: 100%;
  padding: 7px 10px;
  border: 1px solid var(--line-2);
  border-radius: 9px;
  background: var(--surface);
}

.btn.sm {
  padding: 6px 12px;
  font-size: 0.875rem;
}

@media (max-width: 1000px) {
  .layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 700px) {
  .matrix {
    overflow-x: auto;
  }
  .mx-row {
    grid-template-columns: minmax(150px, 2fr) repeat(4, 64px);
    min-width: 430px;
    font-size: 0.875rem;
  }
  .users li {
    grid-template-columns: minmax(0, 1fr) auto;
  }
  .users label {
    grid-column: 1;
  }
  .ms-row {
    grid-template-columns: 28px repeat(3, minmax(0, 1fr));
  }
  .ms input {
    width: 100%;
  }
}
</style>
