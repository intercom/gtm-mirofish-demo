import { ref, watch, onUnmounted } from 'vue'

export function useCountUp(target, { duration = 800 } = {}) {
  const display = ref(0)
  let rafId = null

  function animate(from, to) {
    const start = performance.now()
    cancelAnimationFrame(rafId)

    function tick(now) {
      const t = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - t, 3) // ease-out cubic
      display.value = Math.round(from + (to - from) * eased)
      if (t < 1) {
        rafId = requestAnimationFrame(tick)
      }
    }

    rafId = requestAnimationFrame(tick)
  }

  watch(target, (newVal, oldVal) => {
    animate(oldVal ?? 0, newVal)
  }, { immediate: true })

  onUnmounted(() => cancelAnimationFrame(rafId))

  return display
}
