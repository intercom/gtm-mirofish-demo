import { ref, onMounted, onUnmounted } from 'vue'

const MOBILE_BREAKPOINT = 640

export function useMobileChart() {
  const isMobile = ref(false)
  let mql = null

  function onchange(e) {
    isMobile.value = e.matches
  }

  onMounted(() => {
    mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`)
    isMobile.value = mql.matches
    mql.addEventListener('change', onchange)
  })

  onUnmounted(() => {
    if (mql) mql.removeEventListener('change', onchange)
  })

  return { isMobile }
}
