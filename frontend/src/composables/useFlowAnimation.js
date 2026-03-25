import { ref, computed, provide, inject, watch, isRef, onUnmounted } from 'vue'

const FLOW_ANIMATION_KEY = Symbol('flow-animation')

/**
 * Animation engine composable for synchronized data flow visualizations.
 * Drives multiple child animations from a single requestAnimationFrame loop.
 *
 * @param {Object} options
 * @param {number} options.duration - Total animation duration in ms (default 5000)
 * @param {boolean} options.loop - Whether to loop the animation (default false)
 * @param {boolean} options.autoPlay - Start playing immediately (default false)
 * @param {boolean} options.autoplay - Alias for autoPlay
 */
export function useFlowAnimation(options = {}) {
  const {
    duration: initialDuration = 5000,
    loop = false,
    autoPlay = false,
    autoplay = false,
  } = options

  const shouldAutoPlay = autoPlay || autoplay

  // --- State ---
  const playing = ref(false)
  const speed = ref(1)
  const currentTime = ref(0)
  const duration = ref(initialDuration)

  // --- Derived ---
  const progress = computed(() =>
    duration.value > 0 ? Math.min(currentTime.value / duration.value, 1) : 0,
  )

  // --- Internals ---
  let frameId = null
  let lastTimestamp = null
  const frameCallbacks = new Set()
  let observer = null
  let wasPlayingBeforeHidden = false

  // --- Animation loop ---
  function tick(timestamp) {
    if (!playing.value) return

    if (lastTimestamp === null) lastTimestamp = timestamp

    const delta = (timestamp - lastTimestamp) * speed.value
    lastTimestamp = timestamp

    currentTime.value = Math.min(currentTime.value + delta, duration.value)

    const frameData = {
      time: currentTime.value,
      progress: progress.value,
      delta,
      speed: speed.value,
    }

    for (const cb of frameCallbacks) {
      cb(frameData)
    }

    if (currentTime.value >= duration.value) {
      if (loop) {
        currentTime.value = 0
        lastTimestamp = null
        frameId = requestAnimationFrame(tick)
      } else {
        playing.value = false
        lastTimestamp = null
      }
      return
    }

    frameId = requestAnimationFrame(tick)
  }

  // --- Public methods ---
  function play() {
    if (playing.value) return
    if (currentTime.value >= duration.value) currentTime.value = 0
    playing.value = true
    lastTimestamp = null
    frameId = requestAnimationFrame(tick)
  }

  function pause() {
    playing.value = false
    lastTimestamp = null
    if (frameId) {
      cancelAnimationFrame(frameId)
      frameId = null
    }
  }

  function setSpeed(newSpeed) {
    speed.value = Math.max(0.5, Math.min(4, newSpeed))
  }

  function seek(time) {
    currentTime.value = Math.max(0, Math.min(time, duration.value))
    const frameData = {
      time: currentTime.value,
      progress: progress.value,
      delta: 0,
      speed: speed.value,
    }
    for (const cb of frameCallbacks) {
      cb(frameData)
    }
  }

  function onFrame(callback) {
    frameCallbacks.add(callback)
    return () => frameCallbacks.delete(callback)
  }

  // --- IntersectionObserver auto-pause ---
  function handleVisibility([entry]) {
    if (!entry.isIntersecting && playing.value) {
      wasPlayingBeforeHidden = true
      pause()
    } else if (entry.isIntersecting && wasPlayingBeforeHidden) {
      wasPlayingBeforeHidden = false
      play()
    }
  }

  function observe(elOrRef) {
    if (typeof IntersectionObserver === 'undefined') return

    if (observer) {
      observer.disconnect()
      observer = null
    }

    if (isRef(elOrRef)) {
      watch(
        elOrRef,
        (el) => {
          if (el) attachObserver(el)
        },
        { immediate: true },
      )
    } else if (elOrRef) {
      attachObserver(elOrRef)
    }
  }

  function attachObserver(el) {
    if (observer) observer.disconnect()
    observer = new IntersectionObserver(handleVisibility, { threshold: 0.1 })
    observer.observe(el)
  }

  // --- Cleanup ---
  function destroy() {
    pause()
    frameCallbacks.clear()
    if (observer) {
      observer.disconnect()
      observer = null
    }
  }

  onUnmounted(destroy)

  const api = {
    playing,
    speed,
    currentTime,
    duration,
    progress,
    play,
    pause,
    setSpeed,
    seek,
    onFrame,
    observe,
    destroy,
  }

  provide(FLOW_ANIMATION_KEY, api)

  if (shouldAutoPlay) play()

  return api
}

/**
 * Inject the animation controller from a parent useFlowAnimation() call.
 */
export function useFlowAnimationContext() {
  const ctx = inject(FLOW_ANIMATION_KEY)
  if (!ctx) {
    throw new Error(
      'useFlowAnimationContext() requires an ancestor component that calls useFlowAnimation()',
    )
  }
  return ctx
}

export function provideFlowAnimation(a) {
  provide(FLOW_ANIMATION_KEY, a)
}

export function injectFlowAnimation() {
  return inject(FLOW_ANIMATION_KEY, null)
}
