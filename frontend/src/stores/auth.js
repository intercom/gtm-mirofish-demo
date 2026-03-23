import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchUser() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/auth/me')
      if (res.ok) {
        user.value = await res.json()
      } else {
        user.value = null
      }
    } catch {
      user.value = null
    } finally {
      loading.value = false
    }
  }

  function loginWithGoogle() {
    window.location.href = '/api/auth/google'
  }

  function loginWithOkta() {
    window.location.href = '/api/auth/okta'
  }

  async function logout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST' })
    } catch {
      // Ignore network errors — we clear the local state regardless
    } finally {
      user.value = null
    }
  }

  return { user, loading, error, fetchUser, loginWithGoogle, loginWithOkta, logout }
})
