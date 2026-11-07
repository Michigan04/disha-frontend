<script setup>
import { computed, nextTick, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ACCOUNTS, DEMO_PASSWORD, ROLES } from '../data/accounts'
import { initials } from '../utils/staff'
import Icon from '../components/Icon.vue'
import BrandMark from '../components/BrandMark.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const role = ref('student')
const email = ref('')
const password = ref('')
const remember = ref(true)
const show = ref(false)
const error = ref('')
const busy = ref(false)
const submitBtn = ref(null)

const accounts = computed(() => ACCOUNTS.filter((a) => a.role === role.value))
const ROLE_TABS = Object.entries(ROLES).map(([key, v]) => ({ key, label: v.label }))

function use(a) {
  email.value = a.email
  password.value = DEMO_PASSWORD
  error.value = ''
  nextTick(() => submitBtn.value?.focus())
}

async function submit() {
  error.value = ''
  if (!email.value.trim()) return (error.value = 'Enter your email.')
  if (!/^\S+@\S+\.\S+$/.test(email.value.trim())) return (error.value = 'That does not look like an email address.')
  if (!password.value) return (error.value = 'Enter your password.')
  busy.value = true
  await new Promise((r) => setTimeout(r, 350))
  const msg = auth.login(email.value, password.value, remember.value)
  busy.value = false
  if (msg) return (error.value = msg)
  const target = typeof route.query.redirect === 'string' ? route.query.redirect : auth.home
  router.replace(target)
}
</script>

<template>
  <div class="login">
    <section class="side" aria-hidden="true">
      <div class="logo">
        <BrandMark :size="36" />
        <span>Disha</span>
      </div>
      <p class="line">Every student,<br />on route.</p>

      <svg class="route" viewBox="0 0 440 250">
        <path id="track" d="M20 200 C 110 200, 120 60, 220 60 S 330 190, 420 120" fill="none" stroke="rgba(255,255,255,0.22)" stroke-width="10" stroke-linecap="round" />
        <path d="M20 200 C 110 200, 120 60, 220 60 S 330 190, 420 120" fill="none" stroke="#c9a24a" stroke-width="4" stroke-linecap="round" stroke-dasharray="6 10" />
        <g>
          <circle cx="20" cy="200" r="9" fill="#fff" />
          <circle cx="75" cy="178" r="9" fill="#c9a24a" />
          <circle cx="220" cy="60" r="9" fill="#fff" />
          <circle cx="365" cy="140" r="9" fill="#d4847a" />
          <circle cx="420" cy="120" r="12" fill="#8fbf9f" />
        </g>
        <g class="tags" font-size="13" font-weight="600">
          <rect x="0" y="214" width="76" height="26" rx="13" fill="rgba(255,255,255,0.12)" /><text x="38" y="232" text-anchor="middle" fill="#fff">Term 1</text>
          <rect x="94" y="178" width="124" height="26" rx="13" fill="#c9a24a" /><text x="156" y="196" text-anchor="middle" fill="#1c1917">Failed once: plan</text>
          <rect x="250" y="164" width="156" height="26" rx="13" fill="#d4847a" /><text x="328" y="182" text-anchor="middle" fill="#1c1917">Failed twice: instructor</text>
          <rect x="358" y="74" width="80" height="26" rx="13" fill="#8fbf9f" /><text x="398" y="92" text-anchor="middle" fill="#1c1917">Degree</text>
        </g>
        <circle class="runner" r="7" fill="#fff" />
      </svg>

      <ul class="facts">
        <li><strong>Students</strong> see their progress, risk and a plan</li>
        <li><strong>Staff</strong> see who needs help first and log what they did</li>
        <li><strong>Admins</strong> set the rules, upload data and check the audit log</li>
      </ul>
      <p class="foot">Student Risk Identification and Intervention Platform<br />IITM BS Software Engineering, Team 026</p>
    </section>

    <main class="main">
      <div class="form-wrap">
        <div class="logo small">
          <BrandMark :size="30" />
          <span>Disha</span>
        </div>
        <h1>Sign in</h1>
        <p class="muted">Choose who you are, then pick a demo account.</p>

        <div class="roles" role="tablist" aria-label="Sign in as">
          <button
            v-for="r in ROLE_TABS"
            :key="r.key"
            type="button"
            role="tab"
            :aria-selected="role === r.key"
            :class="{ on: role === r.key }"
            @click="role = r.key"
          >
            {{ r.label }}
          </button>
        </div>

        <form novalidate @submit.prevent="submit">
          <label class="field">
            <span>Email</span>
            <input v-model="email" type="email" autocomplete="username" placeholder="name@disha.demo" :aria-invalid="Boolean(error)" />
          </label>
          <label class="field">
            <span>Password</span>
            <span class="pw">
              <input v-model="password" :type="show ? 'text' : 'password'" autocomplete="current-password" :aria-invalid="Boolean(error)" />
              <button type="button" class="eye" :aria-label="show ? 'Hide password' : 'Show password'" :aria-pressed="show" @click="show = !show">
                <Icon :name="show ? 'cross' : 'eye'" :size="18" />
              </button>
            </span>
          </label>
          <div class="row">
            <label class="check"><input v-model="remember" type="checkbox" /> Keep me signed in</label>
          </div>
          <p v-if="error" class="error" role="alert"><Icon name="alert" :size="18" /> {{ error }}</p>
          <button ref="submitBtn" class="btn go" type="submit" :disabled="busy">
            <template v-if="busy">Signing in…</template>
            <template v-else>Sign in <Icon name="chevron" :size="18" /></template>
          </button>
        </form>

        <section class="demo" aria-labelledby="demo-h">
          <div class="demo-head">
            <h2 id="demo-h">Demo accounts</h2>
            <span class="chip"><Icon name="lock" :size="14" /> Password: <code>{{ DEMO_PASSWORD }}</code></span>
          </div>
          <ul>
            <li v-for="a in accounts" :key="a.email">
              <button type="button" class="acct" :class="{ picked: email === a.email }" @click="use(a)">
                <span class="av" :class="a.role">{{ initials(a.name) }}</span>
                <span class="who">
                  <strong>{{ a.name }}</strong>
                  <span>{{ a.note }}</span>
                </span>
                <span class="mail">{{ a.email }}</span>
              </button>
            </li>
          </ul>
        </section>
        <p class="note">Demo only: sign-in is checked in this browser. In the full platform the backend checks the password and each role’s access.</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.login {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
  background: var(--surface);
}

