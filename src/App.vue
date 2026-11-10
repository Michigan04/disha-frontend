<script setup>
import { computed } from 'vue'
import { useAuthStore } from './stores/auth'
import { boot, ensureData } from './services/loader'
import BrandMark from './components/BrandMark.vue'

const auth = useAuthStore()
// Signed in, but the first load has not finished (or failed).
const waiting = computed(() => Boolean(auth.user) && !boot.ready)

async function retry() {
  await ensureData()
  if (boot.ready) location.reload()
}
</script>

<template>
  <div v-if="waiting && (boot.loading || boot.error)" class="boot" role="status" aria-live="polite">
    <BrandMark />
    <template v-if="boot.error">
      <p class="msg">Your data could not be loaded: {{ boot.error }}</p>
      <div class="acts">
        <button type="button" class="btn" @click="retry">Try again</button>
        <button type="button" class="btn quiet" @click="auth.logout(); $router.replace('/login')">Sign out</button>
      </div>
    </template>
    <p v-else class="msg muted">Loading your data…</p>
  </div>
  <RouterView v-else />
</template>

<style scoped>
.boot {
  min-height: 100vh;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 16px;
  padding: 24px 16px;
  text-align: center;
}
.msg {
  max-width: 44ch;
  margin: 0;
}
.acts {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}
</style>
