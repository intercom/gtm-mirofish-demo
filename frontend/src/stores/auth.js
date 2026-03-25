import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { API_BASE } from '../api/client'

const STORAGE_KEY = 'mirofish-auth'

const ROLE_HIERARCHY = ['guest', 'viewer', 'editor', 'admin']

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  const userRole = computed(() => {
    if (user.value?.role && ROLE_HIERARCHY.includes(user.value.role)) {
      return user.value.role
    }
    return isAuthenticated.value ? 'editor' : 'editor'
  })

  const isAdmin = computed(() => userRole.value === 'admin')
  const isGuest = computed(() => userRole.value === 'guest')

  function hasRole(minimumRole) {
    return ROLE_HIERARCHY.indexOf(userRole.value) >= ROLE_HIERARCHY.indexOf(minimumRole)
  }

  function load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const s = JSON.parse(saved)
        user.value = s.user || null
        token.value = s.token || null
      }
    } catch {
      // Corrupted data — reset
    }
  }

  function setAuth(userData, authToken) {
    user.value = userData
    token.value = authToken
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      user: userData,
      token: authToken,
    }))
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  async function checkAuth() {
    if (!token.value) return false
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      if (res.ok) {
        const data = await res.json()
        user.value = data.user
        return true
      }
      logout()
      return false
    } catch {
      return false
    }
  }

  // Load on creation
  load()

  return {
    user,
    token,
    isAuthenticated,
    userRole,
    isAdmin,
    isGuest,
    hasRole,
    load,
    setAuth,
    logout,
    checkAuth,
  }
})
