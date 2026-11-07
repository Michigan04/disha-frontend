<script setup>
import { useId } from 'vue'

// The "Ask Disha" AI mark: the letters AI with a spark, on a warm gradient tile. Used
// wherever the assistant is offered, so it always reads as the AI helper, not messaging.
defineProps({ size: { type: Number, default: 40 } })
const gid = `ai-${useId()}`
</script>

<template>
  <svg class="ai-mark" viewBox="0 0 32 32" :width="size" :height="size" aria-hidden="true">
    <defs>
      <linearGradient :id="gid" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#d4b061" />
        <stop offset="0.55" stop-color="#9b2c3a" />
        <stop offset="1" stop-color="#5e1520" />
      </linearGradient>
    </defs>
    <rect width="32" height="32" rx="9" :fill="`url(#${gid})`" />
    <!-- "A" -->
    <path fill-rule="evenodd" d="M5.6 24 10.4 9.2h3.2L18.4 24h-3.3l-1-3.3H9.9L8.9 24zm5.1-6h2.6L12 13.6z" fill="#fff" />
    <!-- "I" -->
    <path d="M20 9.2h3.2V24H20z" fill="#fff" />
    <!-- spark in the corner -->
    <path d="M27 2.9c.3 1.4.9 2 2.3 2.3-1.4.3-2 .9-2.3 2.3-.3-1.4-.9-2-2.3-2.3 1.4-.3 2-.9 2.3-2.3z" fill="#fff" />
  </svg>
</template>

<style scoped>
.ai-mark {
  display: block;
  flex: none;
}
</style>
