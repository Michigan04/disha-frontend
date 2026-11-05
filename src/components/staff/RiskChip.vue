<script setup>
import { RISK_VIEW } from '../../utils/staff'

defineProps({
  level: { type: String, required: true },
  isNew: { type: Boolean, default: false },
})
</script>

<template>
  <span class="risk">
    <span class="chip" :class="RISK_VIEW[level].cls"><span class="dot" aria-hidden="true"></span>{{ RISK_VIEW[level].label }}</span>
    <span v-if="isNew" class="new">New</span>
  </span>
</template>

<style scoped>
.risk {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.new {
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--high);
  color: #fff;
}
</style>
