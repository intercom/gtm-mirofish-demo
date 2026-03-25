<script setup>
import { watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from './components/layout/AppLayout.vue'
import ToastContainer from './components/ui/ToastContainer.vue'
import OfflineBanner from './components/common/OfflineBanner.vue'
import PresenterToolbar from './components/demo/PresenterToolbar.vue'
import { useTheme } from './composables/useTheme'
import { useIntercom } from './composables/useIntercom'
import { useDemoMode } from './composables/useDemoMode'
import { useSimulationStore } from './stores/simulation'
import { useScenariosStore } from './stores/scenarios'

const route = useRoute()
const { setRouteDefault } = useTheme()
const intercom = useIntercom()
const { isDemoMode } = useDemoMode()
const simulation = useSimulationStore()
const scenarios = useScenariosStore()

watch(() => route.name, (name) => {
  setRouteDefault(name === 'landing' ? 'dark' : 'light')
}, { immediate: true })

onMounted(() => {
  intercom.install()
  intercom.boot()
})

watch(
  () => ({
    status: simulation.status,
    currentRound: simulation.progress.currentRound,
    totalRounds: simulation.progress.totalRounds,
  }),
  (ctx) => {
    const scenarioName = scenarios.detailCache[route.params?.id]?.name
    intercom.update({
      gtm_scenario: scenarioName || undefined,
      simulation_status: ctx.status,
      current_round: ctx.currentRound,
      total_rounds: ctx.totalRounds,
    })
  },
)

onUnmounted(() => {
  intercom.shutdown()
})
</script>

<template>
  <AppLayout>
    <router-view v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>
  </AppLayout>
  <OfflineBanner />
  <ToastContainer />
  <PresenterToolbar v-if="isDemoMode" />
</template>
