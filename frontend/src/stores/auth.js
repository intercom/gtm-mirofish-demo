import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TOKEN_KEY = 'mirofish-token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  function login(authToken, userInfo) {
    token.value = authToken
    user.value = userInfo
    localStorage.setItem(TOKEN_KEY, authToken)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  function setUser(userInfo) {
    user.value = userInfo
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
    setUser,
  }
})
