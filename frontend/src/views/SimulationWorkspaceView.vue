<script setup>
import { ref, computed, provide, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSimulationPolling } from '../composables/useSimulationPolling'
import { useToast } from '../composables/useToast'
import { useSimulationStore } from '../stores/simulation'
import WorkspacePhaseNav from '../components/simulation/WorkspacePhaseNav.vue'
import GraphPanel from '../components/simulation/GraphPanel.vue'
import SimulationPanel from '../components/simulation/SimulationPanel.vue'
import NavigationMiniMap from '../components/navigation/NavigationMiniMap.vue'
import LiveFeed from '../components/simulation/LiveFeed.vue'
import SimulationControls from '../components/simulation/SimulationControls.vue'
import LiveMetrics from '../components/simulation/LiveMetrics.vue'
import SimulationProgressBar from '../components/simulation/SimulationProgressBar.vue'

const props = defineProps({
  taskId: { type: String, required: true },
})

const route = useRoute()
const router = useRouter()
const toast = useToast()
const simulationStore = useSimulationStore()

const polling = useSimulationPolling(() => props.taskId)
provide('polling', polling)

const activeTab = ref(route.query.tab === 'simulation' ? 'simulation' : 'graph')
const demoMode = ref(false)
provide('demoMode', demoMode)

const showCompleteBanner = ref(false)
let bannerTimer = null

const scenarioName = computed(() =>
  simulationStore.scenarioConfig?.scenarioName || 'Simulation',
)

const isReviewMode = computed(() => polling.simStatus.value === 'completed')
const isSimActive = computed(() =>
  polling.simStatus.value === 'running' || polling.simStatus.value === 'building',
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
    <!-- Breadcrumbs + Mini-map -->
    <div class="flex items-center justify-between px-4 md:px-6 pt-3">
      <div class="text-xs text-[var(--color-text-muted)]">
        <router-link
          to="/"
          class="text-[var(--color-text-muted)] hover:text-[var(--color-primary)] no-underline transition-colors"
        >Home</router-link>
        <span class="mx-1">/</span>
        <span>{{ scenarioName }}</span>
        <span class="mx-1">/</span>
        <span class="text-[var(--color-text)]">Workspace</span>
      </div>
      <NavigationMiniMap class="hidden md:block" />
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
      <!-- Graph tab (unchanged) -->
      <div v-show="activeTab === 'graph'" class="absolute inset-0">
        <GraphPanel :taskId="taskId" :demoMode="demoMode" />
      </div>

      <!-- Simulation tab -->
      <div v-show="activeTab === 'simulation'" class="absolute inset-0 flex flex-col">

        <!-- Active simulation: split panel layout -->
        <div v-if="!isReviewMode" class="flex-1 overflow-hidden">
          <div class="workspace-panels h-full p-4 md:p-6 gap-4 md:gap-6">
            <!-- Left panel (60%): Live Feed -->
            <div class="workspace-left min-h-0">
              <LiveFeed />
            </div>

            <!-- Right panel (40%): Controls + Metrics -->
            <div class="workspace-right flex flex-col gap-4 md:gap-6 min-h-0">
              <!-- Controls (top ~30%) -->
              <div class="workspace-controls shrink-0">
                <SimulationControls :taskId="taskId" />
              </div>
              <!-- Metrics (bottom ~70%) -->
              <div class="flex-1 min-h-0">
                <LiveMetrics />
              </div>
            </div>
          </div>
        </div>

        <!-- Review mode: full SimulationPanel with all data -->
        <div v-else class="flex-1 overflow-hidden">
          <SimulationPanel :taskId="taskId" />
        </div>

        <!-- Bottom progress bar -->
        <SimulationProgressBar
          v-if="isSimActive || isReviewMode"
          :taskId="taskId"
        />
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

/* Panel layout: side-by-side on desktop, stacked on mobile */
.workspace-panels {
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: 1fr 1fr;
}

.workspace-left {
  overflow: hidden;
}

.workspace-right {
  overflow: hidden;
}

@media (min-width: 1024px) {
  .workspace-panels {
    grid-template-columns: 3fr 2fr;
    grid-template-rows: 1fr;
  }
}
</style>
