import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '../api/auth'

const STORAGE_KEY = 'mirofish-auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)
  const loading = ref(false)

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
    loading.value = true
    try {
      const { data } = await authApi.me()
      user.value = data.user
      return true
    } catch {
      logout()
      return false
    } finally {
      loading.value = false
    }
  }

  async function login(credentials) {
    loading.value = true
    try {
      const { data } = await authApi.login(credentials)
      setAuth(data.user, data.token)
      return data.user
    } finally {
      loading.value = false
    }
  }

  async function logoutAndNotify() {
    try {
      await authApi.logout()
    } catch {
      // Server logout is best-effort
    }
    logout()
  }

  // Load on creation
  load()

  return {
    user,
    token,
    loading,
    isAuthenticated,
    load,
    setAuth,
    login,
    logout,
    logoutAndNotify,
    checkAuth,
  }
})
