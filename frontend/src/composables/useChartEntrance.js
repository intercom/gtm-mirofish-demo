import { ref, onMounted, onUnmounted } from 'vue'

export function useChartEntrance(elementRef, options = {}) {
  const { threshold = 0.15, rootMargin = '0px' } = options
  const isVisible = ref(false)
  let observer = null

  onMounted(() => {
    const el = elementRef.value
    if (!el) {
      isVisible.value = true
      return
    }

    observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          isVisible.value = true
          observer.disconnect()
          observer = null
        }
      },
      { threshold, rootMargin }
    )
    observer.observe(el)
  })

  onUnmounted(() => {
    if (observer) {
      observer.disconnect()
      observer = null
    }
  })

  return { isVisible }
}
