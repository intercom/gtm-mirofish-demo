<script setup>
import { ref, computed, provide, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSimulationPolling } from '../composables/useSimulationPolling'
import { useToast } from '../composables/useToast'
import { useScenariosStore } from '../stores/scenarios'
import { useSimulationStore } from '../stores/simulation'
import WorkspacePhaseNav from '../components/simulation/WorkspacePhaseNav.vue'
import GraphPanel from '../components/simulation/GraphPanel.vue'
import Graph3DPanel from '../components/simulation/Graph3DPanel.vue'
import SimulationPanel from '../components/simulation/SimulationPanel.vue'

const props = defineProps({
  taskId: { type: String, required: true },
})

const route = useRoute()
const router = useRouter()
const toast = useToast()
const scenariosStore = useScenariosStore()
const simulationStore = useSimulationStore()

const polling = useSimulationPolling(() => props.taskId)
provide('polling', polling)

const activeTab = ref(route.query.tab === 'simulation' ? 'simulation' : 'graph')
const graphMode = ref('2d') // '2d' | '3d'
const demoMode = ref(false)
provide('demoMode', demoMode)

const showCompleteBanner = ref(false)
let bannerTimer = null

const scenarioName = computed(() =>
  simulationStore.scenarioConfig?.scenarioName || 'Simulation',
)

watch(() => route.query.tab, (tab) => {
  if (tab === 'graph' || tab === 'simulation') {
    activeTab.value = tab
  }
})

watch(activeTab, (tab) => {
  if (route.query.tab !== tab) {
    router.replace({ query: { ...route.query, tab } })
  }
})

function handleKeydown(e) {
  const tag = document.activeElement?.tagName?.toLowerCase()
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return
  if (e.key === '1') activeTab.value = 'graph'
  else if (e.key === '2') activeTab.value = 'simulation'
}

watch(() => polling.simStatus.value, (status, oldStatus) => {
  if (status === 'completed' && oldStatus !== 'completed') {
    if (activeTab.value === 'graph') {
      toast.info('Simulation complete! View results')
    }
    showCompleteBanner.value = true
    bannerTimer = setTimeout(() => {
      showCompleteBanner.value = false
    }, 5000)
  }
})

watch(() => polling.isDemoFallback.value, (fallback) => {
  if (fallback) {
    demoMode.value = true
  }
})

// When graph demo completes, auto-complete the simulation run so it appears in history
watch(() => polling.graphStatus.value, (status) => {
  if (status === 'complete' && demoMode.value && polling.simStatus.value !== 'completed') {
    setTimeout(() => polling.completeDemoRun(), 1500)
  }
})

onMounted(() => {
  polling.start()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  polling.stop()
  window.removeEventListener('keydown', handleKeydown)
  if (bannerTimer) clearTimeout(bannerTimer)
})
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-56px)]">
    <!-- Breadcrumbs -->
    <div class="px-4 md:px-6 pt-3 text-xs text-[var(--color-text-muted)]">
      <router-link
        to="/"
        class="text-[var(--color-text-muted)] hover:text-[var(--color-primary)] no-underline transition-colors"
      >Home</router-link>
      <span class="mx-1">/</span>
      <span>{{ scenarioName }}</span>
      <span class="mx-1">/</span>
      <span class="text-[var(--color-text)]">Workspace</span>
    </div>

    <!-- Success banner -->
    <Transition name="slide-down">
      <div
        v-if="showCompleteBanner"
        class="mx-4 md:mx-6 mt-2 flex items-center gap-3 px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-lg"
      >
        <svg class="w-5 h-5 text-emerald-600 shrink-0" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <span class="text-sm font-medium text-emerald-800 flex-1">Simulation complete!</span>
        <router-link
          :to="`/report/${taskId}`"
          class="text-sm font-medium text-emerald-700 hover:text-emerald-900 no-underline transition-colors"
        >View Report &rarr;</router-link>
      </div>
    </Transition>

    <!-- Tab nav -->
    <div class="px-4 md:px-6 pt-2">
      <WorkspacePhaseNav
        v-model:activeTab="activeTab"
        :taskId="taskId"
        :polling="polling"
      />
    </div>

    <!-- Panels -->
    <div class="flex-1 relative overflow-hidden">
      <div v-show="activeTab === 'graph'" class="absolute inset-0">
        <Graph3DPanel v-if="graphMode === '3d'" :taskId="taskId" :demoMode="demoMode" />
        <GraphPanel v-else :taskId="taskId" :demoMode="demoMode" />

        <!-- 2D/3D toggle -->
        <button
          @click="graphMode = graphMode === '2d' ? '3d' : '2d'"
          class="absolute top-4 right-6 z-30 flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-black/10 dark:bg-white/10 hover:bg-black/20 dark:hover:bg-white/20 text-[var(--color-text)] backdrop-blur-sm transition-colors border border-black/5 dark:border-white/5"
          :title="graphMode === '2d' ? 'Switch to 3D view' : 'Switch to 2D view'"
        >
          <svg v-if="graphMode === '2d'" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z" />
            <path d="M12 12l8-4.5" /><path d="M12 12v9" /><path d="M12 12L4 7.5" />
          </svg>
          <svg v-else class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <circle cx="12" cy="12" r="4" />
          </svg>
          {{ graphMode === '2d' ? '3D' : '2D' }}
        </button>
      </div>
      <div v-show="activeTab === 'simulation'" class="absolute inset-0">
        <SimulationPanel :taskId="taskId" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}
.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
