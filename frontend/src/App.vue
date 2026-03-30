<script setup>
import { computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from './components/layout/AppLayout.vue'
import ErrorBoundary from './components/ui/ErrorBoundary.vue'
import ToastContainer from './components/ui/ToastContainer.vue'
import OfflineBanner from './components/common/OfflineBanner.vue'
import NavigationShortcutIndicator from './components/ui/NavigationShortcutIndicator.vue'
import OnboardingTour from './components/ui/OnboardingTour.vue'
import PwaUpdateBanner from './components/ui/PwaUpdateBanner.vue'
import PwaInstallPrompt from './components/ui/PwaInstallPrompt.vue'
import D3PerfOverlay from './components/ui/D3PerfOverlay.vue'
import PresenterToolbar from './components/demo/PresenterToolbar.vue'
import CommandPalette from './components/common/CommandPalette.vue'
import SystemStatusBar from './components/common/SystemStatusBar.vue'
import KeyboardShortcutsModal from './components/common/KeyboardShortcutsModal.vue'
import KeyboardShortcutCard from './components/ui/KeyboardShortcutCard.vue'
import DemoModeOverlay from './components/common/DemoModeOverlay.vue'
import TutorialSystem from './components/tutorial/TutorialSystem.vue'
import ScenarioWalkthrough from './components/tutorial/ScenarioWalkthrough.vue'
import InteractiveTutorialOverlay from './components/tutorial/InteractiveTutorialOverlay.vue'
import ShortcutQuickRef from './components/common/ShortcutQuickRef.vue'
import { useTheme } from './composables/useTheme'
import { useKeyboardShortcuts } from './composables/useKeyboardShortcuts'
import { useIntercom } from './composables/useIntercom'
import { useDemoMode } from './composables/useDemoMode'
import { useCommandPalette } from './composables/useCommandPalette'
import { useResourcePreload } from './composables/useResourcePreload'
import { usePageTransition } from './composables/usePageTransition'
import { useSimulationStore } from './stores/simulation'
import { useScenariosStore } from './stores/scenarios'
import { useSettingsStore } from './stores/settings'
import { useTutorialStore } from './stores/tutorial'

const route = useRoute()
const router = useRouter()
const { setRouteDefault } = useTheme()
const intercom = useIntercom()
const { isDemoMode } = useDemoMode()
useCommandPalette()
useResourcePreload()
const { register, showHelp } = useKeyboardShortcuts()
const { transitionName } = usePageTransition()
const simulation = useSimulationStore()
const scenarios = useScenariosStore()
const settings = useSettingsStore()
const tutorial = useTutorialStore()

const isDev = import.meta.env.DEV
const showStatusBar = computed(() => isDev || settings.statusBarEnabled)

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
  showHelp.value = !showHelp.value
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
  tutorial.checkFirstVisit()
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
    <ErrorBoundary>
      <router-view v-slot="{ Component }">
        <Transition :name="transitionName" mode="out-in">
          <component :is="Component" />
        </Transition>
      </router-view>
    </ErrorBoundary>
  </AppLayout>
  <OfflineBanner />
  <ToastContainer />
  <PwaUpdateBanner />
  <PwaInstallPrompt />
  <NavigationShortcutIndicator />
  <OnboardingTour />
  <CommandPalette />
  <KeyboardShortcutsModal />
  <KeyboardShortcutCard />
  <DemoModeOverlay v-if="isDemoMode" />
  <D3PerfOverlay />
  <PresenterToolbar v-if="isDemoMode" />
  <SystemStatusBar v-if="showStatusBar" />
  <TutorialSystem />
  <ScenarioWalkthrough />
  <InteractiveTutorialOverlay />
  <ShortcutQuickRef />
</template>
