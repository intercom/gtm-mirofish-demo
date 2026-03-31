<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useToast } from '../../composables/useToast'
import { useDemoMode } from '../../composables/useDemoMode'
import { memoryApi } from '../../api/memory'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({}),
  },
  zepKey: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])

const toast = useToast()
const { isDemoMode } = useDemoMode()

const windowSize = ref(props.modelValue.windowSize ?? 5)
const searchDepth = ref(props.modelValue.searchDepth ?? 10)
const extractionLevel = ref(props.modelValue.extractionLevel ?? 'medium')
const crossSimulation = ref(props.modelValue.crossSimulation ?? false)

const connectionStatus = ref(null)
const connectionError = ref('')
const loadingStats = ref(false)
const stats = ref(null)

const extractionLevels = [
  { id: 'low', label: 'Low', description: 'Only explicit facts' },
  { id: 'medium', label: 'Medium', description: 'Inferred context' },
  { id: 'high', label: 'High', description: 'Speculative insights' },
]

const configSnapshot = computed(() => ({
  windowSize: windowSize.value,
  searchDepth: searchDepth.value,
  extractionLevel: extractionLevel.value,
  crossSimulation: crossSimulation.value,
}))

watch(configSnapshot, (val) => {
  emit('update:modelValue', val)
}, { deep: true })

const hasZepKey = computed(() => !!props.zepKey || isDemoMode)

const statusBadge = computed(() => {
  if (isDemoMode) return { label: 'Simulated', cls: 'text-[#090] bg-[rgba(0,153,0,0.08)] border-[rgba(0,153,0,0.2)]' }
  if (connectionStatus.value === 'success') return { label: 'Connected', cls: 'text-[#090] bg-[rgba(0,153,0,0.08)] border-[rgba(0,153,0,0.2)]' }
  if (connectionStatus.value === 'error') return { label: 'Disconnected', cls: 'text-[var(--color-fin-orange)] bg-[rgba(255,86,0,0.08)] border-[rgba(255,86,0,0.2)]' }
  if (connectionStatus.value === 'testing') return { label: 'Testing...', cls: 'text-[var(--color-primary)] bg-[rgba(32,104,255,0.08)] border-[rgba(32,104,255,0.2)]' }
  if (!props.zepKey) return { label: 'No Key', cls: 'text-[var(--color-text-muted)] bg-[var(--color-tint)] border-[var(--color-border)]' }
  return null
})

async function testConnection() {
  if (isDemoMode) {
    connectionStatus.value = 'success'
    toast.success('Memory service simulated')
    return
  }

  if (!props.zepKey) {
    toast.error('Configure Zep API key in Settings first')
    return
  }

  connectionStatus.value = 'testing'
  connectionError.value = ''

  try {
    const { data } = await memoryApi.testConnection({ apiKey: props.zepKey })
    if (data.ok) {
      connectionStatus.value = 'success'
      toast.success('Zep memory service connected')
    } else {
      connectionStatus.value = 'error'
      connectionError.value = data.error || 'Connection failed'
      toast.error('Zep memory connection failed')
    }
  } catch (e) {
    connectionStatus.value = 'error'
    connectionError.value = e.message || 'Network error'
    toast.error('Zep memory connection failed')
  }
}

