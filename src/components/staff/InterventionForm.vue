<script setup>
import { computed, reactive, ref } from 'vue'
import Icon from '../Icon.vue'
import { INTERVENTION_TYPES, OUTCOMES } from '../../data/actions'
import { STAFF } from '../../data/staff'

// Log an intervention (US-07), or, for an instructor, the support offered on a referral (US-13).
const props = defineProps({
  row: { type: Object, required: true },
  mode: { type: String, default: 'log' }, // log | support
  presetType: { type: String, default: 'call' },
})
const emit = defineEmits(['save', 'cancel'])

const SUPPORT_KINDS = ['Practice session', 'Mock OPPE', 'Doubt-clearing session', 'Check-in']
const iso = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
const today = iso(new Date())
const inAWeek = iso(new Date(Date.now() + 7 * 864e5))

const f = reactive({
  type: props.mode === 'support' ? 'meeting' : props.presetType,
  kind: SUPPORT_KINDS[0],
  reason: props.row.reasons[0]?.key ? `${props.row.reasons[0].key}|${props.row.reasons[0].courseId || ''}` : 'general|',
  date: today,
  notes: '',
  referralTo: '',
  followUp: inAWeek,
  outcome: 'in_progress',
})
const errors = ref({})
const outcomeOptions = Object.entries(OUTCOMES).filter(([k]) => k !== 'not_contacted')
const instructors = Object.values(STAFF).filter((s) => s.role === 'instructor')

const reasonOptions = computed(() => [
  ...props.row.reasons.map((r) => ({ value: `${r.key}|${r.courseId || ''}`, label: r.text })),
  { value: 'general|', label: 'General check-in' },
])

function check() {
  const e = {}
  if (!f.date) e.date = 'Choose the date.'
  else if (f.date > today) e.date = 'The date cannot be in the future.'
  if (f.notes.trim().length < 10) e.notes = 'Write at least a short note (10 characters or more).'
  if (f.type === 'referral' && !f.referralTo) e.referralTo = 'Choose who the student is referred to.'
  if (f.outcome !== 'resolved') {
    if (!f.followUp) e.followUp = 'Choose a follow-up date, or set the outcome to Resolved.'
    else if (f.followUp < f.date) e.followUp = 'The follow-up must be on or after the date above.'
  }
  errors.value = e
  return !Object.keys(e).length
}

function save() {
  if (!check()) return
  const [reason, courseId] = f.reason.split('|')
  const at = new Date(`${f.date}T12:00:00`)
  emit('save', {
    studentId: props.row.id,
    courseId: courseId || props.row.risk.focus?.course.id || null,
    reason,
    type: f.type,
    at,
    notes: props.mode === 'support' ? `${f.kind}: ${f.notes.trim()}` : f.notes.trim(),
    referralTo: f.type === 'referral' ? f.referralTo : null,
    followUp: f.outcome === 'resolved' ? null : new Date(`${f.followUp}T12:00:00`),
    outcome: f.outcome,
  })
}
</script>

<template>
  <form class="form" novalidate @submit.prevent="save">
    <fieldset v-if="mode === 'log'" class="types">
      <legend>Type</legend>
      <label v-for="(t, key) in INTERVENTION_TYPES" :key="key" :class="{ on: f.type === key }">
        <input v-model="f.type" type="radio" name="type" :value="key" />
        <Icon :name="t.icon" :size="18" /> {{ t.label }}
      </label>
    </fieldset>
    <fieldset v-else class="types">
      <legend>Support offered</legend>
      <label v-for="k in SUPPORT_KINDS" :key="k" :class="{ on: f.kind === k }">
        <input v-model="f.kind" type="radio" name="kind" :value="k" /> {{ k }}
      </label>
    </fieldset>

    <div class="two">
      <label class="field">
        <span>Linked to</span>
        <select v-model="f.reason">
          <option v-for="o in reasonOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
        </select>
      </label>
      <label class="field">
        <span>Date</span>
        <input v-model="f.date" type="date" :max="today" :aria-invalid="Boolean(errors.date)" />
        <small v-if="errors.date" class="err">{{ errors.date }}</small>
      </label>
    </div>

    <label v-if="f.type === 'referral'" class="field">
      <span>Refer to</span>
      <select v-model="f.referralTo" :aria-invalid="Boolean(errors.referralTo)">
        <option value="" disabled>Choose an instructor</option>
        <option v-for="i in instructors" :key="i.id" :value="i.id">{{ i.name }} ({{ i.title.replace('Course instructor, ', '') }})</option>
      </select>
      <small v-if="errors.referralTo" class="err">{{ errors.referralTo }}</small>
    </label>

    <label class="field">
      <span>Notes</span>
      <textarea v-model="f.notes" rows="3" :placeholder="mode === 'support' ? 'What you did and what the student will do next' : 'What was discussed and agreed'" :aria-invalid="Boolean(errors.notes)"></textarea>
      <small v-if="errors.notes" class="err">{{ errors.notes }}</small>
    </label>

    <div class="two">
      <label class="field">
        <span>Outcome</span>
        <select v-model="f.outcome">
          <option v-for="[key, o] in outcomeOptions" :key="key" :value="key">{{ o.label }}</option>
        </select>
      </label>
      <label class="field">
        <span>Follow-up date</span>
        <input v-model="f.followUp" type="date" :min="f.date" :disabled="f.outcome === 'resolved'" :aria-invalid="Boolean(errors.followUp)" />
        <small v-if="errors.followUp" class="err">{{ errors.followUp }}</small>
      </label>
    </div>

    <div class="actions">
      <button class="btn" type="submit"><Icon name="check" :size="18" /> Save</button>
      <button class="btn quiet" type="button" @click="emit('cancel')">Cancel</button>
    </div>
  </form>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.types {
  border: 0;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.types legend {
  font-weight: 500;
  margin-bottom: 6px;
  padding: 0;
}

.types label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--line-2);
  cursor: pointer;
  font-size: 0.9375rem;
  background: var(--surface);
}

.types label.on {
  border-color: var(--route);
  background: var(--route-soft);
  color: var(--route-ink);
  font-weight: 600;
}

.types input {
  position: absolute;
  opacity: 0;
  width: 1px;
  height: 1px;
}

.types label:focus-within {
  outline: 2px solid var(--route);
  outline-offset: 2px;
}

.two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-weight: 500;
  min-width: 0;
}

.field select,
.field input,
.field textarea {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--line-2);
  border-radius: 10px;
  background: var(--surface);
  font-weight: 400;
}

.field textarea {
  resize: vertical;
}

.field [aria-invalid='true'] {
  border-color: var(--high);
}

.field input:disabled {
  background: var(--paper);
  color: var(--muted);
}

.err {
  color: var(--high);
  font-weight: 500;
  font-size: 0.8125rem;
}

.actions {
  display: flex;
  gap: 8px;
}

@media (max-width: 560px) {
  .two {
    grid-template-columns: 1fr;
  }
}
</style>
