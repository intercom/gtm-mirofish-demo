import { ref, computed, watch, provide, inject, onMounted, onUnmounted, toValue } from 'vue'

const TIMELINE_KEY = Symbol('timelineScrubber')

const DEFAULT_SPEEDS = [0.5, 1, 2, 4]
const STEP_SIZE = 0.01

/**
 * Main composable — call in the parent component that owns the timeline.
 * Provides timeline state to all descendants via Vue's provide/inject.
 *
 * @param {Object} options
 * @param {import('vue').Ref<number>|number} [options.totalRounds] - Total simulation rounds (auto-calculates duration)
 * @param {number} [options.defaultSpeed=1] - Initial playback speed multiplier
 * @param {number} [options.baseDuration=10000] - Base duration in ms at 1x speed for full playback
 * @param {boolean} [options.keyboardEnabled=true] - Enable keyboard shortcuts
 */
export function useTimelineScrubber(options = {}) {
  const {
    totalRounds: totalRoundsSource,
    defaultSpeed = 1,
    baseDuration = 10000,
    keyboardEnabled = true,
  } = options

  // --- Core state ---
  const currentPosition = ref(0)
  const isPlaying = ref(false)
  const playbackSpeed = ref(defaultSpeed)
  const marks = ref([])

  // --- Derived ---
  const totalRounds = computed(() => {
    const val = toValue(totalRoundsSource)
    return typeof val === 'number' && val > 0 ? val : 1
  })

  const duration = computed(() => baseDuration / playbackSpeed.value)

  const currentRound = computed(() =>
    Math.round(currentPosition.value * (totalRounds.value - 1)) + 1,
  )

  const stepSize = computed(() =>
    totalRounds.value > 1 ? 1 / (totalRounds.value - 1) : STEP_SIZE,
  )

  // --- Callbacks ---
  const positionCallbacks = []
  const playCallbacks = []
  const pauseCallbacks = []

  function onPositionChange(cb) { positionCallbacks.push(cb) }
  function onPlay(cb) { playCallbacks.push(cb) }
  function onPause(cb) { pauseCallbacks.push(cb) }

  watch(currentPosition, (pos) => {
    positionCallbacks.forEach(cb => cb(pos))
  })

  // --- Playback loop (rAF-based) ---
  let frameId = null
  let lastTimestamp = null

  function tick(timestamp) {
    if (!isPlaying.value) return

    if (lastTimestamp !== null) {
      const elapsed = timestamp - lastTimestamp
      const increment = (elapsed / duration.value) * playbackSpeed.value
      const next = currentPosition.value + increment

      if (next >= 1) {
        currentPosition.value = 1
        pause()
        return
      }
      currentPosition.value = next
    }

    lastTimestamp = timestamp
    frameId = requestAnimationFrame(tick)
  }

  function play() {
    if (isPlaying.value) return
    if (currentPosition.value >= 1) currentPosition.value = 0
    isPlaying.value = true
    lastTimestamp = null
    frameId = requestAnimationFrame(tick)
    playCallbacks.forEach(cb => cb())
  }

  function pause() {
    if (!isPlaying.value) return
    isPlaying.value = false
    if (frameId) {
      cancelAnimationFrame(frameId)
      frameId = null
    }
    lastTimestamp = null
    pauseCallbacks.forEach(cb => cb())
  }

  function togglePlay() {
    isPlaying.value ? pause() : play()
  }

  function seek(position) {
    const clamped = Math.max(0, Math.min(1, position))
    currentPosition.value = clamped
  }

  function seekToRound(round) {
    if (totalRounds.value <= 1) {
      seek(0)
      return
    }
    seek((round - 1) / (totalRounds.value - 1))
  }

  function stepForward() {
    seek(currentPosition.value + stepSize.value)
  }

  function stepBack() {
    seek(currentPosition.value - stepSize.value)
  }

  function setSpeed(multiplier) {
    if (DEFAULT_SPEEDS.includes(multiplier) || multiplier > 0) {
      playbackSpeed.value = multiplier
    }
  }

  function setMarks(newMarks) {
    marks.value = newMarks
  }

  function reset() {
    pause()
    currentPosition.value = 0
  }

  // --- Keyboard shortcuts ---
  function handleKeydown(e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
      return
    }

    switch (e.key) {
      case ' ':
        e.preventDefault()
        togglePlay()
        break
      case 'ArrowRight':
        e.preventDefault()
        stepForward()
        break
      case 'ArrowLeft':
        e.preventDefault()
        stepBack()
        break
      case '+':
      case '=': {
        e.preventDefault()
        const idx = DEFAULT_SPEEDS.indexOf(playbackSpeed.value)
        if (idx < DEFAULT_SPEEDS.length - 1) setSpeed(DEFAULT_SPEEDS[idx + 1])
        break
      }
      case '-': {
        e.preventDefault()
        const idx = DEFAULT_SPEEDS.indexOf(playbackSpeed.value)
        if (idx > 0) setSpeed(DEFAULT_SPEEDS[idx - 1])
        break
      }
    }
  }

  onMounted(() => {
    if (keyboardEnabled) {
      document.addEventListener('keydown', handleKeydown)
    }
  })

  onUnmounted(() => {
    pause()
    document.removeEventListener('keydown', handleKeydown)
    positionCallbacks.length = 0
    playCallbacks.length = 0
    pauseCallbacks.length = 0
  })

  // --- Provide/inject ---
  const context = {
    currentPosition,
    isPlaying,
    playbackSpeed,
    duration,
    marks,
    totalRounds,
    currentRound,
    stepSize,
    availableSpeeds: DEFAULT_SPEEDS,
    play,
    pause,
    togglePlay,
    seek,
    seekToRound,
    stepForward,
    stepBack,
    setSpeed,
    setMarks,
    reset,
    onPositionChange,
    onPlay,
    onPause,
  }

  provide(TIMELINE_KEY, context)

  return context
}

/**
 * Inject the timeline context in any descendant component.
 * Throws if no ancestor called useTimelineScrubber().
 */
export function useTimelineContext() {
  const context = inject(TIMELINE_KEY)
  if (!context) {
    throw new Error('useTimelineContext() requires an ancestor component that calls useTimelineScrubber()')
  }
  return context
}

export { TIMELINE_KEY, DEFAULT_SPEEDS }