async function fetchStats() {
  loadingStats.value = true
  try {
    const { data } = await memoryApi.getStats({ zepKey: props.zepKey || '' })
    if (data.ok) {
      stats.value = data.stats
    }
  } catch {
    stats.value = null
  } finally {
    loadingStats.value = false
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<template>
  <div class="space-y-5">
    <!-- Zep Connection Status -->
    <div>
      <div class="flex items-center justify-between mb-3">
        <label class="text-xs uppercase tracking-wider text-[var(--color-text-muted)]">Memory Service</label>
        <span
          v-if="statusBadge"
          class="text-[10px] font-medium px-2 py-0.5 rounded-full border"
          :class="statusBadge.cls"
        >
          {{ statusBadge.label }}
        </span>
      </div>

      <button
        @click="testConnection"
        :disabled="connectionStatus === 'testing'"
        class="w-full px-3 py-2 text-xs border rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        :class="connectionStatus === 'success'
          ? 'border-[rgba(0,153,0,0.3)] text-[#090] hover:bg-[rgba(0,153,0,0.04)]'
          : connectionStatus === 'error'
            ? 'border-[rgba(255,86,0,0.3)] text-[var(--color-fin-orange)] hover:bg-[rgba(255,86,0,0.04)]'
            : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] hover:bg-[var(--color-primary-light)]'"
      >
        {{ connectionStatus === 'testing' ? 'Testing...' : connectionStatus === 'success' ? '&#10003; Connected' : connectionStatus === 'error' ? '&#10007; Retry' : 'Test Memory Connection' }}
      </button>
      <p v-if="connectionError" class="text-[10px] text-red-500 mt-1">{{ connectionError }}</p>
      <p v-else-if="!hasZepKey" class="text-[10px] text-[var(--color-text-muted)] mt-1">
        Configure Zep key in
        <router-link to="/settings" class="text-[var(--color-primary)] hover:underline">Settings</router-link>
      </p>
    </div>

    <!-- Memory Window Size -->
    <div>
      <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
        Context Window
      </label>
      <input
        type="range"
        v-model.number="windowSize"
        min="1"
        max="20"
        step="1"
        class="w-full accent-[var(--color-primary)]"
      />
      <div class="flex justify-between text-[10px] text-[var(--color-text-muted)] mt-1">
        <span>1 round</span>
        <span class="font-semibold text-[var(--color-primary)] text-xs">{{ windowSize }} rounds</span>
        <span>20 rounds</span>
      </div>
    </div>

    <!-- Memory Search Depth -->
    <div>
      <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
        Search Depth
      </label>
      <input
        type="range"
        v-model.number="searchDepth"
        min="1"
        max="50"
        step="1"
        class="w-full accent-[var(--color-primary)]"
      />
      <div class="flex justify-between text-[10px] text-[var(--color-text-muted)] mt-1">
        <span>1 result</span>
        <span class="font-semibold text-[var(--color-primary)] text-xs">{{ searchDepth }} results</span>
        <span>50 results</span>
      </div>
    </div>

    <!-- Fact Extraction Level -->
    <div>
      <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
        Fact Extraction
      </label>
      <div class="flex gap-1.5">
        <button
          v-for="level in extractionLevels"
          :key="level.id"
          @click="extractionLevel = level.id"
          class="flex-1 px-2 py-1.5 text-[11px] rounded-lg border transition-colors cursor-pointer text-center"
          :class="extractionLevel === level.id
            ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
            : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]'"
        >
          {{ level.label }}
        </button>
      </div>
      <p class="text-[10px] text-[var(--color-text-muted)] mt-1.5">
        {{ extractionLevels.find(l => l.id === extractionLevel)?.description }}
      </p>
    </div>

    <!-- Cross-Simulation Memory -->
    <div>
      <label class="flex items-center gap-2.5 cursor-pointer group">
        <input
          type="checkbox"
          v-model="crossSimulation"
          class="accent-[var(--color-primary)] w-3.5 h-3.5"
        />
        <div>
          <span class="text-xs font-medium text-[var(--color-text)] group-hover:text-[var(--color-primary)] transition-colors">
            Cross-simulation memory
          </span>
          <p class="text-[10px] text-[var(--color-text-muted)]">Carry agent memories forward between runs</p>
        </div>
      </label>
    </div>

    <!-- Memory Usage Stats -->
    <div v-if="stats" class="border-t border-[var(--color-border)] pt-4">
      <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-3">Usage</label>
      <div class="grid grid-cols-2 gap-2">
        <div class="bg-[var(--color-tint)] rounded-lg p-2.5 text-center">
          <div class="text-sm font-semibold text-[var(--color-text)]">{{ stats.totalFacts.toLocaleString() }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">Facts</div>
        </div>
        <div class="bg-[var(--color-tint)] rounded-lg p-2.5 text-center">
          <div class="text-sm font-semibold text-[var(--color-text)]">{{ stats.totalEpisodes.toLocaleString() }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">Episodes</div>
        </div>
        <div class="bg-[var(--color-tint)] rounded-lg p-2.5 text-center">
          <div class="text-sm font-semibold text-[var(--color-text)]">{{ stats.graphNodes.toLocaleString() }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">Nodes</div>
        </div>
        <div class="bg-[var(--color-tint)] rounded-lg p-2.5 text-center">
          <div class="text-sm font-semibold text-[var(--color-text)]">{{ stats.graphEdges.toLocaleString() }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">Edges</div>
        </div>
      </div>
    </div>

    <div v-else-if="loadingStats" class="text-center py-3">
      <div class="inline-block w-4 h-4 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin"></div>
    </div>
  </div>
</template>
