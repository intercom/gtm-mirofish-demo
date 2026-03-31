<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppButton from '../components/common/AppButton.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const error = ref('')
const loading = ref(false)
const allowedDomain = import.meta.env.VITE_AUTH_ALLOWED_DOMAIN || 'intercom.io'

async function loginWithEmail() {
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
  loading.value = true
  try {
    auth.setAuth({ email: addr }, `email-${Date.now()}`)
    router.replace(route.query.redirect || '/')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (auth.isAuthenticated) {
    router.replace(route.query.redirect || '/')
    return
  }
  if (route.query.callback) {
    loading.value = true
    const ok = await auth.checkAuth()
    loading.value = false
    if (ok) {
      router.replace(route.query.redirect || '/')
    } else {
      error.value = `Sign-in failed. Only @${allowedDomain} accounts are allowed.`
    }
  }
})
</script>

<template>
  <div class="login-page">
    <!-- Background decoration -->
    <div class="login-bg-pattern" aria-hidden="true">
      <div class="login-bg-glow" />
    </div>

    <div class="login-card">
      <!-- Logo -->
      <div class="flex justify-center mb-6">
        <div class="login-logo">
          <svg width="36" height="36" viewBox="0 0 28 28" fill="none" aria-label="Intercom logo">
            <rect width="28" height="28" rx="6" fill="var(--color-primary)"/>
            <path d="M7 10.5C7 10.2239 7.22386 10 7.5 10H8.5C8.77614 10 9 10.2239 9 10.5V17.5C9 17.7761 8.77614 18 8.5 18H7.5C7.22386 18 7 17.7761 7 17.5V10.5Z" fill="white"/>
            <path d="M10.5 8.5C10.5 8.22386 10.7239 8 11 8H12C12.2761 8 12.5 8.22386 12.5 8.5V19.5C12.5 19.7761 12.2761 20 12 20H11C10.7239 20 10.5 19.7761 10.5 19.5V8.5Z" fill="white"/>
            <path d="M15.5 8.5C15.5 8.22386 15.7239 8 16 8H17C17.2761 8 17.5 8.22386 17.5 8.5V19.5C17.5 19.7761 17.2761 20 17 20H16C15.7239 20 15.5 19.7761 15.5 19.5V8.5Z" fill="white"/>
            <path d="M19 10.5C19 10.2239 19.2239 10 19.5 10H20.5C20.7761 10 21 10.2239 21 10.5V17.5C21 17.7761 20.7761 18 20.5 18H19.5C19.2239 18 19 17.7761 19 17.5V10.5Z" fill="white"/>
            <path d="M8 20.5C9.5 22 11.5 23 14 23C16.5 23 18.5 22 20 20.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </div>
      </div>

      <h1 class="login-title">Sign in to MiroFish</h1>
      <p class="login-subtitle">GTM simulation powered by swarm intelligence</p>

      <!-- Error message -->
      <Transition name="fade">
        <div v-if="error" class="login-error" role="alert">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" class="shrink-0 mt-0.5">
            <path fill-rule="evenodd" d="M8 15A7 7 0 108 1a7 7 0 000 14zm-.75-2.75a.75.75 0 101.5 0 .75.75 0 00-1.5 0zM8 4.5a.75.75 0 00-.75.75v4a.75.75 0 001.5 0v-4A.75.75 0 008 4.5z" clip-rule="evenodd"/>
          </svg>
          <span>{{ error }}</span>
        </div>
      </Transition>

      <!-- Email login form -->
      <form @submit.prevent="loginWithEmail" class="space-y-4">
        <div>
          <label for="login-email" class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">
            Work email
          </label>
          <input
            id="login-email"
            v-model="email"
            type="email"
            :placeholder="`you@${allowedDomain}`"
            autocomplete="email"
            :disabled="loading"
            class="login-input"
            @keydown.enter.prevent="loginWithEmail"
          />
        </div>

        <AppButton
          type="submit"
          variant="primary"
          size="lg"
          :loading="loading"
          :disabled="loading"
          class="w-full"
        >
          Continue
        </AppButton>
      </form>

      <p class="login-domain-note">
        Restricted to <strong>@{{ allowedDomain }}</strong> accounts
      </p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
  background: var(--color-navy);
  position: relative;
  overflow: hidden;
}

.login-bg-pattern {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.login-bg-glow {
  position: absolute;
  top: 30%;
  left: 50%;
  width: 600px;
  max-width: calc(100vw - 2rem);
  height: 600px;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(32, 104, 255, 0.08) 0%, transparent 70%);
  border-radius: 50%;
}

.login-card {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-10) var(--space-8);
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-lg), 0 0 0 1px rgba(0, 0, 0, 0.05);
  position: relative;
  z-index: 1;
}

.login-logo {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-light);
  border-radius: var(--radius-lg);
}

.login-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  text-align: center;
  margin-bottom: var(--space-1);
  letter-spacing: var(--letter-spacing-tight);
}

.login-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  text-align: center;
  margin-bottom: var(--space-8);
}

.login-error {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-error);
  background: var(--color-error-light);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius-lg);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-4);
}

.login-input {
  width: 100%;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: var(--input-radius);
  padding: var(--space-3) var(--input-padding-x);
  font-size: var(--input-font-size);
  color: var(--input-text);
  transition: border-color var(--input-transition), box-shadow var(--input-transition);
}

.login-input::placeholder {
  color: var(--input-placeholder);
}

.login-input:focus {
  outline: none;
  border-color: var(--input-border-focus);
  box-shadow: 0 0 0 3px var(--input-ring);
}

.login-input:disabled {
  opacity: var(--input-disabled-opacity);
  background: var(--input-disabled-bg);
  cursor: not-allowed;
}

.login-domain-note {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: center;
  margin-top: var(--space-6);
}

.login-domain-note strong {
  color: var(--color-text-secondary);
  font-weight: var(--font-medium);
}

/* Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-fast);
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
