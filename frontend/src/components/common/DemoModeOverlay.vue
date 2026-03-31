<script setup>
import { ref, onMounted } from 'vue'
import { useDemoMode } from '../../composables/useDemoMode'

const STORAGE_KEY = 'demo-onboarding-dismissed'

const { isDemoMode } = useDemoMode()
const showModal = ref(false)
const dontShowAgain = ref(false)

onMounted(() => {
  if (isDemoMode && !localStorage.getItem(STORAGE_KEY)) {
    showModal.value = true
  }
})

function dismiss() {
  if (dontShowAgain.value) {
    localStorage.setItem(STORAGE_KEY, '1')
  }
  showModal.value = false
}
</script>

<template>
  <Teleport to="body">
    <Transition name="demo-overlay">
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
        @click.self="dismiss"
      >
        <div class="bg-[--color-surface] rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden border border-[--color-border]">
          <!-- Header -->
          <div class="px-6 pt-6 pb-4 text-center">
            <div class="w-12 h-12 mx-auto mb-4 rounded-full bg-[var(--color-warning-light)] flex items-center justify-center">
              <svg class="w-6 h-6 text-[var(--color-warning)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 class="text-lg font-semibold text-[--color-text]">Welcome to Demo Mode</h2>
            <p class="mt-2 text-sm text-[--color-text-secondary] leading-relaxed">
              You are running in demo mode. All data is simulated.
            </p>
          </div>

          <!-- Steps -->
          <div class="px-6 pb-4">
            <p class="text-xs font-semibold uppercase tracking-wider text-[--color-text-muted] mb-3">
              To enable real AI-powered features:
            </p>
            <ol class="space-y-3">
              <li class="flex gap-3 items-start">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-[--color-primary] text-white text-xs font-bold flex items-center justify-center">1</span>
                <span class="text-sm text-[--color-text-secondary]">Add your <strong class="text-[--color-text]">LLM API key</strong> in Settings</span>
              </li>
              <li class="flex gap-3 items-start">
                <span class="flex-shrink-0 w-6 h-6 rounded-full bg-[--color-primary] text-white text-xs font-bold flex items-center justify-center">2</span>
                <span class="text-sm text-[--color-text-secondary]">Add your <strong class="text-[--color-text]">Zep API key</strong> for knowledge graph features</span>
              </li>
            </ol>
          </div>

          <!-- Footer -->
          <div class="px-6 pb-6 space-y-4">
            <label class="flex items-center gap-2 cursor-pointer select-none">
              <input
                v-model="dontShowAgain"
                type="checkbox"
                class="w-4 h-4 rounded border-[--color-border] text-[--color-primary] focus:ring-[--color-primary] cursor-pointer"
              />
              <span class="text-xs text-[--color-text-muted]">Don't show again</span>
            </label>
            <button
              @click="dismiss"
              class="w-full py-2.5 rounded-lg bg-[--color-primary] text-white text-sm font-semibold hover:bg-[--color-primary-hover] active:bg-[--color-primary-active] transition-colors cursor-pointer"
            >
              Got it
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.demo-overlay-enter-active,
.demo-overlay-leave-active {
  transition: opacity var(--transition-base);
}
.demo-overlay-enter-active > div,
.demo-overlay-leave-active > div {
  transition: transform var(--transition-base), opacity var(--transition-base);
}
.demo-overlay-enter-from,
.demo-overlay-leave-to {
  opacity: 0;
}
.demo-overlay-enter-from > div {
  transform: scale(0.95) translateY(8px);
  opacity: 0;
}
.demo-overlay-leave-to > div {
  transform: scale(0.95) translateY(8px);
  opacity: 0;
}
</style>
