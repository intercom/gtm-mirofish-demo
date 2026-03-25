<script setup>
import { computed, watch, ref } from 'vue'
import { useOnboardingTour } from '../../composables/useOnboardingTour'

const {
  isActive,
  currentStep,
  currentIndex,
  totalSteps,
  isFirst,
  isLast,
  targetRect,
  next,
  prev,
  finish,
} = useOnboardingTour()

const tooltipStyle = computed(() => {
  if (!targetRect.value) return { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }

  const r = targetRect.value
  const pad = 16
  const pos = currentStep.value?.position || 'bottom'

  if (pos === 'top') {
    return {
      bottom: `${window.innerHeight - r.top + pad}px`,
      left: `${r.left + r.width / 2}px`,
      transform: 'translateX(-50%)',
    }
  }
  return {
    top: `${r.top + r.height + pad}px`,
    left: `${r.left + r.width / 2}px`,
    transform: 'translateX(-50%)',
  }
})

const spotlightStyle = computed(() => {
  if (!targetRect.value) return {}
  const r = targetRect.value
  const inset = 8
  return {
    top: `${r.top - inset}px`,
    left: `${r.left - inset}px`,
    width: `${r.width + inset * 2}px`,
    height: `${r.height + inset * 2}px`,
  }
})

const showContent = ref(false)
watch(isActive, (active) => {
  if (active) setTimeout(() => { showContent.value = true }, 100)
  else showContent.value = false
})
watch(currentIndex, () => {
  showContent.value = false
  setTimeout(() => { showContent.value = true }, 300)
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-300"
      leave-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div v-if="isActive" class="fixed inset-0 z-[10000]" @click.self="finish">
        <!-- Dark overlay with spotlight cutout -->
        <div class="absolute inset-0 bg-black/60 pointer-events-none" />

        <!-- Spotlight ring around target -->
        <div
          v-if="targetRect"
          class="absolute rounded-xl border-2 border-[#2068FF] pointer-events-none transition-all duration-400 ease-out"
          :style="spotlightStyle"
          style="box-shadow: 0 0 0 9999px rgba(0,0,0,0.6), 0 0 24px rgba(32,104,255,0.3)"
        />

        <!-- Tooltip -->
        <Transition
          enter-active-class="transition-all duration-300 ease-out"
          enter-from-class="opacity-0 translate-y-2"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition-all duration-200"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div
            v-if="showContent"
            class="absolute z-10 w-[340px] max-w-[calc(100vw-2rem)] bg-white rounded-xl shadow-2xl p-5 pointer-events-auto"
            :style="tooltipStyle"
          >
            <!-- Step indicator dots -->
            <div class="flex items-center gap-1.5 mb-3">
              <div
                v-for="i in totalSteps"
                :key="i"
                class="h-1.5 rounded-full transition-all duration-300"
                :class="i - 1 === currentIndex
                  ? 'w-5 bg-[#2068FF]'
                  : i - 1 < currentIndex
                    ? 'w-1.5 bg-[#2068FF]/40'
                    : 'w-1.5 bg-gray-200'"
              />
            </div>

            <h3 class="text-sm font-semibold text-[#1a1a1a] mb-1.5">
              {{ currentStep?.title }}
            </h3>
            <p class="text-xs text-gray-500 leading-relaxed mb-4">
              {{ currentStep?.body }}
            </p>

            <!-- Navigation -->
            <div class="flex items-center justify-between">
              <button
                @click="finish"
                class="text-xs text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
              >
                Skip tour
              </button>
              <div class="flex gap-2">
                <button
                  v-if="!isFirst"
                  @click="prev"
                  class="px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors cursor-pointer"
                >
                  Back
                </button>
                <button
                  @click="next"
                  class="px-4 py-1.5 text-xs font-medium text-white bg-[#2068FF] hover:bg-[#1a5ae0] rounded-lg transition-colors cursor-pointer"
                >
                  {{ isLast ? 'Get Started' : 'Next' }}
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
