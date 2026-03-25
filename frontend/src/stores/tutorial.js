import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { welcomeTourSteps, walkthroughSteps } from '../data/help-content'

const STORAGE_KEY = 'mirofish-tutorial'

export const useTutorialStore = defineStore('tutorial', () => {
  // --- Persisted state ---
  const hasSeenWelcome = ref(false)
  const completedTours = ref([])

  // --- Tutorial overlay state ---
  const isTourActive = ref(false)
  const currentStepIndex = ref(0)
  const tourSteps = ref([])

  // --- Walkthrough state ---
  const isWalkthroughActive = ref(false)
  const walkthroughStepIndex = ref(0)
  const walkthroughAutoAdvance = ref(false)

  // --- Shortcut quick-ref state ---
  const isShortcutRefOpen = ref(false)
  const isShortcutRefPinned = ref(false)

  // --- Computed ---
  const currentStep = computed(() => tourSteps.value[currentStepIndex.value] || null)
  const totalSteps = computed(() => tourSteps.value.length)
  const isFirstStep = computed(() => currentStepIndex.value === 0)
  const isLastStep = computed(() => currentStepIndex.value >= totalSteps.value - 1)

  const currentWalkthroughStep = computed(() => walkthroughSteps[walkthroughStepIndex.value] || null)
  const walkthroughTotalSteps = computed(() => walkthroughSteps.length)
  const walkthroughRemainingSeconds = computed(() => {
    let total = 0
    for (let i = walkthroughStepIndex.value; i < walkthroughSteps.length; i++) {
      total += walkthroughSteps[i].estimatedSeconds || 0
    }
    return total
  })

  // --- Persistence ---
  function load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const s = JSON.parse(saved)
        hasSeenWelcome.value = s.hasSeenWelcome || false
        completedTours.value = s.completedTours || []
      }
    } catch {
      // Corrupted — use defaults
    }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      hasSeenWelcome: hasSeenWelcome.value,
      completedTours: completedTours.value,
    }))
  }

  // --- Welcome tour ---
  function startWelcomeTour() {
    tourSteps.value = [...welcomeTourSteps]
    currentStepIndex.value = 0
    isTourActive.value = true
  }

  function nextStep() {
    if (currentStepIndex.value < totalSteps.value - 1) {
      currentStepIndex.value++
    } else {
      finishTour()
    }
  }

  function prevStep() {
    if (currentStepIndex.value > 0) {
      currentStepIndex.value--
    }
  }

  function skipTour() {
    finishTour()
  }

  function finishTour() {
    isTourActive.value = false
    hasSeenWelcome.value = true
    if (!completedTours.value.includes('welcome')) {
      completedTours.value.push('welcome')
    }
    save()
  }

  // --- Scenario walkthrough ---
  function startWalkthrough(autoAdvance = false) {
    walkthroughStepIndex.value = 0
    walkthroughAutoAdvance.value = autoAdvance
    isWalkthroughActive.value = true
  }

  function walkthroughNext() {
    if (walkthroughStepIndex.value < walkthroughSteps.length - 1) {
      walkthroughStepIndex.value++
    } else {
      finishWalkthrough()
    }
  }

  function walkthroughPrev() {
    if (walkthroughStepIndex.value > 0) {
      walkthroughStepIndex.value--
    }
  }

  function finishWalkthrough() {
    isWalkthroughActive.value = false
    walkthroughAutoAdvance.value = false
  }

  // --- Shortcut quick-ref ---
  function toggleShortcutRef() {
    if (isShortcutRefPinned.value) return
    isShortcutRefOpen.value = !isShortcutRefOpen.value
  }

  function pinShortcutRef() {
    isShortcutRefPinned.value = !isShortcutRefPinned.value
    if (isShortcutRefPinned.value) {
      isShortcutRefOpen.value = true
    }
  }

  function closeShortcutRef() {
    isShortcutRefOpen.value = false
    isShortcutRefPinned.value = false
  }

  // --- Auto-trigger on first visit ---
  function checkFirstVisit() {
    if (!hasSeenWelcome.value) {
      startWelcomeTour()
    }
  }

  // Load persisted state on creation
  load()

  return {
    // State
    hasSeenWelcome,
    completedTours,
    isTourActive,
    currentStepIndex,
    tourSteps,
    isWalkthroughActive,
    walkthroughStepIndex,
    walkthroughAutoAdvance,
    isShortcutRefOpen,
    isShortcutRefPinned,

    // Computed
    currentStep,
    totalSteps,
    isFirstStep,
    isLastStep,
    currentWalkthroughStep,
    walkthroughTotalSteps,
    walkthroughRemainingSeconds,

    // Actions
    startWelcomeTour,
    nextStep,
    prevStep,
    skipTour,
    finishTour,
    startWalkthrough,
    walkthroughNext,
    walkthroughPrev,
    finishWalkthrough,
    toggleShortcutRef,
    pinShortcutRef,
    closeShortcutRef,
    checkFirstVisit,
  }
})
