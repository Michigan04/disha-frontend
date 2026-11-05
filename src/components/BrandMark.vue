<script setup>
defineProps({ size: { type: Number, default: 30 } })
</script>

<template>
  <svg viewBox="0 0 32 32" :width="size" :height="size" aria-hidden="true">
    <rect width="32" height="32" rx="9" fill="var(--route)" />
    <path d="M7 21h6l6-10h6" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
    <circle cx="7" cy="21" r="2.6" fill="#fff" />
    <circle cx="25" cy="11" r="2.6" fill="#fff" />
  </svg>
</template>
