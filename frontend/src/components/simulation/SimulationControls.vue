<script setup>
import { ref, computed, inject, onMounted, onUnmounted, watch } from 'vue'
import { useScenariosStore } from '../../stores/scenarios'
import { useSettingsStore } from '../../stores/settings'
import { simulationApi } from '../../api/simulation'
import { API_BASE } from '../../api/client'

const polling = inject('polling')
const demoMode = inject('demoMode', ref(false))

const scenariosStore = useScenariosStore()
const settingsStore = useSettingsStore()

// --- Configuration state ---
const selectedScenario = ref('')
const agentCount = ref(5)
const roundCount = ref(10)
const llmProvider = ref('auto')
const starting = ref(false)
const startError = ref('')
const stopping = ref(false)

// --- Elapsed time tracking ---
const startedAt = ref(null)
const elapsedSeconds = ref(0)
let elapsedTimer = null

// --- SSE connection ---
let eventSource = null

const providerOptions = [
  { value: 'auto', label: 'Auto (server default)' },
  { value: 'anthropic', label: 'Claude (Anthropic)' },
  { value: 'openai', label: 'GPT-4o (OpenAI)' },
  { value: 'gemini', label: 'Gemini (Google)' },
]

// --- Computed state from polling ---
const status = computed(() => {
  const rs = polling.runStatus.value?.runner_status
  if (!rs || rs === 'idle') return 'idle'
  if (rs === 'starting') return 'starting'
  if (rs === 'running') return 'running'
  if (rs === 'paused') return 'paused'
  if (rs === 'completed' || rs === 'stopped') return 'completed'
  if (rs === 'failed') return 'failed'
  return 'idle'
})

const isRunning = computed(() =>
  ['starting', 'running', 'paused'].includes(status.value),
)

const isIdle = computed(() =>
  ['idle', 'completed', 'failed'].includes(status.value) &&
  polling.simStatus.value !== 'running' &&
  polling.simStatus.value !== 'building',
)

const currentRound = computed(() => polling.runStatus.value?.current_round ?? 0)
const totalRounds = computed(() => polling.runStatus.value?.total_rounds ?? 0)
const progressPercent = computed(() => polling.runStatus.value?.progress_percent ?? 0)

const currentAgent = computed(() => {
  const actions = polling.recentActions.value
  if (!actions.length) return null
  const last = actions[actions.length - 1]
  return last?.agent_name || `Agent #${last?.agent_id}`
})

