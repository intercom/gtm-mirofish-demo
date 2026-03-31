<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { API_BASE } from '../../api/client'

const route = useRoute()
const router = useRouter()

const expanded = ref(false)
const activeSpeed = ref(1)
const loading = ref(false)

const PHASES = {
  'scenario-builder': 'Graph',
  workspace: 'Simulation',
  report: 'Report',
  chat: 'Chat',
}

const currentPhase = computed(() => PHASES[route.name] || 'Idle')

const skipLabel = computed(() => {
  const phase = PHASES[route.name]
  return phase ? `Skip ${phase}` : null
})

const SPEEDS = [1, 2, 3, 5]

async function setSpeed(speed) {
  activeSpeed.value = speed
  try {
    await fetch(`${API_BASE}/demo/speed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ speed }),
    })
  } catch {
    // best-effort -- toolbar should not block the demo
  }
}

async function skipPhase() {
  const phase = currentPhase.value.toLowerCase()
  if (phase === 'idle') return
  loading.value = true
  try {
    await fetch(`${API_BASE}/demo/skip/${phase}`, { method: 'POST' })
  } catch {
    // best-effort
  } finally {
    loading.value = false
  }
}

async function resetDemo() {
  loading.value = true
  try {
    await fetch(`${API_BASE}/demo/reset`, { method: 'POST' })
  } catch {
    // best-effort
  }
  localStorage.clear()
  loading.value = false
  router.push('/')
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed bottom-6 right-6 z-50">
      <!-- Collapsed: circular toggle -->
      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        leave-active-class="transition-all duration-150 ease-in"
        enter-from-class="scale-0 opacity-0"
        enter-to-class="scale-100 opacity-100"
        leave-from-class="scale-100 opacity-100"
        leave-to-class="scale-0 opacity-0"
      >
        <button
          v-if="!expanded"
          @click="expanded = true"
          class="w-12 h-12 rounded-full bg-[#2068FF] text-white shadow-lg flex items-center justify-center hover:bg-[#1a57d6] transition-colors cursor-pointer"
          title="Presenter controls"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 3 19 12 5 21 5 3" />
          </svg>
        </button>
      </Transition>

      <!-- Expanded: control panel -->
      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        leave-active-class="transition-all duration-150 ease-in"
        enter-from-class="scale-95 opacity-0 translate-y-2"
        enter-to-class="scale-100 opacity-100 translate-y-0"
        leave-from-class="scale-100 opacity-100 translate-y-0"
        leave-to-class="scale-95 opacity-0 translate-y-2"
      >
        <div
          v-if="expanded"
          class="w-[calc(100vw-2rem)] sm:w-72 rounded-xl bg-gray-900/90 backdrop-blur-md shadow-2xl border border-white/10 text-white overflow-hidden"
        >
          <!-- Header -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <span class="text-xs font-semibold uppercase tracking-wider text-white/60">Presenter</span>
            <button
              @click="expanded = false"
              class="w-6 h-6 flex items-center justify-center rounded hover:bg-white/10 text-white/60 hover:text-white transition-colors cursor-pointer"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <div class="px-4 py-3 space-y-4">
            <!-- Phase indicator -->
            <div>
              <div class="text-[10px] font-semibold uppercase tracking-wider text-white/40 mb-1">Phase</div>
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full shrink-0" :class="currentPhase === 'Idle' ? 'bg-white/30' : 'bg-emerald-400 animate-pulse'" />
                <span class="text-sm font-medium">{{ currentPhase }}</span>
              </div>
            </div>

            <!-- Speed controls -->
            <div>
              <div class="text-[10px] font-semibold uppercase tracking-wider text-white/40 mb-1.5">Speed</div>
              <div class="flex gap-1.5">
                <button
                  v-for="s in SPEEDS"
                  :key="s"
                  @click="setSpeed(s)"
                  class="flex-1 py-1.5 rounded-md text-xs font-semibold transition-colors cursor-pointer"
                  :class="activeSpeed === s
                    ? 'bg-[#2068FF] text-white'
                    : 'bg-white/10 text-white/60 hover:bg-white/20 hover:text-white'"
                >
                  {{ s }}x
                </button>
              </div>
            </div>

            <!-- Skip button (only when a phase is active) -->
            <button
              v-if="skipLabel"
              @click="skipPhase"
              :disabled="loading"
              class="w-full py-2 rounded-md text-xs font-semibold bg-white/10 hover:bg-white/20 text-white/80 hover:text-white transition-colors disabled:opacity-40 cursor-pointer"
            >
              {{ loading ? 'Skipping...' : skipLabel }}
            </button>

            <!-- Reset -->
            <button
              @click="resetDemo"
              :disabled="loading"
              class="w-full py-2 rounded-md text-xs font-semibold bg-red-600/80 hover:bg-red-600 text-white transition-colors disabled:opacity-40 cursor-pointer"
            >
              {{ loading ? 'Resetting...' : 'Reset Demo' }}
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </Teleport>
</template>
