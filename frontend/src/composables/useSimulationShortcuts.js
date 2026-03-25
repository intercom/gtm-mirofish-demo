import { ref } from 'vue'
import { useKeyboardShortcuts } from './useKeyboardShortcuts'
import { useToast } from './useToast'

const SPEED_STEPS = [0.5, 1, 1.5, 2, 3, 5]

/**
 * Registers simulation-specific keyboard shortcuts.
 * Automatically unregistered when the calling component unmounts.
 *
 * @param {{ onPlayPause?: Function, onPrevRound?: Function, onNextRound?: Function, onBranch?: Function }} callbacks
 * @returns {{ playbackSpeed: Ref<number>, showMetrics: Ref<boolean>, showThinking: Ref<boolean>, isFullscreen: Ref<boolean> }}
 */
export function useSimulationShortcuts(callbacks = {}) {
  const toast = useToast()

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

  const shortcuts = [
    {
      key: ' ',
      description: 'Play / Pause simulation',
      handler: () => {
        if (callbacks.onPlayPause) callbacks.onPlayPause()
        else toast.info('Play/Pause toggled')
      },
    },
    {
      key: 'ArrowLeft',
      description: 'Previous round',
      handler: () => {
        if (callbacks.onPrevRound) callbacks.onPrevRound()
        else toast.info('Previous round')
      },
    },
    {
      key: 'ArrowRight',
      description: 'Next round',
      handler: () => {
        if (callbacks.onNextRound) callbacks.onNextRound()
        else toast.info('Next round')
      },
    },
    {
      key: '+',
      description: 'Increase playback speed',
      handler: () => cycleSpeed(1),
    },
    {
      key: '=',
      description: 'Increase playback speed',
      handler: () => cycleSpeed(1),
    },
    {
      key: '-',
      description: 'Decrease playback speed',
      handler: () => cycleSpeed(-1),
    },
    {
      key: 't',
      description: 'Toggle agent thinking transparency',
      handler: () => {
        showThinking.value = !showThinking.value
        toast.info(showThinking.value ? 'Agent thinking visible' : 'Agent thinking hidden')
      },
    },
    {
      key: 'm',
      description: 'Toggle metrics panel',
      handler: () => {
        showMetrics.value = !showMetrics.value
        toast.info(showMetrics.value ? 'Metrics shown' : 'Metrics hidden')
      },
    },
    {
      key: 'f',
      description: 'Toggle full-screen mode',
      handler: toggleFullscreen,
    },
    {
      key: 'b',
      description: 'Create branch at current round',
      handler: () => {
        if (callbacks.onBranch) callbacks.onBranch()
        else toast.info('Branch created at current round')
      },
    },
  ]

  useKeyboardShortcuts(shortcuts)

  return {
    playbackSpeed,
    showMetrics,
    showThinking,
    isFullscreen,
    shortcuts,
  }
}
