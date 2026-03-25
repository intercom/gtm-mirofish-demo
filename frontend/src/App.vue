<script setup>
import { watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from './components/layout/AppLayout.vue'
import ToastContainer from './components/ui/ToastContainer.vue'
import PresenterToolbar from './components/demo/PresenterToolbar.vue'
import { useTheme } from './composables/useTheme'
import { useIntercom } from './composables/useIntercom'
import { useDemoMode } from './composables/useDemoMode'
import { useKeyboardShortcuts } from './composables/useKeyboardShortcuts'
import { useSimulationStore } from './stores/simulation'
import { useScenariosStore } from './stores/scenarios'

const route = useRoute()
const router = useRouter()
const { setRouteDefault } = useTheme()
const intercom = useIntercom()
const { isDemoMode } = useDemoMode()
const { register } = useKeyboardShortcuts()
const simulation = useSimulationStore()
const scenarios = useScenariosStore()

// --- Global keyboard shortcuts ---

register('mod+k', () => {
  window.dispatchEvent(new CustomEvent('shortcut:command-palette'))
}, { description: 'Open command palette' })

register('mod+n', () => {
  router.push('/')
}, { description: 'New simulation' })

register('mod+s', () => {
  window.dispatchEvent(new CustomEvent('shortcut:save'))
}, { description: 'Save current work' })

register('escape', () => {
  window.dispatchEvent(new CustomEvent('shortcut:close-overlay'))
}, { description: 'Close modal or panel' })

register('/', () => {
  window.dispatchEvent(new CustomEvent('shortcut:focus-search'))
}, { description: 'Focus search' })

register('?', () => {
  window.dispatchEvent(new CustomEvent('shortcut:shortcuts-help'))
}, { description: 'Show keyboard shortcuts' })

register('g+d', () => {
  router.push('/simulations')
}, { description: 'Go to Dashboard', category: 'Navigation' })

register('g+s', () => {
  router.push('/simulations')
}, { description: 'Go to Simulations', category: 'Navigation' })

register('g+r', () => {
  router.push('/simulations')
}, { description: 'Go to Reports', category: 'Navigation' })

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
  <ToastContainer />
  <PresenterToolbar v-if="isDemoMode" />
</template>
