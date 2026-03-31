<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTutorialStore } from '../../stores/tutorial'

const router = useRouter()
const tutorial = useTutorialStore()

const difficultyColor = computed(() => {
  const d = tutorial.activeTutorial?.difficulty
  if (d === 'beginner') return '#22c55e'
  if (d === 'intermediate') return '#f59e0b'
  return '#ef4444'
})

function handleAction() {
  const action = tutorial.activeStep?.action
  if (action?.type === 'navigate' && action.route) {
    router.push(action.route)
  }
  tutorial.interactiveNext()
}
</script>

<template>
  <Teleport to="body">
    <Transition name="itutorial-slide">
      <div v-if="tutorial.isInteractiveTutorialActive && tutorial.activeTutorial" class="itutorial-panel">
        <!-- Header -->
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-2.5">
            <div class="w-7 h-7 rounded-lg bg-[#2068FF]/10 flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2068FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </svg>
            </div>
            <div>
              <h3 class="text-sm font-bold text-[var(--color-text)] leading-tight">
                {{ tutorial.activeTutorial.title }}
              </h3>
              <span
                class="text-[10px] font-semibold uppercase tracking-wider"
                :style="{ color: difficultyColor }"
              >
                {{ tutorial.activeTutorial.difficulty }}
              </span>
            </div>
          </div>
          <button
            class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer px-2 py-1 rounded-md hover:bg-[var(--color-border)]"
            @click="tutorial.exitInteractiveTutorial()"
          >
            Exit
          </button>
        </div>

        <!-- Progress bar -->
        <div class="flex items-center gap-2 mb-4">
          <div class="flex-1 h-1.5 bg-[var(--color-border)] rounded-full overflow-hidden">
            <div
              class="h-full bg-[#2068FF] rounded-full transition-all duration-500"
              :style="{ width: `${tutorial.activeProgressPercent}%` }"
            />
          </div>
          <span class="text-xs text-[var(--color-text-muted)] whitespace-nowrap font-medium">
            {{ tutorial.activeStepIndex + 1 }}/{{ tutorial.activeTotalSteps }}
          </span>
        </div>

        <!-- Step content -->
        <div v-if="tutorial.activeStep" class="mb-4">
          <div class="flex items-center gap-2 mb-2">
            <span class="flex items-center justify-center w-5 h-5 rounded-full bg-[#2068FF] text-white text-[10px] font-bold">
              {{ tutorial.activeStepIndex + 1 }}
            </span>
            <h4 class="text-sm font-bold text-[var(--color-text)]">
              {{ tutorial.activeStep.title }}
            </h4>
          </div>
          <p class="text-sm text-[var(--color-text-muted)] leading-relaxed pl-7">
            {{ tutorial.activeStep.content }}
          </p>

          <!-- Action hint -->
          <div
            v-if="tutorial.activeStep.action"
            class="mt-3 ml-7 flex items-center gap-1.5 text-xs text-[#2068FF]"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
            <span v-if="tutorial.activeStep.action.type === 'navigate'">
              This step will navigate to <strong>{{ tutorial.activeStep.action.route }}</strong>
            </span>
            <span v-else-if="tutorial.activeStep.action.type === 'click'">
              Interactive action step
            </span>
          </div>
        </div>

        <!-- Navigation -->
        <div class="flex items-center justify-between pt-3 border-t border-[var(--color-border)]">
          <button
            v-if="!tutorial.activeIsFirst"
            class="px-3 py-1.5 text-xs font-semibold text-[var(--color-text-muted)] hover:text-[var(--color-text)] rounded-lg cursor-pointer transition-colors"
            @click="tutorial.interactivePrev()"
          >
            Back
          </button>
          <span v-else />

          <button
            class="px-4 py-1.5 text-xs font-semibold text-white bg-[#2068FF] hover:bg-[#1a5ae0] rounded-lg cursor-pointer transition-colors"
            @click="handleAction"
          >
            {{ tutorial.activeIsLast ? 'Complete' : tutorial.activeStep?.action ? 'Do This' : 'Next' }}
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.itutorial-panel {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 400px;
  max-width: calc(100vw - 48px);
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  z-index: 9997;
}

.itutorial-slide-enter-active,
.itutorial-slide-leave-active {
  transition: all 0.3s ease;
}
.itutorial-slide-enter-from,
.itutorial-slide-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
