import { ref, onMounted, onUnmounted } from 'vue'

const PULL_THRESHOLD = 60
const MAX_PULL = 120

export function usePullToRefresh(containerRef, onRefresh) {
  const pulling = ref(false)
  const pullDistance = ref(0)
  const refreshing = ref(false)

  let startY = 0
  let active = false

  function onTouchStart(e) {
    if (refreshing.value) return
    const el = containerRef.value
    if (!el || el.scrollTop > 0) return
    startY = e.touches[0].clientY
    active = true
  }

  function onTouchMove(e) {
    if (!active || refreshing.value) return
    const el = containerRef.value
    if (!el || el.scrollTop > 0) {
      active = false
      pullDistance.value = 0
      pulling.value = false
      return
    }
    const dy = e.touches[0].clientY - startY
    if (dy > 0) {
      pulling.value = true
      pullDistance.value = Math.min(dy * 0.5, MAX_PULL)
      if (dy > 10) e.preventDefault()
    }
  }

  function onTouchEnd() {
    if (!active) return
    active = false
    if (pullDistance.value >= PULL_THRESHOLD && !refreshing.value) {
      refreshing.value = true
      pullDistance.value = PULL_THRESHOLD
      Promise.resolve(onRefresh()).finally(() => {
        refreshing.value = false
        pullDistance.value = 0
        pulling.value = false
      })
    } else {
      pullDistance.value = 0
      pulling.value = false
    }
  }

  onMounted(() => {
    const el = containerRef.value
    if (!el) return
    el.addEventListener('touchstart', onTouchStart, { passive: true })
    el.addEventListener('touchmove', onTouchMove, { passive: false })
    el.addEventListener('touchend', onTouchEnd, { passive: true })
  })

  onUnmounted(() => {
    const el = containerRef.value
    if (!el) return
    el.removeEventListener('touchstart', onTouchStart)
    el.removeEventListener('touchmove', onTouchMove)
    el.removeEventListener('touchend', onTouchEnd)
  })

  return { pulling, pullDistance, refreshing, PULL_THRESHOLD }
}
