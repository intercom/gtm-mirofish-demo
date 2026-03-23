<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref('')
const error = ref('')

function loginWithGoogle() {
  loading.value = 'google'
  error.value = ''
  const redirect = route.query.redirect || '/'
  window.location.href = `/api/auth/google?redirect=${encodeURIComponent(redirect)}`
}

function loginWithOkta() {
  loading.value = 'okta'
  error.value = ''
  const redirect = route.query.redirect || '/'
  window.location.href = `/api/auth/okta?redirect=${encodeURIComponent(redirect)}`
}

onMounted(() => {
  const token = route.query.token
  const email = route.query.email
  const name = route.query.name
  const authError = route.query.error

  if (authError) {
    error.value = authError
    return
  }

  if (token) {
    authStore.login(token, { email: email || '', name: name || '' })
    const redirect = route.query.redirect || '/'
    router.replace(redirect)
  } else if (authStore.isAuthenticated) {
    router.replace(route.query.redirect || '/')
  }
})
</script>

<template>
  <div class="min-h-[calc(100vh-120px)] bg-[var(--color-navy)] flex items-center justify-center px-6">
    <div class="bg-white rounded-xl p-8 w-full max-w-sm text-center shadow-lg">
      <!-- Logo -->
      <div class="flex justify-center mb-6">
        <svg width="40" height="40" viewBox="0 0 28 28" fill="none">
          <rect width="28" height="28" rx="6" fill="#2068FF"/>
          <path d="M7 10.5C7 10.2239 7.22386 10 7.5 10H8.5C8.77614 10 9 10.2239 9 10.5V17.5C9 17.7761 8.77614 18 8.5 18H7.5C7.22386 18 7 17.7761 7 17.5V10.5Z" fill="white"/>
          <path d="M10.5 8.5C10.5 8.22386 10.7239 8 11 8H12C12.2761 8 12.5 8.22386 12.5 8.5V19.5C12.5 19.7761 12.2761 20 12 20H11C10.7239 20 10.5 19.7761 10.5 19.5V8.5Z" fill="white"/>
          <path d="M15.5 8.5C15.5 8.22386 15.7239 8 16 8H17C17.2761 8 17.5 8.22386 17.5 8.5V19.5C17.5 19.7761 17.2761 20 17 20H16C15.7239 20 15.5 19.7761 15.5 19.5V8.5Z" fill="white"/>
          <path d="M19 10.5C19 10.2239 19.2239 10 19.5 10H20.5C20.7761 10 21 10.2239 21 10.5V17.5C21 17.7761 20.7761 18 20.5 18H19.5C19.2239 18 19 17.7761 19 17.5V10.5Z" fill="white"/>
          <path d="M8 20.5C9.5 22 11.5 23 14 23C16.5 23 18.5 22 20 20.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>

      <h2 class="text-lg font-semibold text-[var(--color-navy)] mb-1">Sign in to MiroFish Demo</h2>
      <p class="text-xs text-neutral-500 mb-6">Restricted to @intercom.io accounts</p>

      <!-- Error message -->
      <div
        v-if="error"
        class="mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2"
        role="alert"
      >
        {{ error }}
      </div>

      <!-- OAuth Buttons -->
      <div class="space-y-3">
        <button
          data-testid="google-btn"
          :disabled="!!loading"
          class="w-full flex items-center justify-center gap-2 bg-white border border-black/10 rounded-lg px-4 py-3 text-sm font-medium hover:bg-black/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          @click="loginWithGoogle"
        >
          <svg v-if="loading !== 'google'" width="18" height="18" viewBox="0 0 18 18"><path d="M17.64 9.2c0-.63-.06-1.25-.16-1.84H9v3.49h4.84a4.14 4.14 0 01-1.8 2.71v2.26h2.92a8.78 8.78 0 002.68-6.62z" fill="#4285F4"/><path d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.83.86-3.04.86-2.34 0-4.32-1.58-5.03-3.71H.96v2.33A9 9 0 009 18z" fill="#34A853"/><path d="M3.97 10.71A5.41 5.41 0 013.68 9c0-.6.1-1.17.29-1.71V4.96H.96A9 9 0 000 9c0 1.45.35 2.82.96 4.04l3.01-2.33z" fill="#FBBC05"/><path d="M9 3.58c1.32 0 2.51.45 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 00.96 4.96l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z" fill="#EA4335"/></svg>
          <span v-if="loading === 'google'" class="inline-block w-4 h-4 border-2 border-neutral-300 border-t-neutral-600 rounded-full animate-spin" />
          Continue with Google
        </button>

        <button
          data-testid="okta-btn"
          :disabled="!!loading"
          class="w-full flex items-center justify-center gap-2 bg-[var(--color-navy)] text-white rounded-lg px-4 py-3 text-sm font-medium hover:bg-[var(--color-navy-light)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          @click="loginWithOkta"
        >
          <span v-if="loading === 'okta'" class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          Continue with Okta SSO
        </button>
      </div>
    </div>
  </div>
</template>
