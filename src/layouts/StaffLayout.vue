<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useStaffStore } from '../stores/staff'
import { STAFF } from '../data/staff'
import { initials } from '../utils/staff'
import Icon from '../components/Icon.vue'
import BrandMark from '../components/BrandMark.vue'

const auth = useAuthStore()
const staff = useStaffStore()
const router = useRouter()

const newHigh = computed(() => staff.atRisk.filter((r) => r.isNew).length)
const due = computed(() => staff.followUps.filter((f) => f.due && (auth.role === 'admin' || staff.meta[f.studentId].owner === auth.user?.staffId)).length)

const ALL = [
  { to: '/staff', label: 'Overview', icon: 'grid', roles: ['admin', 'support'], exact: true },
  { to: '/staff/students', label: 'At-risk students', short: 'Students', icon: 'users', roles: ['admin', 'support'], badge: () => newHigh.value },
  { to: '/staff/interventions', label: 'Interventions', icon: 'board', roles: ['admin', 'support'], badge: () => due.value },
  { to: '/staff/course', label: 'My course', icon: 'courses', roles: ['instructor'] },
  { to: '/staff/reports', label: 'Reports', icon: 'chart', roles: ['admin'] },
  { to: '/staff/data', label: 'Data and system', short: 'Data', icon: 'upload', roles: ['admin'] },
  { to: '/staff/rules', label: 'Rules and access', short: 'Rules', icon: 'sliders', roles: ['admin'] },
  { to: '/staff/audit', label: 'Audit log', short: 'Audit', icon: 'log', roles: ['admin'] },
]
const nav = computed(() => ALL.filter((n) => n.roles.includes(auth.role)))
const me = computed(() => STAFF[auth.user?.staffId])

function signOut() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <template v-if="auth.user">
  <a class="skip" href="#content">Skip to content</a>
  <div class="shell">
    <aside class="rail" aria-label="Staff">
      <RouterLink :to="auth.home" class="brand">
        <BrandMark :size="30" />
        <span>Disha</span>
        <span class="tag">Staff</span>
      </RouterLink>

      <nav>
        <ul class="nav">
          <li v-for="item in nav" :key="item.to">
            <RouterLink :to="item.to" class="nav-link" :exact-active-class="item.exact ? 'active' : ''" :active-class="item.exact ? '' : 'active'">
              <Icon :name="item.icon" />
              <span>{{ item.label }}</span>
              <span v-if="item.badge && item.badge()" class="badge num" :aria-label="`${item.badge()} need attention`">{{ item.badge() }}</span>
            </RouterLink>
          </li>
        </ul>
      </nav>

      <div class="me">
        <div class="who">
          <span class="avatar" aria-hidden="true">{{ initials(auth.user.name) }}</span>
          <div>
            <strong>{{ auth.user.name }}</strong>
            <span>{{ me?.title || auth.roleLabel }}</span>
          </div>
        </div>
        <button type="button" class="signout" @click="signOut"><Icon name="logout" :size="18" /> Sign out</button>
      </div>
    </aside>

    <header class="topbar">
      <RouterLink :to="auth.home" class="brand small">
        <BrandMark :size="26" />
        <span>Disha</span>
        <span class="tag">Staff</span>
      </RouterLink>
      <div class="top-me">
        <span class="avatar sm" aria-hidden="true">{{ initials(auth.user.name) }}</span>
        <button type="button" class="icon-btn" aria-label="Sign out" @click="signOut"><Icon name="logout" :size="20" /></button>
      </div>
    </header>
    <nav v-if="nav.length > 1" class="strip" aria-label="Staff">
      <RouterLink v-for="item in nav" :key="item.to" :to="item.to" :exact-active-class="item.exact ? 'active' : ''" :active-class="item.exact ? '' : 'active'">
        <Icon :name="item.icon" :size="18" /> {{ item.short || item.label }}
        <span v-if="item.badge && item.badge()" class="badge num">{{ item.badge() }}</span>
      </RouterLink>
    </nav>

    <main id="content" class="content" tabindex="-1">
      <RouterView />
    </main>
  </div>
  </template>
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
  grid-template-columns: var(--rail) minmax(0, 1fr);
  min-height: 100vh;
  background: linear-gradient(90deg, var(--ink) 0 var(--rail), transparent var(--rail));
}

.rail {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: 26px 18px 20px;
  color: #fff;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px;
  text-decoration: none;
  color: #fff;
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.tag {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  color: var(--saffron);
}

.nav {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 12px;
  border-radius: var(--r-s);
  color: var(--on-dark-2);
  text-decoration: none;
  font-weight: 500;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.07);
  color: #fff;
}

.nav-link.active {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  font-weight: 600;
  box-shadow: inset 3px 0 0 var(--saffron);
}

.badge {
  margin-left: auto;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-size: 0.75rem;
  font-weight: 700;
  background: var(--tangerine);
  color: var(--ink);
}

.me {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px 10px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.14);
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

.who span:not(.avatar) {
  font-size: 0.8125rem;
  color: var(--on-dark-3);
  line-height: 1.3;
}

.avatar {
  width: 38px;
  height: 38px;
  flex: none;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--saffron);
  color: var(--ink);
  font-weight: 700;
  font-size: 0.875rem;
}

.signout {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  align-self: flex-start;
  border: 1px solid rgba(255, 255, 255, 0.24);
  background: transparent;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 0.9375rem;
  font-weight: 500;
  color: #fff;
  cursor: pointer;
}

.signout:hover {
  background: rgba(255, 255, 255, 0.08);
}

.topbar,
.strip {
  display: none;
}

.content {
  min-width: 0;
  outline: none;
}

@media (max-width: 860px) {
  .shell {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto 1fr;
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
    background: var(--ink);
  }

  .brand.small {
    font-size: 1.125rem;
    padding: 0;
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
    border: 1px solid rgba(255, 255, 255, 0.24);
    background: transparent;
    color: #fff;
    cursor: pointer;
  }

  .strip {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    padding: 10px 16px;
    background: var(--surface);
    border-bottom: 1px solid var(--line);
    scrollbar-width: none;
  }

  .strip a {
    flex: none;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 999px;
    border: 1px solid var(--line-2);
    color: var(--ink-2);
    text-decoration: none;
    font-size: 0.9375rem;
    font-weight: 500;
    white-space: nowrap;
  }

  .strip a.active {
    background: var(--ink);
    border-color: var(--ink);
    color: #fff;
  }

  .strip .badge {
    margin-left: 2px;
    min-width: 20px;
    height: 20px;
  }
}
</style>
