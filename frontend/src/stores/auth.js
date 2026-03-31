import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '../api/auth'

const STORAGE_KEY = 'mirofish-auth'

const ROLE_HIERARCHY = ['guest', 'viewer', 'editor', 'admin']

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)
  const role = ref('admin')
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userPermissions = computed(() => user.value?.permissions || [])

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
        role.value = s.role || 'admin'
      }
    } catch {
      // Corrupted data — reset
    }
  }

  function setAuth(userData, authToken, userRole = 'viewer') {
    user.value = userData
    token.value = authToken
    role.value = userRole
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      user: userData,
      token: authToken,
      role: userRole,
    }))
  }

  function logout() {
    user.value = null
    token.value = null
    role.value = 'admin'
    localStorage.removeItem(STORAGE_KEY)
  }

  async function checkAuth() {
    if (!token.value) return false
    // When offline, trust cached credentials rather than logging out
    if (!navigator.onLine) return true
    loading.value = true
    try {
      const { data } = await authApi.me()
      user.value = data.user
      return true
    } catch {
      // Network error (likely offline) — trust cached auth
      return !!token.value
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
    role,
    loading,
    isAuthenticated,
    userRole,
    userPermissions,
    isAdmin,
    isGuest,
    hasRole,
    load,
    setAuth,
    login,
    logout,
    logoutAndNotify,
    checkAuth,
  }
})
