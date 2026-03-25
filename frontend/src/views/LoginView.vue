<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const error = ref('')
const allowedDomain = import.meta.env.VITE_AUTH_ALLOWED_DOMAIN || 'intercom.io'

function loginWithEmail() {
  error.value = ''
  const addr = email.value.trim().toLowerCase()
  if (!addr) {
    error.value = 'Please enter your email address.'
    return
  }
  if (!addr.endsWith(`@${allowedDomain}`)) {
    error.value = `Only @${allowedDomain} accounts are allowed.`
    return
  }
  auth.setAuth({ email: addr }, `email-${Date.now()}`)
  router.replace(route.query.redirect || '/')
}

onMounted(async () => {
  // Handle OAuth callback if configured
  if (route.query.callback) {
    const ok = await auth.checkAuth()
    if (ok) {
      router.replace(route.query.redirect || '/')
    } else {
      error.value = `Sign-in failed. Only @${allowedDomain} accounts are allowed.`
    }
  }
})
</script>

<template>
  <div class="min-h-[calc(100vh-120px)] bg-[var(--color-navy)] flex items-center justify-center px-6">
    <div class="bg-[var(--color-surface)] rounded-xl p-8 w-full max-w-sm text-center shadow-lg">
      <!-- Logo -->
      <div class="flex justify-center mb-6">
        <svg width="40" height="40" viewBox="0 0 28 28" fill="none">
          <rect width="28" height="28" rx="6" fill="var(--color-primary)"/>
          <path d="M7 10.5C7 10.2239 7.22386 10 7.5 10H8.5C8.77614 10 9 10.2239 9 10.5V17.5C9 17.7761 8.77614 18 8.5 18H7.5C7.22386 18 7 17.7761 7 17.5V10.5Z" fill="white"/>
          <path d="M10.5 8.5C10.5 8.22386 10.7239 8 11 8H12C12.2761 8 12.5 8.22386 12.5 8.5V19.5C12.5 19.7761 12.2761 20 12 20H11C10.7239 20 10.5 19.7761 10.5 19.5V8.5Z" fill="white"/>
          <path d="M15.5 8.5C15.5 8.22386 15.7239 8 16 8H17C17.2761 8 17.5 8.22386 17.5 8.5V19.5C17.5 19.7761 17.2761 20 17 20H16C15.7239 20 15.5 19.7761 15.5 19.5V8.5Z" fill="white"/>
          <path d="M19 10.5C19 10.2239 19.2239 10 19.5 10H20.5C20.7761 10 21 10.2239 21 10.5V17.5C21 17.7761 20.7761 18 20.5 18H19.5C19.2239 18 19 17.7761 19 17.5V10.5Z" fill="white"/>
          <path d="M8 20.5C9.5 22 11.5 23 14 23C16.5 23 18.5 22 20 20.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>

      <h2 class="text-lg font-semibold text-[var(--color-navy)] mb-1">Sign in to MiroFish Demo</h2>
      <p class="text-xs text-[var(--color-text-muted)] mb-6">Restricted to @{{ allowedDomain }} accounts</p>

      <!-- Error -->
      <p v-if="error" class="text-sm text-red-600 bg-red-50 rounded-lg px-4 py-3 mb-4">{{ error }}</p>

      <!-- Email login form -->
      <form @submit.prevent="loginWithEmail" class="space-y-4">
        <input
          v-model="email"
          type="email"
          placeholder="you@intercom.io"
          class="w-full border border-[var(--color-border)] rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
          autocomplete="email"
        />
        <button
          type="submit"
          class="w-full bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white rounded-lg px-4 py-3 text-sm font-medium transition-colors"
        >
          Continue
        </button>
      </form>
    </div>
  </div>
</template>
