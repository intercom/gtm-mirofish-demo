<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { useDemoMode } from '../../composables/useDemoMode'

const authStore = useAuthStore()
const { isDemoMode } = useDemoMode()
const isOpen = ref(false)
const menuRef = ref(null)

const displayUser = computed(() => {
  if (authStore.user) return authStore.user
  if (isDemoMode) return { name: 'Demo User', email: 'demo@intercom.io' }
  return null
})

const userInitials = computed(() => {
  const name = displayUser.value?.name
  if (!name) return '?'
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
})

const avatarUrl = computed(() => displayUser.value?.picture_url || displayUser.value?.picture || null)

function toggle() {
  isOpen.value = !isOpen.value
}

function close() {
  isOpen.value = false
}

function handleClickOutside(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) {
    close()
  }
}

function handleKeydown(e) {
  if (e.key === 'Escape') close()
}

function handleSignOut() {
  close()
  authStore.logout()
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div ref="menuRef" class="relative">
    <!-- Authenticated / Demo: avatar trigger -->
    <button
      v-if="displayUser"
      @click="toggle"
      class="flex items-center gap-2 rounded-full transition-opacity hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:ring-offset-2 focus:ring-offset-[var(--color-navy)]"
      :aria-expanded="isOpen"
      aria-haspopup="true"
      aria-label="User menu"
    >
      <img
        v-if="avatarUrl"
        :src="avatarUrl"
        :alt="displayUser.name"
        class="w-8 h-8 rounded-full object-cover ring-2 ring-white/20"
      />
      <span
        v-else
        class="w-8 h-8 rounded-full bg-[var(--color-primary)] text-white text-xs font-semibold flex items-center justify-center ring-2 ring-white/20"
      >
        {{ userInitials }}
      </span>
    </button>

    <!-- Unauthenticated: sign in link -->
    <router-link
      v-else
      to="/login"
      class="text-sm text-white/60 hover:text-white transition-colors no-underline px-3 py-1.5 rounded-md hover:bg-white/8"
    >
      Sign In
    </router-link>

    <!-- Dropdown menu -->
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isOpen && displayUser"
        class="absolute right-0 top-full mt-2 w-64 rounded-lg bg-[#0a0a0a] border border-white/10 shadow-lg z-50 overflow-hidden origin-top-right"
        role="menu"
      >
        <!-- User info header -->
        <div class="px-4 py-3 border-b border-white/10">
          <p class="text-sm font-semibold text-white truncate">{{ displayUser.name }}</p>
          <p class="text-xs text-white/50 truncate mt-0.5">{{ displayUser.email }}</p>
          <span
            v-if="displayUser.role"
            class="inline-block mt-1.5 text-xs font-semibold px-2 py-0.5 rounded-full bg-[rgba(32,104,255,0.15)] text-[var(--color-primary)]"
          >
            {{ displayUser.role }}
          </span>
        </div>

        <!-- Menu items -->
        <div class="py-1">
          <router-link
            to="/settings"
            class="menu-item"
            role="menuitem"
            @click="close"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" class="shrink-0">
              <path fill-rule="evenodd" d="M7.194.553a1.85 1.85 0 011.612 0l.548.274a1.85 1.85 0 01.806.806l.107.214a.35.35 0 00.312.192h.24a1.85 1.85 0 011.612.935l.274.548c.18.36.18.786 0 1.147l-.107.214a.35.35 0 000 .312l.107.214c.18.36.18.786 0 1.147l-.274.548a1.85 1.85 0 01-.806.806l-.214.107a.35.35 0 00-.192.312v.24a1.85 1.85 0 01-.935 1.612l-.548.274a1.85 1.85 0 01-1.147 0l-.214-.107a.35.35 0 00-.312 0l-.214.107a1.85 1.85 0 01-1.147 0l-.548-.274a1.85 1.85 0 01-.806-.806l-.107-.214a.35.35 0 00-.312-.192h-.24a1.85 1.85 0 01-1.612-.935l-.274-.548a1.85 1.85 0 010-1.147l.107-.214a.35.35 0 000-.312l-.107-.214a1.85 1.85 0 010-1.147l.274-.548a1.85 1.85 0 01.806-.806l.214-.107A.35.35 0 004.6 2.63v-.24A1.85 1.85 0 015.535.778L6.083.504a1.85 1.85 0 011.111-.001zM8 10a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/>
            </svg>
            Settings
          </router-link>

          <div class="my-1 border-t border-white/10"></div>

          <button
            class="menu-item w-full text-left text-[var(--color-error)] hover:text-[var(--color-error)]"
            role="menuitem"
            @click="handleSignOut"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" class="shrink-0">
              <path fill-rule="evenodd" d="M3 2a1 1 0 00-1 1v10a1 1 0 001 1h3a.5.5 0 010 1H3a2 2 0 01-2-2V3a2 2 0 012-2h3a.5.5 0 010 1H3zm9.854 3.146a.5.5 0 010 .708L10.707 8l2.147 2.146a.5.5 0 01-.708.708l-2.5-2.5a.5.5 0 010-.708l2.5-2.5a.5.5 0 01.708 0z" clip-rule="evenodd"/>
              <path fill-rule="evenodd" d="M6 8a.5.5 0 01.5-.5H13a.5.5 0 010 1H6.5A.5.5 0 016 8z" clip-rule="evenodd"/>
            </svg>
            Sign Out
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.menu-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: background-color var(--transition-fast), color var(--transition-fast);
  cursor: pointer;
  background: none;
  border: none;
  font-family: inherit;
}
.menu-item:hover {
  background-color: rgba(255, 255, 255, 0.08);
  color: white;
}
</style>
