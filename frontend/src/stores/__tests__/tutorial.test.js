import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../data/help-content', () => ({
  welcomeTourSteps: [
    { id: 's1', title: 'Step 1' },
    { id: 's2', title: 'Step 2' },
    { id: 's3', title: 'Step 3' },
  ],
  walkthroughSteps: [
    { id: 'w1', title: 'Walk 1', estimatedSeconds: 30 },
    { id: 'w2', title: 'Walk 2', estimatedSeconds: 45 },
  ],
}))

import { useTutorialStore } from '../tutorial'

describe('useTutorialStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('has not seen welcome', () => {
      const store = useTutorialStore()
      expect(store.hasSeenWelcome).toBe(false)
    })

    it('has no completed tours', () => {
      const store = useTutorialStore()
      expect(store.completedTours).toEqual([])
    })

    it('tour is not active', () => {
      const store = useTutorialStore()
      expect(store.isTourActive).toBe(false)
    })

    it('walkthrough is not active', () => {
      const store = useTutorialStore()
      expect(store.isWalkthroughActive).toBe(false)
    })

    it('shortcut ref is closed and unpinned', () => {
      const store = useTutorialStore()
      expect(store.isShortcutRefOpen).toBe(false)
      expect(store.isShortcutRefPinned).toBe(false)
    })
  })

  describe('welcome tour', () => {
    it('startWelcomeTour() activates tour and sets steps', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      expect(store.isTourActive).toBe(true)
      expect(store.tourSteps).toHaveLength(3)
      expect(store.currentStepIndex).toBe(0)
      expect(store.currentStep.id).toBe('s1')
    })

    it('nextStep() advances through steps', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      store.nextStep()
      expect(store.currentStepIndex).toBe(1)
      expect(store.currentStep.id).toBe('s2')
    })

    it('prevStep() goes back', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      store.nextStep()
      store.prevStep()
      expect(store.currentStepIndex).toBe(0)
      expect(store.currentStep.id).toBe('s1')
    })

    it('prevStep() does nothing at first step', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      store.prevStep()
      expect(store.currentStepIndex).toBe(0)
    })

    it('isFirstStep computed is true at index 0', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      expect(store.isFirstStep).toBe(true)
      store.nextStep()
      expect(store.isFirstStep).toBe(false)
    })

    it('isLastStep computed is true at last index', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      expect(store.isLastStep).toBe(false)
      store.nextStep()
      store.nextStep()
      expect(store.isLastStep).toBe(true)
    })

    it('totalSteps matches the tour steps length', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      expect(store.totalSteps).toBe(3)
    })

    it('nextStep() on last step finishes the tour', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      store.nextStep()
      store.nextStep()
      store.nextStep()
      expect(store.isTourActive).toBe(false)
      expect(store.hasSeenWelcome).toBe(true)
      expect(store.completedTours).toContain('welcome')
    })

    it('finishTour() deactivates tour, marks welcome as seen, persists', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      store.finishTour()
      expect(store.isTourActive).toBe(false)
      expect(store.hasSeenWelcome).toBe(true)
      expect(store.completedTours).toContain('welcome')

      const saved = JSON.parse(localStorage.getItem('mirofish-tutorial'))
      expect(saved.hasSeenWelcome).toBe(true)
      expect(saved.completedTours).toContain('welcome')
    })

    it('finishTour() does not duplicate welcome in completedTours', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      store.finishTour()
      store.startWelcomeTour()
      store.finishTour()
      expect(store.completedTours.filter(t => t === 'welcome')).toHaveLength(1)
    })

    it('skipTour() finishes the tour', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      store.skipTour()
      expect(store.isTourActive).toBe(false)
      expect(store.hasSeenWelcome).toBe(true)
    })
  })

  describe('checkFirstVisit', () => {
    it('starts tour when welcome has not been seen', () => {
      const store = useTutorialStore()
      store.checkFirstVisit()
      expect(store.isTourActive).toBe(true)
    })

    it('does nothing when welcome has already been seen', () => {
      const store = useTutorialStore()
      store.startWelcomeTour()
      store.finishTour()
      store.checkFirstVisit()
      expect(store.isTourActive).toBe(false)
    })
  })

  describe('walkthrough', () => {
    it('startWalkthrough() activates walkthrough', () => {
      const store = useTutorialStore()
      store.startWalkthrough()
      expect(store.isWalkthroughActive).toBe(true)
      expect(store.walkthroughStepIndex).toBe(0)
      expect(store.walkthroughAutoAdvance).toBe(false)
    })

    it('startWalkthrough(true) enables auto-advance', () => {
      const store = useTutorialStore()
      store.startWalkthrough(true)
      expect(store.walkthroughAutoAdvance).toBe(true)
    })

    it('walkthroughNext() advances through steps', () => {
      const store = useTutorialStore()
      store.startWalkthrough()
      store.walkthroughNext()
      expect(store.walkthroughStepIndex).toBe(1)
      expect(store.currentWalkthroughStep.id).toBe('w2')
    })

    it('walkthroughNext() on last step finishes walkthrough', () => {
      const store = useTutorialStore()
      store.startWalkthrough()
      store.walkthroughNext()
      store.walkthroughNext()
      expect(store.isWalkthroughActive).toBe(false)
    })

    it('walkthroughPrev() goes back', () => {
      const store = useTutorialStore()
      store.startWalkthrough()
      store.walkthroughNext()
      store.walkthroughPrev()
      expect(store.walkthroughStepIndex).toBe(0)
    })

    it('walkthroughPrev() does nothing at first step', () => {
      const store = useTutorialStore()
      store.startWalkthrough()
      store.walkthroughPrev()
      expect(store.walkthroughStepIndex).toBe(0)
    })

    it('finishWalkthrough() deactivates walkthrough', () => {
      const store = useTutorialStore()
      store.startWalkthrough(true)
      store.finishWalkthrough()
      expect(store.isWalkthroughActive).toBe(false)
      expect(store.walkthroughAutoAdvance).toBe(false)
    })

    it('walkthroughTotalSteps reflects mock data', () => {
      const store = useTutorialStore()
      expect(store.walkthroughTotalSteps).toBe(2)
    })

    it('walkthroughRemainingSeconds computes from current step onward', () => {
      const store = useTutorialStore()
      store.startWalkthrough()
      expect(store.walkthroughRemainingSeconds).toBe(75)
      store.walkthroughNext()
      expect(store.walkthroughRemainingSeconds).toBe(45)
    })
  })

  describe('shortcut quick-ref', () => {
    it('toggleShortcutRef() opens and closes', () => {
      const store = useTutorialStore()
      store.toggleShortcutRef()
      expect(store.isShortcutRefOpen).toBe(true)
      store.toggleShortcutRef()
      expect(store.isShortcutRefOpen).toBe(false)
    })

    it('toggleShortcutRef() does nothing when pinned', () => {
      const store = useTutorialStore()
      store.pinShortcutRef()
      expect(store.isShortcutRefPinned).toBe(true)
      expect(store.isShortcutRefOpen).toBe(true)
      store.toggleShortcutRef()
      expect(store.isShortcutRefOpen).toBe(true)
    })

    it('pinShortcutRef() toggles pinned state and opens when pinned', () => {
      const store = useTutorialStore()
      store.pinShortcutRef()
      expect(store.isShortcutRefPinned).toBe(true)
      expect(store.isShortcutRefOpen).toBe(true)
    })

    it('pinShortcutRef() unpins on second call', () => {
      const store = useTutorialStore()
      store.pinShortcutRef()
      store.pinShortcutRef()
      expect(store.isShortcutRefPinned).toBe(false)
    })

    it('closeShortcutRef() closes and unpins', () => {
      const store = useTutorialStore()
      store.pinShortcutRef()
      store.closeShortcutRef()
      expect(store.isShortcutRefOpen).toBe(false)
      expect(store.isShortcutRefPinned).toBe(false)
    })
  })

  describe('persistence', () => {
    it('loads persisted state from localStorage', () => {
      localStorage.setItem('mirofish-tutorial', JSON.stringify({
        hasSeenWelcome: true,
        completedTours: ['welcome'],
      }))
      setActivePinia(createPinia())
      const store = useTutorialStore()
      expect(store.hasSeenWelcome).toBe(true)
      expect(store.completedTours).toEqual(['welcome'])
    })

    it('handles corrupted localStorage gracefully', () => {
      localStorage.setItem('mirofish-tutorial', '{broken')
      setActivePinia(createPinia())
      const store = useTutorialStore()
      expect(store.hasSeenWelcome).toBe(false)
      expect(store.completedTours).toEqual([])
    })

    it('handles missing fields in persisted data', () => {
      localStorage.setItem('mirofish-tutorial', JSON.stringify({}))
      setActivePinia(createPinia())
      const store = useTutorialStore()
      expect(store.hasSeenWelcome).toBe(false)
      expect(store.completedTours).toEqual([])
    })
  })
})
