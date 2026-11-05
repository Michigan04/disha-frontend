import { defineStore } from 'pinia'
import { DEMO_PASSWORD, ROLES, findAccount } from '../data/accounts'

// Demo sign-in. The session is the account's email, kept in this browser only.
// In the full platform the backend checks the password and issues the session.
const KEY = 'disha.session'

function readSession() {
  try {
    return findAccount(localStorage.getItem(KEY) || sessionStorage.getItem(KEY))
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({ user: readSession() }),
  getters: {
    role: (s) => s.user?.role || null,
    isStaff: (s) => Boolean(s.user && s.user.role !== 'student'),
    home: (s) => (s.user ? ROLES[s.user.role].home : '/login'),
    roleLabel: (s) => (s.user ? ROLES[s.user.role].label : ''),
  },
  actions: {
    login(email, password, remember = true) {
      const account = findAccount(email)
      if (!account || password !== DEMO_PASSWORD) return 'That email and password do not match a demo account.'
      this.user = account
      try {
        ;(remember ? localStorage : sessionStorage).setItem(KEY, account.email)
      } catch {
        /* storage unavailable: signed in for this visit only */
      }
      return null
    },
    logout() {
      this.user = null
      try {
        localStorage.removeItem(KEY)
        sessionStorage.removeItem(KEY)
      } catch {
        /* nothing to clear */
      }
    },
  },
})
