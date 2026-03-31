<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const lastOnline = ref(Date.now())
const dismissed = ref(false)
const state = ref('idle') // 'idle' | 'offline' | 'reconnecting' | 'reconnected'

let reconnectedTimer = null
let agoInterval = null
let checkInterval = null
const agoText = ref('')

function updateAgoText() {
  const diff = Date.now() - lastOnline.value
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) {
    agoText.value = 'just now'
  } else {
    const minutes = Math.floor(seconds / 60)
    agoText.value = `${minutes}m ago`
  }
}

function handleOnline() {
  state.value = 'reconnected'
  dismissed.value = false
  clearInterval(agoInterval)
  clearInterval(checkInterval)
  reconnectedTimer = setTimeout(() => {
    state.value = 'idle'
  }, 3000)
}

function handleOffline() {
  lastOnline.value = Date.now()
  dismissed.value = false
  state.value = 'offline'
  clearTimeout(reconnectedTimer)
  updateAgoText()
  agoInterval = setInterval(updateAgoText, 10000)
  startConnectivityCheck()
}

function startConnectivityCheck() {
  clearInterval(checkInterval)
  checkInterval = setInterval(async () => {
    if (state.value !== 'offline') return
    state.value = 'reconnecting'
    try {
      const res = await fetch('/api/health', { method: 'HEAD', cache: 'no-store' })
      if (res.ok) {
        handleOnline()
      } else {
        state.value = 'offline'
      }
    } catch {
      state.value = 'offline'
    }
  }, 15000)
}

function dismiss() {
  dismissed.value = true
}

const visible = computed(() => {
  if (state.value === 'idle') return false
  if (state.value === 'reconnected') return true
  return !dismissed.value
})

const isWarning = computed(() => state.value === 'offline' || state.value === 'reconnecting')

onMounted(() => {
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  if (!navigator.onLine) {
    handleOffline()
  }
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
  clearTimeout(reconnectedTimer)
  clearInterval(agoInterval)
  clearInterval(checkInterval)
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      enter-from-class="-translate-y-full opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="-translate-y-full opacity-0"
    >
      <div
        v-if="visible"
        class="fixed top-0 left-0 right-0 z-[10000] flex items-center justify-center gap-3 px-4 py-2.5 text-sm font-medium"
        :class="isWarning ? 'bg-[--color-warning] text-[#1a1a1a]' : 'bg-[--color-success] text-white'"
      >
        <!-- Offline state -->
        <template v-if="state === 'offline'">
          <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M18.364 5.636a9 9 0 010 12.728M5.636 18.364a9 9 0 010-12.728M8.464 15.536a5 5 0 010-7.072M15.536 8.464a5 5 0 010 7.072" />
            <line x1="4" y1="4" x2="20" y2="20" stroke-linecap="round" />
          </svg>
          <span>You are currently offline. Data may not be up to date.</span>
          <span class="opacity-70 text-xs">Last synced: {{ agoText }}</span>
        </template>

        <!-- Reconnecting state -->
        <template v-else-if="state === 'reconnecting'">
          <svg class="animate-spin w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>Reconnecting...</span>
        </template>

        <!-- Reconnected state -->
        <template v-else-if="state === 'reconnected'">
          <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <span>Back online! Syncing...</span>
        </template>

        <!-- Dismiss button (only when offline/reconnecting) -->
        <button
          v-if="state !== 'reconnected'"
          @click="dismiss"
          class="absolute right-3 opacity-70 hover:opacity-100 cursor-pointer text-lg leading-none"
          aria-label="Dismiss offline notification"
        >
          &times;
        </button>
      </div>
    </Transition>
  </Teleport>
</template>
