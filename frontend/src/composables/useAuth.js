import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

/**
 * High-level auth composable for components.
 * Wraps the auth store with router-aware login/logout flows
 * and provides a one-call init() for app startup.
 */
export function useAuth() {
  const store = useAuthStore()
  const router = useRouter()

  const user = computed(() => store.user)
  const isAuthenticated = computed(() => store.isAuthenticated)
  const loading = computed(() => store.loading)

  async function init() {
    if (store.token) {
      await store.checkAuth()
    }
  }

  async function login(credentials) {
    const userData = await store.login(credentials)
    router.push({ name: 'landing' })
    return userData
  }

  async function logout() {
    await store.logoutAndNotify()
    router.push({ name: 'landing' })
  }

  function requireAuth(to, from, next) {
    if (store.isAuthenticated) {
      next()
    } else {
      next({ name: 'landing', query: { redirect: to.fullPath } })
    }
  }

  return {
    user,
    isAuthenticated,
    loading,
    init,
    login,
    logout,
    requireAuth,
  }
}
