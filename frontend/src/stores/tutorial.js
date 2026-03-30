import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { welcomeTourSteps, walkthroughSteps } from '../data/help-content'
import { tutorialsApi } from '../api/tutorials'

const STORAGE_KEY = 'mirofish-tutorial'

export const useTutorialStore = defineStore('tutorial', () => {
  // --- Persisted state ---
  const hasSeenWelcome = ref(false)
  const completedTours = ref([])
  // Per-tutorial progress: { [tutorialId]: { completedSteps: string[], completedAt: string|null } }
  const tutorialProgress = ref({})

  // --- Tutorial overlay state (spotlight tour) ---
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

  // --- Interactive tutorial state (multi-track system) ---
  const catalog = ref([])
  const categories = ref([])
  const catalogLoading = ref(false)
  const activeTutorial = ref(null)
  const activeTutorialSteps = ref([])
  const activeStepIndex = ref(0)
  const isInteractiveTutorialActive = ref(false)

  // --- Computed: spotlight tour ---
  const currentStep = computed(() => tourSteps.value[currentStepIndex.value] || null)
  const totalSteps = computed(() => tourSteps.value.length)
  const isFirstStep = computed(() => currentStepIndex.value === 0)
  const isLastStep = computed(() => currentStepIndex.value >= totalSteps.value - 1)

  // --- Computed: walkthrough ---
  const currentWalkthroughStep = computed(() => walkthroughSteps[walkthroughStepIndex.value] || null)
  const walkthroughTotalSteps = computed(() => walkthroughSteps.length)
  const walkthroughRemainingSeconds = computed(() => {
    let total = 0
    for (let i = walkthroughStepIndex.value; i < walkthroughSteps.length; i++) {
      total += walkthroughSteps[i].estimatedSeconds || 0
    }
    return total
  })

  // --- Computed: interactive tutorial ---
  const activeStep = computed(() => activeTutorialSteps.value[activeStepIndex.value] || null)
  const activeTotalSteps = computed(() => activeTutorialSteps.value.length)
  const activeIsFirst = computed(() => activeStepIndex.value === 0)
  const activeIsLast = computed(() => activeStepIndex.value >= activeTotalSteps.value - 1)
  const activeProgressPercent = computed(() => {
    if (activeTotalSteps.value === 0) return 0
    return ((activeStepIndex.value + 1) / activeTotalSteps.value) * 100
  })

  // Per-tutorial completion status
  const completedTutorialIds = computed(() =>
    Object.entries(tutorialProgress.value)
      .filter(([, p]) => p.completedAt)
      .map(([id]) => id),
  )
  const overallProgress = computed(() => {
    if (catalog.value.length === 0) return 0
    return Math.round((completedTutorialIds.value.length / catalog.value.length) * 100)
  })

  // --- Persistence ---
  function load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const s = JSON.parse(saved)
        hasSeenWelcome.value = s.hasSeenWelcome || false
        completedTours.value = s.completedTours || []
        tutorialProgress.value = s.tutorialProgress || {}
      }
    } catch {
      // Corrupted — use defaults
    }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      hasSeenWelcome: hasSeenWelcome.value,
      completedTours: completedTours.value,
      tutorialProgress: tutorialProgress.value,
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

  // --- Interactive tutorial system ---
  async function fetchCatalog() {
    catalogLoading.value = true
    try {
      const { data } = await tutorialsApi.list()
      catalog.value = data.data || []
      categories.value = data.categories || []
    } catch {
      catalog.value = []
      categories.value = []
    } finally {
      catalogLoading.value = false
    }
  }

  async function startTutorial(tutorialId) {
    try {
      const { data } = await tutorialsApi.get(tutorialId)
      const tutorial = data.data
      activeTutorial.value = tutorial
      activeTutorialSteps.value = tutorial.steps || []
      activeStepIndex.value = 0
      isInteractiveTutorialActive.value = true

      // Initialize progress entry if not present
      if (!tutorialProgress.value[tutorialId]) {
        tutorialProgress.value[tutorialId] = { completedSteps: [], completedAt: null }
      }
    } catch {
      activeTutorial.value = null
      activeTutorialSteps.value = []
    }
  }

  function interactiveNext() {
    const step = activeStep.value
    const tutorialId = activeTutorial.value?.id
    if (step && tutorialId) {
      markStepCompleted(tutorialId, step.id)
    }
    if (activeStepIndex.value < activeTotalSteps.value - 1) {
      activeStepIndex.value++
    } else {
      finishInteractiveTutorial()
    }
  }

  function interactivePrev() {
    if (activeStepIndex.value > 0) {
      activeStepIndex.value--
    }
  }

  function finishInteractiveTutorial() {
    const tutorialId = activeTutorial.value?.id
    if (tutorialId) {
      const progress = tutorialProgress.value[tutorialId]
      if (progress) {
        progress.completedAt = new Date().toISOString()
      }
      if (!completedTours.value.includes(tutorialId)) {
        completedTours.value.push(tutorialId)
      }
    }
    isInteractiveTutorialActive.value = false
    activeTutorial.value = null
    activeTutorialSteps.value = []
    activeStepIndex.value = 0
    save()
  }

  function exitInteractiveTutorial() {
    isInteractiveTutorialActive.value = false
    activeTutorial.value = null
    activeTutorialSteps.value = []
    activeStepIndex.value = 0
    save()
  }

  function markStepCompleted(tutorialId, stepId) {
    if (!tutorialProgress.value[tutorialId]) {
      tutorialProgress.value[tutorialId] = { completedSteps: [], completedAt: null }
    }
    const steps = tutorialProgress.value[tutorialId].completedSteps
    if (!steps.includes(stepId)) {
      steps.push(stepId)
    }
    save()
  }

  function getTutorialProgress(tutorialId) {
    return tutorialProgress.value[tutorialId] || { completedSteps: [], completedAt: null }
  }

  function isTutorialCompleted(tutorialId) {
    return !!tutorialProgress.value[tutorialId]?.completedAt
  }

  function resetTutorialProgress(tutorialId) {
    delete tutorialProgress.value[tutorialId]
    const idx = completedTours.value.indexOf(tutorialId)
    if (idx !== -1) completedTours.value.splice(idx, 1)
    save()
  }

  function resetAllProgress() {
    tutorialProgress.value = {}
    completedTours.value = []
    hasSeenWelcome.value = false
    save()
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

    // Computed: spotlight tour
    currentStep,
    totalSteps,
    isFirstStep,
    isLastStep,
    currentWalkthroughStep,
    walkthroughTotalSteps,
    walkthroughRemainingSeconds,

    // Actions: spotlight tour
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

    // Interactive tutorial system
    catalog,
    categories,
    catalogLoading,
    activeTutorial,
    activeTutorialSteps,
    activeStepIndex,
    isInteractiveTutorialActive,
    activeStep,
    activeTotalSteps,
    activeIsFirst,
    activeIsLast,
    activeProgressPercent,
    completedTutorialIds,
    overallProgress,
    tutorialProgress,
    fetchCatalog,
    startTutorial,
    interactiveNext,
    interactivePrev,
    finishInteractiveTutorial,
    exitInteractiveTutorial,
    markStepCompleted,
    getTutorialProgress,
    isTutorialCompleted,
    resetTutorialProgress,
    resetAllProgress,
  }
})
