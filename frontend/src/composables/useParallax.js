import { ref, onMounted, onUnmounted } from 'vue'

export function useParallax(containerRef) {
  const scrollY = ref(0)
  const progress = ref(0)
  let ticking = false

  function update() {
    const y = window.scrollY
    scrollY.value = y

    const el = containerRef?.value
    if (el) {
      const height = el.offsetHeight
      progress.value = height > 0 ? Math.min(y / height, 1) : 0
    }

    ticking = false
  }

  function onScroll() {
    if (!ticking) {
      requestAnimationFrame(update)
      ticking = true
    }
  }

  onMounted(() => {
    window.addEventListener('scroll', onScroll, { passive: true })
    update()
  })

  onUnmounted(() => {
    window.removeEventListener('scroll', onScroll)
  })

  return { scrollY, progress }
}
