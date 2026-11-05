<script setup>
import { computed } from 'vue'

const props = defineProps({ status: { type: Object, required: true } })

const view = computed(() => {
  const s = props.status
  if (s.state === 'passed') return { cls: 'ok', text: `Passed, grade ${s.grade}` }
  if (s.state === 'in_progress') {
    if (s.fails >= 2) return { cls: 'high', text: `Attempt ${s.attemptNo}, instructor support` }
    if (s.fails === 1) return { cls: 'low', text: `Attempt ${s.attemptNo}, guidance available` }
    return { cls: 'route', text: 'In progress' }
  }
  if (s.state === 'not_cleared') return { cls: s.fails >= 2 ? 'high' : 'low', text: `Not cleared, ${s.fails} ${s.fails === 1 ? 'attempt' : 'attempts'}` }
  return { cls: '', text: 'Not started' }
})
</script>

<template>
  <span class="chip" :class="view.cls">{{ view.text }}</span>
</template>
