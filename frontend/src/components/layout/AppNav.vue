<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const mobileMenuOpen = ref(false)

const authUser = computed(() => {
  try {
    const stored = localStorage.getItem('auth_user')
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
})

const navLinks = [
  { to: '/', label: 'Home', exact: true },
  { to: '/settings', label: 'Settings', exact: false },
]

function logout() {
  localStorage.removeItem('auth_user')
  router.push('/login')
}
</script>

<template>
  <nav class="bg-[var(--color-navy)] border-b border-white/10 px-6 py-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-6">
        <router-link to="/" class="flex items-center gap-2 text-white no-underline">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">
            <rect width="28" height="28" rx="6" fill="var(--color-primary)"/>
            <path d="M7 10.5C7 10.2239 7.22386 10 7.5 10H8.5C8.77614 10 9 10.2239 9 10.5V17.5C9 17.7761 8.77614 18 8.5 18H7.5C7.22386 18 7 17.7761 7 17.5V10.5Z" fill="white"/>
            <path d="M10.5 8.5C10.5 8.22386 10.7239 8 11 8H12C12.2761 8 12.5 8.22386 12.5 8.5V19.5C12.5 19.7761 12.2761 20 12 20H11C10.7239 20 10.5 19.7761 10.5 19.5V8.5Z" fill="white"/>
            <path d="M15.5 8.5C15.5 8.22386 15.7239 8 16 8H17C17.2761 8 17.5 8.22386 17.5 8.5V19.5C17.5 19.7761 17.2761 20 17 20H16C15.7239 20 15.5 19.7761 15.5 19.5V8.5Z" fill="white"/>
            <path d="M19 10.5C19 10.2239 19.2239 10 19.5 10H20.5C20.7761 10 21 10.2239 21 10.5V17.5C21 17.7761 20.7761 18 20.5 18H19.5C19.2239 18 19 17.7761 19 17.5V10.5Z" fill="white"/>
            <path d="M8 20.5C9.5 22 11.5 23 14 23C16.5 23 18.5 22 20 20.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="text-sm font-semibold tracking-tight">MiroFish</span>
          <span class="text-xs text-white/40 ml-1">GTM Demo</span>
        </router-link>

        <div class="hidden md:flex items-center gap-1">
          <router-link
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            :exact="link.exact"
            class="nav-link"
            :class="{ 'nav-link--exact': link.exact }"
          >
            {{ link.label }}
          </router-link>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <div v-if="authUser" class="hidden sm:flex items-center gap-2">
          <span class="w-6 h-6 rounded-full bg-[var(--color-primary)] text-white text-xs flex items-center justify-center font-medium">
            {{ authUser.email?.[0]?.toUpperCase() ?? '?' }}
          </span>
          <span class="text-xs text-white/60 max-w-[120px] truncate">{{ authUser.email }}</span>
          <button
            @click="logout"
            class="text-xs text-white/40 hover:text-white transition-colors ml-1"
          >
            Sign out
          </button>
        </div>

        <div v-else class="hidden sm:flex items-center gap-2 text-xs text-white/40">
          <span class="w-2 h-2 rounded-full bg-green-500"></span>
          <span>Connected</span>
        </div>

        <button
          @click="mobileMenuOpen = !mobileMenuOpen"
          class="md:hidden text-white/60 hover:text-white transition-colors"
          :aria-expanded="mobileMenuOpen"
          aria-label="Toggle navigation menu"
        >
          <svg v-if="!mobileMenuOpen" width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>
    </div>

    <div v-if="mobileMenuOpen" class="md:hidden mt-3 pt-3 border-t border-white/10 flex flex-col gap-2">
      <router-link
        v-for="link in navLinks"
        :key="link.to"
        :to="link.to"
        :exact="link.exact"
        class="nav-link"
        :class="{ 'nav-link--exact': link.exact }"
        @click="mobileMenuOpen = false"
      >
        {{ link.label }}
      </router-link>
    </div>
  </nav>
</template>

<style scoped>
.nav-link {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-sm);
  transition: color var(--transition-fast), background-color var(--transition-fast);
}
.nav-link:hover {
  color: white;
  background-color: rgba(255, 255, 255, 0.08);
}
.nav-link.router-link-active {
  color: white;
  background-color: rgba(255, 255, 255, 0.12);
}
.nav-link--exact.router-link-active:not(.router-link-exact-active) {
  color: rgba(255, 255, 255, 0.6);
  background-color: transparent;
}
.nav-link--exact.router-link-exact-active {
  color: white;
  background-color: rgba(255, 255, 255, 0.12);
}
</style>
