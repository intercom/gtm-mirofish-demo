import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'

const STORAGE_KEY = 'mirofish-onboarding-completed'

const steps = [
  {
    target: '[data-tour="hero"]',
    title: 'Welcome to MiroFish',
    body: 'Predict GTM campaign outcomes before they happen using AI swarm intelligence. Let us show you around.',
    position: 'bottom',
  },
  {
    target: '[data-tour="scenarios"]',
    title: 'Pick a Scenario',
    body: 'Choose from pre-built GTM simulations or create your own. Each scenario seeds a population of AI buyer personas.',
    position: 'top',
  },
  {
    target: '[data-tour="how-it-works"]',
    title: 'Three Simple Steps',
    body: 'Seed your campaign data, let the swarm simulate reactions, then review a predictive report — all in minutes.',
    position: 'bottom',
  },
  {
    target: '[data-tour="stats"]',
    title: 'Enterprise Scale',
    body: 'The OASIS engine supports up to 1M concurrent agents across multiple simulated social platforms.',
    position: 'bottom',
  },
]

const isActive = ref(false)
const currentIndex = ref(0)
const targetRect = ref(null)

let scrollListener = null

function isCompleted() {
  return localStorage.getItem(STORAGE_KEY) === 'true'
}

function markCompleted() {
  localStorage.setItem(STORAGE_KEY, 'true')
}

function updateTargetRect() {
  const step = steps[currentIndex.value]
  if (!step) return
  const el = document.querySelector(step.target)
  if (!el) { targetRect.value = null; return }
  const rect = el.getBoundingClientRect()
  targetRect.value = {
    top: rect.top,
    left: rect.left,
    width: rect.width,
    height: rect.height,
  }
}

function scrollToTarget() {
  const step = steps[currentIndex.value]
  if (!step) return
  const el = document.querySelector(step.target)
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

export function useOnboardingTour() {
  const currentStep = computed(() => steps[currentIndex.value] || null)
  const totalSteps = steps.length
  const isFirst = computed(() => currentIndex.value === 0)
  const isLast = computed(() => currentIndex.value === steps.length - 1)

  function start() {
    currentIndex.value = 0
    isActive.value = true
    nextTick(() => {
      scrollToTarget()
      setTimeout(updateTargetRect, 400)
    })
  }

  function next() {
    if (currentIndex.value < steps.length - 1) {
      currentIndex.value++
      nextTick(() => {
        scrollToTarget()
        setTimeout(updateTargetRect, 400)
      })
    } else {
      finish()
    }
  }

  function prev() {
    if (currentIndex.value > 0) {
      currentIndex.value--
      nextTick(() => {
        scrollToTarget()
        setTimeout(updateTargetRect, 400)
      })
    }
  }

  function finish() {
    isActive.value = false
    markCompleted()
    targetRect.value = null
  }

  function reset() {
    localStorage.removeItem(STORAGE_KEY)
  }

  function autoStart() {
    if (!isCompleted()) {
      setTimeout(start, 800)
    }
  }

  onMounted(() => {
    scrollListener = () => { if (isActive.value) updateTargetRect() }
    window.addEventListener('scroll', scrollListener, { passive: true })
    window.addEventListener('resize', scrollListener, { passive: true })
  })

  onUnmounted(() => {
    if (scrollListener) {
      window.removeEventListener('scroll', scrollListener)
      window.removeEventListener('resize', scrollListener)
    }
  })

  return {
    isActive,
    currentStep,
    currentIndex,
    totalSteps,
    isFirst,
    isLast,
    targetRect,
    start,
    next,
    prev,
    finish,
    reset,
    autoStart,
    isCompleted,
  }
}
