import { ref, onMounted, onUnmounted, watch, isRef } from 'vue'

/**
 * Composable that tracks whether a template ref element is visible in the viewport.
 * Uses IntersectionObserver to defer rendering or loading of heavy content.
 *
 * @param {Ref<HTMLElement|null>} target - template ref to observe
 * @param {Object} options
 * @param {string} options.rootMargin - observer rootMargin (default '200px' to preload slightly before viewport)
 * @param {number} options.threshold - visibility threshold (default 0)
 * @param {boolean} options.once - stop observing after first intersection (default true)
 * @returns {{ isVisible: Ref<boolean> }}
 */
export function useLazyLoad(target, options = {}) {
  const { rootMargin = '200px', threshold = 0, once = true } = options
  const isVisible = ref(false)
  let observer = null

  function cleanup() {
    if (observer) {
      observer.disconnect()
      observer = null
    }
  }

  function observe(el) {
    cleanup()
    if (!el || typeof IntersectionObserver === 'undefined') {
      isVisible.value = true
      return
    }

    observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          isVisible.value = true
          if (once) cleanup()
        } else if (!once) {
          isVisible.value = false
        }
      },
      { rootMargin, threshold },
    )
    observer.observe(el)
  }

  onMounted(() => {
    const el = isRef(target) ? target.value : target
    if (el) observe(el)
  })

  if (isRef(target)) {
    watch(target, (el) => {
      if (el && !isVisible.value) observe(el)
    })
  }

  onUnmounted(cleanup)

  return { isVisible }
}
