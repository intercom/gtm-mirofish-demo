<script setup>
import { ref, computed, provide, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSimulationPolling } from '../composables/useSimulationPolling'
import { useToast } from '../composables/useToast'
import { useScenariosStore } from '../stores/scenarios'
import { useSimulationStore } from '../stores/simulation'
import { AppBreadcrumb } from '../components/common'
import { useBreadcrumbs } from '../composables/useBreadcrumbs'
import WorkspacePhaseNav from '../components/simulation/WorkspacePhaseNav.vue'
import GraphPanel from '../components/simulation/GraphPanel.vue'
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
const demoMode = ref(false)
provide('demoMode', demoMode)

const showCompleteBanner = ref(false)
let bannerTimer = null

const scenarioName = computed(() =>
  simulationStore.scenarioConfig?.scenarioName || 'Simulation',
)

const { crumbs } = useBreadcrumbs(
  computed(() => ({ workspace: scenarioName.value })),
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
    <AppBreadcrumb :crumbs="crumbs" />

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
        <GraphPanel :taskId="taskId" :demoMode="demoMode" />
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
