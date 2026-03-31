import { ref } from 'vue'
import { useKeyboardShortcuts } from './useKeyboardShortcuts'
import { useToast } from './useToast'

const SPEED_STEPS = [0.5, 1, 1.5, 2, 3, 5]

/**
 * Registers simulation-specific keyboard shortcuts via the global registry.
 * Automatically unregistered when the calling component unmounts.
 *
 * @param {{ onPlayPause?: Function, onPrevRound?: Function, onNextRound?: Function, onBranch?: Function }} callbacks
 * @returns {{ playbackSpeed: Ref<number>, showMetrics: Ref<boolean>, showThinking: Ref<boolean>, isFullscreen: Ref<boolean> }}
 */
export function useSimulationShortcuts(callbacks = {}) {
  const toast = useToast()
  const { register } = useKeyboardShortcuts()

  const playbackSpeed = ref(1)
  const showMetrics = ref(true)
  const showThinking = ref(false)
  const isFullscreen = ref(false)

  function cycleSpeed(direction) {
    const currentIdx = SPEED_STEPS.indexOf(playbackSpeed.value)
    const idx = currentIdx === -1 ? 1 : currentIdx
    const nextIdx = Math.max(0, Math.min(SPEED_STEPS.length - 1, idx + direction))
    playbackSpeed.value = SPEED_STEPS[nextIdx]
    toast.info(`Playback speed: ${playbackSpeed.value}x`)
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {})
      isFullscreen.value = true
    } else {
      document.exitFullscreen().catch(() => {})
      isFullscreen.value = false
    }
  }

  register(' ', () => {
    if (callbacks.onPlayPause) callbacks.onPlayPause()
    else toast.info('Play/Pause toggled')
  }, { description: 'Play / Pause simulation', category: 'Simulation' })

  register('arrowleft', () => {
    if (callbacks.onPrevRound) callbacks.onPrevRound()
    else toast.info('Previous round')
  }, { description: 'Previous round', category: 'Simulation' })

  register('arrowright', () => {
    if (callbacks.onNextRound) callbacks.onNextRound()
    else toast.info('Next round')
  }, { description: 'Next round', category: 'Simulation' })

  register('+', () => cycleSpeed(1), { description: 'Increase playback speed', category: 'Simulation' })
  register('=', () => cycleSpeed(1), { description: 'Increase playback speed', category: 'Simulation' })
  register('-', () => cycleSpeed(-1), { description: 'Decrease playback speed', category: 'Simulation' })

  register('t', () => {
    showThinking.value = !showThinking.value
    toast.info(showThinking.value ? 'Agent thinking visible' : 'Agent thinking hidden')
  }, { description: 'Toggle agent thinking transparency', category: 'Simulation' })

  register('m', () => {
    showMetrics.value = !showMetrics.value
    toast.info(showMetrics.value ? 'Metrics shown' : 'Metrics hidden')
  }, { description: 'Toggle metrics panel', category: 'Simulation' })

  register('f', toggleFullscreen, { description: 'Toggle full-screen mode', category: 'Simulation' })

  register('b', () => {
    if (callbacks.onBranch) callbacks.onBranch()
    else toast.info('Branch created at current round')
  }, { description: 'Create branch at current round', category: 'Simulation' })

  return {
    playbackSpeed,
    showMetrics,
    showThinking,
    isFullscreen,
  }
}
