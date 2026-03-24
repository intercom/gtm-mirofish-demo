import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'mirofish-auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)

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
      const res = await fetch('/api/auth/me', {
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
    load,
    setAuth,
    logout,
    checkAuth,
  }
})
