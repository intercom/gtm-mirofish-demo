import { ref, computed, onMounted, onUnmounted } from 'vue'

const MOBILE_BREAKPOINT = 640

// Shared singleton state so multiple chart instances don't duplicate listeners
let listenerCount = 0
const isMobile = ref(false)
const prefersReducedMotion = ref(false)
let mql = null
let motionMql = null

function onMobileChange(e) {
  isMobile.value = e.matches
}

function onMotionChange(e) {
  prefersReducedMotion.value = e.matches
}

function attachListeners() {
  if (listenerCount === 0) {
    mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`)
    isMobile.value = mql.matches
    mql.addEventListener('change', onMobileChange)

    motionMql = window.matchMedia('(prefers-reduced-motion: reduce)')
    prefersReducedMotion.value = motionMql.matches
    motionMql.addEventListener('change', onMotionChange)
  }
  listenerCount++
}

function detachListeners() {
  listenerCount--
  if (listenerCount === 0) {
    if (mql) mql.removeEventListener('change', onMobileChange)
    if (motionMql) motionMql.removeEventListener('change', onMotionChange)
    mql = null
    motionMql = null
  }
}

export function useMobileChart() {
  onMounted(attachListeners)
  onUnmounted(detachListeners)

  const shouldReduceMotion = computed(() => prefersReducedMotion.value || isMobile.value)

  const mobileMargins = computed(() =>
    isMobile.value
      ? { top: 40, right: 16, bottom: 32, left: 36 }
      : null
  )

  const animationDuration = computed(() => {
    if (prefersReducedMotion.value) return 0
    return isMobile.value ? 300 : 600
  })

  const staggerDelay = computed(() => {
    if (prefersReducedMotion.value) return 0
    return isMobile.value ? 30 : 80
  })

  const fontSize = computed(() => ({
    title: isMobile.value ? '12px' : '14px',
    subtitle: isMobile.value ? '10px' : '11px',
    label: isMobile.value ? '10px' : '12px',
    tick: isMobile.value ? '9px' : '10px',
    value: isMobile.value ? '10px' : '11px',
  }))

  const tickCount = computed(() => isMobile.value ? 3 : 5)

  const maxLabelChars = computed(() => isMobile.value ? 10 : 20)

  return {
    isMobile,
    prefersReducedMotion,
    shouldReduceMotion,
    mobileMargins,
    animationDuration,
    staggerDelay,
    fontSize,
    tickCount,
    maxLabelChars,
  }
}
