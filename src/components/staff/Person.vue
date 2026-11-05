<script setup>
import { initials } from '../../utils/staff'

defineProps({
  name: { type: String, required: true },
  sub: { type: String, default: '' },
  size: { type: Number, default: 34 },
  tone: { type: String, default: '' },
})
</script>

<template>
  <span class="person">
    <span class="av" :class="tone" :style="{ width: `${size}px`, height: `${size}px`, fontSize: `${size * 0.38}px` }" aria-hidden="true">{{ initials(name) }}</span>
    <span class="txt">
      <strong>{{ name }}</strong>
      <span v-if="sub">{{ sub }}</span>
    </span>
  </span>
</template>

<style scoped>
.person {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.av {
  flex: none;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-weight: 700;
  background: var(--route-soft);
  color: var(--route-ink);
}

.av.high { background: var(--high-soft); color: var(--high); }
.av.low { background: var(--low-soft); color: var(--low); }
.av.ok { background: var(--ok-soft); color: var(--ok); }
.av.ink { background: var(--ink); color: #fff; }

.txt {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
  min-width: 0;
}

.txt strong {
  font-weight: 600;
  overflow-wrap: anywhere;
}

.txt span {
  font-size: 0.8125rem;
  color: var(--muted);
}
</style>