const elapsedFormatted = computed(() => {
  const s = elapsedSeconds.value
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${m}:${String(sec).padStart(2, '0')}`
})

const modeLabel = computed(() => demoMode.value ? 'Demo Mode' : 'OASIS Mode')
const modeClass = computed(() =>
  demoMode.value
    ? 'bg-amber-100 text-amber-700'
    : 'bg-emerald-100 text-emerald-700',
)

// --- Elapsed time ---
function startElapsedTimer() {
  startedAt.value = Date.now()
  elapsedSeconds.value = 0
  elapsedTimer = setInterval(() => {
    elapsedSeconds.value = Math.floor((Date.now() - startedAt.value) / 1000)
  }, 1000)
}

function stopElapsedTimer() {
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
    elapsedTimer = null
  }
}

// --- SSE connection (attempt, fallback to polling) ---
function connectSSE(simId) {
  try {
    const url = `${API_BASE}/simulation/${simId}/stream`
    eventSource = new EventSource(url)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.current_round != null) {
          polling.runStatus.value = {
            ...polling.runStatus.value,
            ...data,
          }
        }
      } catch {
        // Ignore parse errors
      }
    }

    eventSource.onerror = () => {
      // SSE not available — close and rely on polling
      closeSSE()
    }
  } catch {
    // SSE construction failed — polling is the fallback
  }
}

function closeSSE() {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

// --- Actions ---
async function startSimulation() {
  starting.value = true
  startError.value = ''

  try {
    const simId = polling.runStatus.value?.simulation_id
    if (!simId) {
      startError.value = 'No simulation ID available. Build a graph first.'
      return
    }

    await simulationApi.start({
      simulation_id: simId,
      max_rounds: roundCount.value,
      force: true,
    })

    startElapsedTimer()
    connectSSE(simId)
  } catch (err) {
    startError.value = err.message || 'Failed to start simulation'
  } finally {
    starting.value = false
  }
}

async function stopSimulation() {
  stopping.value = true
  try {
    const simId = polling.runStatus.value?.simulation_id
    if (simId) {
      await simulationApi.stop({ simulation_id: simId })
    }
    stopElapsedTimer()
    closeSSE()
  } catch {
    // Stop is best-effort
  } finally {
    stopping.value = false
  }
}

// --- Watch for simulation state transitions ---
watch(status, (val, oldVal) => {
  if (val === 'running' && oldVal !== 'running' && !elapsedTimer) {
    startElapsedTimer()
  }
  if (['completed', 'failed', 'idle'].includes(val) && elapsedTimer) {
    stopElapsedTimer()
    closeSSE()
  }
})

// --- Lifecycle ---
onMounted(() => {
  scenariosStore.fetchScenarios()

  // Resume timer if simulation is already running
  if (status.value === 'running') {
    startElapsedTimer()
  }
})

onUnmounted(() => {
  stopElapsedTimer()
  closeSSE()
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg">
    <!-- Header with mode badge -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)]">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Simulation Controls</h3>
      <span class="px-2.5 py-1 rounded-full text-[10px] font-semibold tracking-wide uppercase" :class="modeClass">
        {{ modeLabel }}
      </span>
    </div>

    <div class="p-4">
      <!-- ═══ CONFIGURATION SECTION (idle) ═══ -->
      <template v-if="isIdle">
        <div class="space-y-4">
          <!-- Template selector -->
          <div>
            <label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
              Scenario Template
            </label>
            <select
              v-model="selectedScenario"
              class="w-full px-3 py-2 text-sm bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
            >
              <option value="">Select a template...</option>
              <option
                v-for="scenario in scenariosStore.scenarios"
                :key="scenario.id"
                :value="scenario.id"
              >
                {{ scenario.name }}
              </option>
            </select>
          </div>

          <!-- Agent count slider -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-xs font-medium text-[var(--color-text-secondary)]">Agent Count</label>
              <span class="text-xs font-semibold text-[var(--color-primary)] tabular-nums">{{ agentCount }}</span>
            </div>
            <input
              v-model.number="agentCount"
              type="range"
              min="2"
              max="8"
              step="1"
              class="slider w-full"
            />
            <div class="flex justify-between text-[10px] text-[var(--color-text-muted)] mt-0.5">
              <span>2</span>
              <span>8</span>
            </div>
          </div>

          <!-- Round count slider -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-xs font-medium text-[var(--color-text-secondary)]">Rounds</label>
              <span class="text-xs font-semibold text-[var(--color-primary)] tabular-nums">{{ roundCount }}</span>
            </div>
            <input
              v-model.number="roundCount"
              type="range"
              min="4"
              max="20"
              step="1"
              class="slider w-full"
            />
            <div class="flex justify-between text-[10px] text-[var(--color-text-muted)] mt-0.5">
              <span>4</span>
              <span>20</span>
            </div>
          </div>

          <!-- LLM Provider selector -->
          <div>
            <label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">
              LLM Provider
            </label>
            <select
              v-model="llmProvider"
              class="w-full px-3 py-2 text-sm bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-[var(--color-text)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
            >
              <option
                v-for="opt in providerOptions"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </option>
            </select>
          </div>

          <!-- Error message -->
          <p v-if="startError" class="text-xs text-[var(--color-error)]">
            {{ startError }}
          </p>

          <!-- Start button -->
          <button
            :disabled="starting"
            class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold text-white bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] active:bg-[var(--color-primary-active)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            @click="startSimulation"
          >
            <svg v-if="starting" class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-dasharray="31.4 31.4" stroke-linecap="round" />
            </svg>
            <svg v-else class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path d="M6.3 2.84A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.27l9.344-5.891a1.5 1.5 0 000-2.538L6.3 2.841z" />
            </svg>
            {{ starting ? 'Starting...' : 'Start Simulation' }}
          </button>
        </div>
      </template>

      <!-- ═══ RUNNING SECTION ═══ -->
      <template v-else-if="isRunning">
        <div class="space-y-4">
          <!-- Progress bar -->
          <div>
            <div class="flex items-center justify-between text-xs text-[var(--color-text-secondary)] mb-1.5">
              <span class="font-medium">Round {{ currentRound }} of {{ totalRounds }}</span>
              <span class="tabular-nums">{{ progressPercent }}%</span>
            </div>
            <div class="h-2 bg-[var(--color-tint)] rounded-full overflow-hidden">
              <div
                class="h-full rounded-full bg-[var(--color-primary)] transition-all duration-700 ease-out"
                :style="{ width: `${progressPercent}%` }"
              />
            </div>
          </div>

          <!-- Elapsed time -->
          <div class="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
            <svg class="w-3.5 h-3.5 text-[var(--color-text-muted)]" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a.75.75 0 00-1.5 0v5c0 .414.336.75.75.75h4a.75.75 0 000-1.5h-3.25V5z" clip-rule="evenodd" />
            </svg>
            <span>Elapsed: <strong class="text-[var(--color-text)] tabular-nums">{{ elapsedFormatted }}</strong></span>
          </div>

          <!-- Current agent -->
          <div v-if="currentAgent" class="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
            <svg class="w-3.5 h-3.5 text-[var(--color-text-muted)]" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z" />
            </svg>
            <span class="truncate">Acting: <strong class="text-[var(--color-text)]">{{ currentAgent }}</strong></span>
          </div>

          <!-- Control buttons -->
          <div class="flex gap-2 pt-1">
            <button
              :disabled="stopping"
              class="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold text-[var(--color-error)] bg-[var(--color-error-light)] hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              @click="stopSimulation"
            >
              <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                <rect x="5" y="5" width="10" height="10" rx="1" />
              </svg>
              {{ stopping ? 'Stopping...' : 'Stop' }}
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.slider {
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: var(--color-tint);
  outline: none;
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid var(--color-surface);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  transition: transform 0.15s ease;
}
.slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}
.slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-primary);
  cursor: pointer;
  border: 2px solid var(--color-surface);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}
</style>
