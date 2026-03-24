import { ref, watch, toValue, onUnmounted } from 'vue'

export function useCountUp(source, options = {}) {
  const { duration = 800 } = options
  const display = ref(0)
  let frameId = null

  function cancel() {
    if (frameId) {
      cancelAnimationFrame(frameId)
      frameId = null
    }
  }

  watch(
    () => toValue(source),
    (newVal) => {
      cancel()
      const target = typeof newVal === 'number' ? newVal : parseInt(newVal, 10)
      if (isNaN(target)) return

      const from = display.value
      const startTime = performance.now()

      function step(now) {
        const elapsed = now - startTime
        const progress = Math.min(elapsed / duration, 1)
        const eased = 1 - Math.pow(1 - progress, 3)
        display.value = Math.round(from + (target - from) * eased)
        if (progress < 1) {
          frameId = requestAnimationFrame(step)
        } else {
          frameId = null
        }
      }

      frameId = requestAnimationFrame(step)
    },
    { immediate: true },
  )

  onUnmounted(cancel)

  return display
}
