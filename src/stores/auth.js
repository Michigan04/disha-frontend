import { defineStore } from 'pinia'
import { ROLES } from '../data/accounts'
import { api, clearSession, readSession, saveSession } from '../services/api'
import { resetData } from '../services/loader'

// Sign-in. The backend checks the password and issues a token; the token and the
// signed-in user are kept in this browser (local storage, or the tab if "remember me"
// is off). Every permission is enforced again on the server.
export const useAuthStore = defineStore('auth', {
  state: () => ({ user: readSession() }),
  getters: {
    role: (s) => s.user?.role || null,
    isStaff: (s) => Boolean(s.user && s.user.role !== 'student'),
    home: (s) => (s.user ? ROLES[s.user.role].home : '/login'),
    roleLabel: (s) => (s.user ? ROLES[s.user.role].label : ''),
  },
  actions: {
    /** Returns null when signed in, otherwise the message to show. */
    async login(email, password, remember = true) {
      try {
        const res = await api.post('/auth/login', { email: email.trim(), password })
        resetData()
        saveSession(res.access_token, res.user, remember)
        this.user = res.user
        return null
      } catch (err) {
        return err.message
      }
    },
    logout() {
      this.user = null
      clearSession()
      resetData()
    },
  },
})
