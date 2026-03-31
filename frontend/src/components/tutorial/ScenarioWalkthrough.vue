<script setup>
import { ref, watch, computed, onUnmounted } from 'vue'
import { useTutorialStore } from '../../stores/tutorial'

const tutorial = useTutorialStore()

const autoAdvanceTimer = ref(null)

const remainingFormatted = computed(() => {
  const secs = tutorial.walkthroughRemainingSeconds
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return m > 0 ? `${m}m ${s}s remaining` : `${s}s remaining`
})

const progressPercent = computed(() => {
  if (tutorial.walkthroughTotalSteps === 0) return 0
  return ((tutorial.walkthroughStepIndex + 1) / tutorial.walkthroughTotalSteps) * 100
})

function handleAction() {
  tutorial.walkthroughNext()
}

function toggleAutoAdvance() {
  tutorial.walkthroughAutoAdvance = !tutorial.walkthroughAutoAdvance
}

// Auto-advance: progress to next step after estimated time
watch(
  () => [tutorial.walkthroughAutoAdvance, tutorial.walkthroughStepIndex, tutorial.isWalkthroughActive],
  () => {
    clearTimeout(autoAdvanceTimer.value)
    if (tutorial.isWalkthroughActive && tutorial.walkthroughAutoAdvance && tutorial.currentWalkthroughStep) {
      const delay = (tutorial.currentWalkthroughStep.estimatedSeconds || 10) * 1000
      autoAdvanceTimer.value = setTimeout(() => {
        tutorial.walkthroughNext()
      }, delay)
    }
  },
  { immediate: true },
)

onUnmounted(() => {
  clearTimeout(autoAdvanceTimer.value)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="walkthrough-slide">
      <div v-if="tutorial.isWalkthroughActive" class="walkthrough-panel">
        <!-- Header -->
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 rounded-full bg-[#2068FF] flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
            </div>
            <span class="text-sm font-bold text-[var(--color-text)]">Guided Walkthrough</span>
          </div>
          <button
            class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer"
            @click="tutorial.finishWalkthrough()"
          >
            Exit
          </button>
        </div>

        <!-- Progress -->
        <div class="flex items-center gap-2 mb-3">
          <div class="flex-1 h-1.5 bg-[var(--color-border)] rounded-full overflow-hidden">
            <div
              class="h-full bg-[#2068FF] rounded-full transition-all duration-500"
              :style="{ width: `${progressPercent}%` }"
            />
          </div>
          <span class="text-xs text-[var(--color-text-muted)] whitespace-nowrap">
            {{ tutorial.walkthroughStepIndex + 1 }}/{{ tutorial.walkthroughTotalSteps }}
          </span>
        </div>

        <!-- Step content -->
        <div v-if="tutorial.currentWalkthroughStep" class="mb-4">
          <h4 class="text-sm font-bold text-[var(--color-text)] mb-1">
            {{ tutorial.currentWalkthroughStep.title }}
          </h4>
          <p class="text-sm text-[var(--color-text-muted)] leading-relaxed">
            {{ tutorial.currentWalkthroughStep.narration }}
          </p>
        </div>

        <!-- Action + controls -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <!-- Previous -->
            <button
              v-if="tutorial.walkthroughStepIndex > 0"
              class="px-3 py-1.5 text-xs font-semibold text-[var(--color-text-muted)] hover:text-[var(--color-text)] rounded-lg cursor-pointer"
              @click="tutorial.walkthroughPrev()"
            >
              Back
            </button>

            <!-- Auto-advance toggle -->
            <button
              class="flex items-center gap-1 px-2 py-1 text-xs rounded-md cursor-pointer transition-colors"
              :class="tutorial.walkthroughAutoAdvance
                ? 'bg-[#2068FF]/10 text-[#2068FF]'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
              @click="toggleAutoAdvance"
              :title="tutorial.walkthroughAutoAdvance ? 'Auto-advancing' : 'Click to auto-advance'"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <polygon v-if="!tutorial.walkthroughAutoAdvance" points="5 3 19 12 5 21 5 3" />
                <template v-else>
                  <rect x="6" y="4" width="4" height="16" />
                  <rect x="14" y="4" width="4" height="16" />
                </template>
              </svg>
              <span>Auto</span>
            </button>
          </div>

          <div class="flex items-center gap-2">
            <span class="text-xs text-[var(--color-text-muted)]">{{ remainingFormatted }}</span>

            <!-- Do This / Next button -->
            <button
              class="px-4 py-1.5 text-xs font-semibold text-white bg-[#2068FF] hover:bg-[#1a5ae0] rounded-lg cursor-pointer transition-colors"
              @click="handleAction"
            >
              {{ tutorial.currentWalkthroughStep?.actionLabel || 'Next' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.walkthrough-panel {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  width: min(480px, calc(100vw - 2rem));
  max-width: calc(100vw - 32px);
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 16px;
  padding: 16px 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  z-index: 9998;
}

.walkthrough-slide-enter-active,
.walkthrough-slide-leave-active {
  transition: all 0.3s ease;
}
.walkthrough-slide-enter-from,
.walkthrough-slide-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
</style>