.side {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 26px;
  padding: 44px 48px 36px;
  background:
    radial-gradient(120% 70% at 100% 0%, rgba(123, 30, 43, 0.65), transparent 60%),
    radial-gradient(90% 60% at 0% 100%, rgba(201, 162, 74, 0.16), transparent 65%),
    var(--ink);
  color: #fff;
  overflow: hidden;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.5rem;
  font-weight: 700;
}

.line {
  font-size: 2.75rem;
  line-height: 1.08;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.route {
  width: 100%;
  max-width: 480px;
  height: auto;
}

.runner {
  offset-path: path('M20 200 C 110 200, 120 60, 220 60 S 330 190, 420 120');
  animation: run 6s ease-in-out infinite;
}

@keyframes run {
  from { offset-distance: 0%; }
  to { offset-distance: 100%; }
}

.facts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  color: var(--on-dark-2);
}

.facts li {
  padding-left: 18px;
  position: relative;
}

.facts li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--saffron);
}

.facts strong {
  color: #fff;
  font-weight: 600;
}

.foot {
  margin-top: auto;
  font-size: 0.8125rem;
  color: var(--on-dark-3);
}

.main {
  display: grid;
  place-items: center;
  padding: 40px 32px;
}

.form-wrap {
  width: 100%;
  max-width: 460px;
}

.logo.small {
  display: none;
  color: var(--ink);
  font-size: 1.25rem;
  margin-bottom: 22px;
}

h1 {
  margin-bottom: 4px;
}

.roles {
  margin: 22px 0 18px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 4px;
  padding: 4px;
  border-radius: 12px;
  background: var(--paper);
  border: 1px solid var(--line);
}

.roles button {
  border: 0;
  background: transparent;
  border-radius: 9px;
  padding: 8px 4px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--ink-2);
  cursor: pointer;
  line-height: 1.25;
}

.roles button.on {
  background: var(--surface);
  color: var(--route-ink);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(28, 25, 23, 0.12);
}

form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 500;
}

.field input {
  width: 100%;
  padding: 11px 14px;
  border: 1px solid var(--line-2);
  border-radius: 10px;
  background: var(--surface);
  font-weight: 400;
}

.field input:focus {
  outline: 2px solid var(--route);
  outline-offset: 0;
  border-color: var(--route);
}

.field input[aria-invalid='true'] {
  border-color: var(--high);
}

.pw {
  position: relative;
  display: block;
}

.pw input {
  padding-right: 46px;
}

.eye {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border: 0;
  background: none;
  color: var(--muted);
  cursor: pointer;
  border-radius: 8px;
}

.row {
  display: flex;
  justify-content: space-between;
}

.check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9375rem;
  color: var(--ink-2);
  cursor: pointer;
}

.check input {
  width: 17px;
  height: 17px;
  accent-color: var(--route);
}

.error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--high-soft);
  color: var(--high);
  font-size: 0.9375rem;
}

.go {
  justify-content: center;
  padding: 12px 18px;
  font-size: 1rem;
  border-radius: 12px;
}

.demo {
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid var(--line);
}

.demo-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.demo h2 {
  font-size: 1rem;
}

.demo code {
  font-family: ui-monospace, Menlo, monospace;
  font-size: 0.8125rem;
  color: var(--ink);
}

.demo ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.acct {
  width: 100%;
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: var(--surface);
  text-align: left;
  cursor: pointer;
}

.acct:hover {
  border-color: var(--line-2);
  background: var(--paper);
}

.acct.picked {
  border-color: var(--route);
  background: var(--route-soft);
}

.av {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 0.875rem;
  background: var(--route-soft);
  color: var(--route-ink);
}

.av.support { background: var(--ok-soft); color: var(--ok); }
.av.instructor { background: var(--low-soft); color: var(--low); }
.av.admin { background: var(--ink); color: #fff; }

.who {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  min-width: 0;
}

.who strong {
  font-weight: 600;
}

.who span {
  font-size: 0.875rem;
  color: var(--muted);
}

.mail {
  font-size: 0.8125rem;
  color: var(--muted);
}

@media (max-width: 960px) {
  .login {
    grid-template-columns: 1fr;
  }
  .side {
    display: none;
  }
  .logo.small {
    display: flex;
  }
  .main {
    place-items: start center;
    padding: 28px 16px 40px;
  }
}

@media (max-width: 480px) {
  .roles {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .mail {
    display: none;
  }
  .acct {
    grid-template-columns: 40px minmax(0, 1fr);
  }
}
</style>
