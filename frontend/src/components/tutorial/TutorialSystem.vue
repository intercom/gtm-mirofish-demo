<script setup>
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { useTutorialStore } from '../../stores/tutorial'

const tutorial = useTutorialStore()

const tooltipStyle = ref({})
const spotlightStyle = ref({})

function positionTooltip() {
  const step = tutorial.currentStep
  if (!step) return

  const el = document.querySelector(step.target)
  if (!el) {
    // Target not found — center the tooltip as a fallback
    tooltipStyle.value = {
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
    }
    spotlightStyle.value = { display: 'none' }
    return
  }

  const rect = el.getBoundingClientRect()
  const pad = 8

  // Spotlight cutout over the target element
  spotlightStyle.value = {
    top: `${rect.top - pad}px`,
    left: `${rect.left - pad}px`,
    width: `${rect.width + pad * 2}px`,
    height: `${rect.height + pad * 2}px`,
  }

  // Position tooltip relative to target
  const tooltipWidth = 320
  const tooltipHeight = 180
  const gap = 12
  const style = { position: 'fixed' }

  switch (step.position) {
    case 'bottom':
      style.top = `${rect.bottom + gap}px`
      style.left = `${rect.left + rect.width / 2 - tooltipWidth / 2}px`
      break
    case 'top':
      style.top = `${rect.top - tooltipHeight - gap}px`
      style.left = `${rect.left + rect.width / 2 - tooltipWidth / 2}px`
      break
    case 'left':
      style.top = `${rect.top + rect.height / 2 - tooltipHeight / 2}px`
      style.left = `${rect.left - tooltipWidth - gap}px`
      break
    case 'right':
      style.top = `${rect.top + rect.height / 2 - tooltipHeight / 2}px`
      style.left = `${rect.right + gap}px`
      break
    default:
      style.top = `${rect.bottom + gap}px`
      style.left = `${rect.left}px`
  }

  // Clamp to viewport
  const maxLeft = window.innerWidth - tooltipWidth - 16
  const parsedLeft = parseFloat(style.left)
  if (parsedLeft < 16) style.left = '16px'
  else if (parsedLeft > maxLeft) style.left = `${maxLeft}px`

  tooltipStyle.value = style
}

watch(
  () => [tutorial.isTourActive, tutorial.currentStepIndex],
  async () => {
    if (tutorial.isTourActive) {
      await nextTick()
      positionTooltip()
    }
  },
  { immediate: true },
)

// Reposition on window resize
function onResize() {
  if (tutorial.isTourActive) positionTooltip()
}
if (typeof window !== 'undefined') {
  window.addEventListener('resize', onResize)
}
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="tutorial-fade">
      <div v-if="tutorial.isTourActive" class="tutorial-overlay">
        <!-- Dimming overlay — pointer-events blocks interaction everywhere -->
        <div class="tutorial-backdrop" @click="tutorial.skipTour()" />

        <!-- Spotlight cutout — allows clicking the highlighted element -->
        <div class="tutorial-spotlight" :style="spotlightStyle" />

        <!-- Tooltip -->
        <div class="tutorial-tooltip" :style="tooltipStyle">
          <!-- Step counter -->
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-semibold text-[#2068FF]">
              Step {{ tutorial.currentStepIndex + 1 }} of {{ tutorial.totalSteps }}
            </span>
            <button
              class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer"
              @click="tutorial.skipTour()"
            >
              Skip tour
            </button>
          </div>

          <!-- Progress bar -->
          <div class="w-full h-1 bg-[var(--color-border)] rounded-full mb-3">
            <div
              class="h-full bg-[#2068FF] rounded-full transition-all duration-300"
              :style="{ width: `${((tutorial.currentStepIndex + 1) / tutorial.totalSteps) * 100}%` }"
            />
          </div>

          <!-- Content -->
          <h3 class="text-sm font-bold text-[var(--color-text)] mb-1">
            {{ tutorial.currentStep?.title }}
          </h3>
          <p class="text-sm text-[var(--color-text-muted)] mb-4 leading-relaxed">
            {{ tutorial.currentStep?.description }}
          </p>

          <!-- Navigation buttons -->
          <div class="flex items-center justify-between">
            <button
              v-if="!tutorial.isFirstStep"
              class="px-3 py-1.5 text-xs font-semibold text-[var(--color-text-muted)] hover:text-[var(--color-text)] rounded-lg cursor-pointer"
              @click="tutorial.prevStep()"
            >
              Back
            </button>
            <span v-else />

            <button
              class="px-4 py-1.5 text-xs font-semibold text-white bg-[#2068FF] hover:bg-[#1a5ae0] rounded-lg cursor-pointer transition-colors"
              @click="tutorial.nextStep()"
            >
              {{ tutorial.isLastStep ? 'Finish' : 'Next' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.tutorial-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
}

.tutorial-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  pointer-events: auto;
}

.tutorial-spotlight {
  position: fixed;
  border-radius: 8px;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
  pointer-events: none;
  z-index: 1;
  transition: all 0.3s ease;
}

.tutorial-tooltip {
  position: fixed;
  width: min(320px, calc(100vw - 2rem));
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  pointer-events: auto;
  z-index: 2;
  transition: top 0.3s ease, left 0.3s ease;
}

.tutorial-fade-enter-active,
.tutorial-fade-leave-active {
  transition: opacity 0.25s ease;
}
.tutorial-fade-enter-from,
.tutorial-fade-leave-to {
  opacity: 0;
}
</style>
