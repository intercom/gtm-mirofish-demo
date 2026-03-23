import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TOKEN_KEY = 'auth_token'
const USER_KEY = 'mirofish-user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))

  const isAuthenticated = computed(() => !!token.value)

  function login(authToken, userInfo) {
    token.value = authToken
    user.value = userInfo
    localStorage.setItem(TOKEN_KEY, authToken)
    if (userInfo) {
      localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  function setUser(userInfo) {
    user.value = userInfo
    if (userInfo) {
      localStorage.setItem(USER_KEY, JSON.stringify(userInfo))
    } else {
      localStorage.removeItem(USER_KEY)
    }
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
