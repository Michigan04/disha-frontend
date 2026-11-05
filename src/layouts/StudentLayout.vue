<script setup>
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '../stores/student'
import { useAuthStore } from '../stores/auth'
import { useCalendar } from '../services/calendar'
import Icon from '../components/Icon.vue'
import BrandMark from '../components/BrandMark.vue'

const store = useStudentStore()
const auth = useAuthStore()
const router = useRouter()
const calendar = useCalendar()

// The signed-in student decides whose record is shown.
watch(() => auth.user?.studentId, (id) => { if (id && id !== store.currentId) store.setStudent(id) }, { immediate: true })

function signOut() {
  auth.logout()
  router.push('/login')
}

const nav = [
  { to: '/', label: 'Home', icon: 'home', mobile: true },
  { to: '/progress', label: 'CGPA and terms', short: 'Progress', icon: 'progress', mobile: true },
  { to: '/courses', label: 'Courses', icon: 'courses', mobile: true },
  { to: '/oppe', label: 'OPPE eligibility', short: 'OPPE', icon: 'oppe', mobile: false },
  { to: '/meetings', label: 'Meetings', icon: 'calendar', mobile: true },
  { to: '/ask', label: 'Ask Disha', short: 'Ask', icon: 'chat', mobile: true },
]

const initials = computed(() => store.student.name.split(' ').map((p) => p[0]).join(''))

// Reload the calendar whenever the demo student changes.
watch(() => store.student.id, () => calendar.load(store.student), { immediate: true })
</script>

<template>
  <a class="skip" href="#content">Skip to content</a>
  <div class="shell">
    <aside class="rail" aria-label="Main">
      <RouterLink to="/" class="brand">
        <BrandMark :size="30" />
        <span>Disha</span>
      </RouterLink>

      <nav>
        <ul class="nav">
          <li v-for="item in nav" :key="item.to">
            <RouterLink :to="item.to" class="nav-link" :exact-active-class="item.to === '/' ? 'active' : ''" :active-class="item.to === '/' ? '' : 'active'">
              <Icon :name="item.icon" />
              <span>{{ item.label }}</span>
            </RouterLink>
          </li>
        </ul>
      </nav>

      <div class="me">
        <div class="who">
          <span class="avatar" aria-hidden="true">{{ initials }}</span>
          <div>
            <strong>{{ store.student.name }}</strong>
            <span class="muted">{{ store.rule.label }}, term {{ store.termNumber }}</span>
          </div>
        </div>
        <button type="button" class="signout" @click="signOut">
          <Icon name="logout" :size="18" /> Sign out
        </button>
      </div>
    </aside>

    <header class="topbar">
      <RouterLink to="/" class="brand small">
        <BrandMark :size="26" />
        <span>Disha</span>
      </RouterLink>
      <div class="top-me">
        <span class="avatar sm" aria-hidden="true">{{ initials }}</span>
        <button type="button" class="icon-btn" aria-label="Sign out" @click="signOut"><Icon name="logout" :size="20" /></button>
      </div>
    </header>

    <main id="content" class="content" tabindex="-1">
      <RouterView :key="store.currentId" />
    </main>

    <nav class="tabbar" aria-label="Main">
      <RouterLink
        v-for="item in nav.filter((n) => n.mobile)"
        :key="item.to"
        :to="item.to"
        :exact-active-class="item.to === '/' ? 'active' : ''"
        :active-class="item.to === '/' ? '' : 'active'"
      >
        <Icon :name="item.icon" :size="22" />
        <span>{{ item.short || item.label }}</span>
      </RouterLink>
    </nav>
  </div>
</template>

<style scoped>
.skip {
  position: absolute;
  left: -999px;
  top: 8px;
  z-index: 10;
  background: var(--ink);
  color: #fff;
  padding: 8px 14px;
  border-radius: var(--r-s);
}

.skip:focus {
  left: 8px;
}

.shell {
  display: grid;
  grid-template-columns: var(--rail) 1fr;
  min-height: 100vh;
  /* keeps the rail's white column and border running the full page height */
  background: linear-gradient(90deg, var(--surface) 0 calc(var(--rail) - 1px), var(--line) calc(var(--rail) - 1px) var(--rail), transparent var(--rail));
}

.rail {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: 26px 18px 20px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px;
  text-decoration: none;
  color: var(--ink);
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

/* Navigation drawn as stations on a vertical line */
.nav {
  position: relative;
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 12px;
  border-radius: var(--r-s);
  color: var(--ink-2);
  text-decoration: none;
  font-weight: 500;
}

.nav-link:hover {
  background: var(--paper);
  color: var(--ink);
}

.nav-link.active {
  background: var(--route-soft);
  color: var(--route-ink);
  font-weight: 600;
}

.nav-link.active::after {
  content: '';
  position: absolute;
  right: 12px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--route);
}

.me {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px 10px 0;
  border-top: 1px solid var(--line);
}

.who {
  display: flex;
  gap: 10px;
  align-items: center;
}

.who strong {
  display: block;
  font-weight: 600;
  line-height: 1.25;
}

.who .muted {
  font-size: 0.875rem;
}

.avatar {
  width: 38px;
  height: 38px;
  flex: none;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--ink);
  color: #fff;
  font-weight: 600;
  font-size: 0.875rem;
}

.signout {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  align-self: flex-start;
  border: 1px solid var(--line-2);
  background: var(--surface);
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--ink-2);
  cursor: pointer;
}

.signout:hover {
  background: var(--paper);
  color: var(--ink);
}

.top-me {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar.sm {
  width: 32px;
  height: 32px;
  font-size: 0.8125rem;
}

.icon-btn {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid var(--line-2);
  background: var(--surface);
  color: var(--ink-2);
  cursor: pointer;
}

.topbar,
.tabbar {
  display: none;
}

.content {
  min-width: 0;
  outline: none;
}

@media (max-width: 860px) {
  .shell {
    grid-template-columns: 1fr;
    background: none;
  }

  .rail {
    display: none;
  }

  .topbar {
    position: sticky;
    top: 0;
    z-index: 5;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    background: var(--surface);
    border-bottom: 1px solid var(--line);
  }

  .brand.small {
    font-size: 1.125rem;
    padding: 0;
  }

  .tabbar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 5;
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    background: var(--surface);
    border-top: 1px solid var(--line);
    padding: 6px 4px calc(6px + env(safe-area-inset-bottom));
  }

  .tabbar a {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    padding: 4px 0;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--muted);
    text-decoration: none;
    border-radius: var(--r-s);
  }

  .tabbar a.active {
    color: var(--route-ink);
  }
}
</style>
