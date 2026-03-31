<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { scenariosApi } from '../api/scenarios'
import { useToast } from '../composables/useToast'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'
import WalkthroughStepCard from '../components/walkthrough/WalkthroughStepCard.vue'

const props = defineProps({ id: String })
const router = useRouter()
const toast = useToast()

const walkthrough = ref(null)
const loading = ref(true)
const error = ref(null)
const currentStep = ref(0)

const steps = computed(() => walkthrough.value?.steps || [])
const totalSteps = computed(() => steps.value.length)
const activeStep = computed(() => steps.value[currentStep.value])
const isFirstStep = computed(() => currentStep.value === 0)
const isLastStep = computed(() => currentStep.value === totalSteps.value - 1)
const progressPercent = computed(() =>
  totalSteps.value > 1 ? Math.round((currentStep.value / (totalSteps.value - 1)) * 100) : 0,
)

function nextStep() {
  if (currentStep.value < totalSteps.value - 1) currentStep.value++
}

function prevStep() {
  if (currentStep.value > 0) currentStep.value--
}

function goToStep(index) {
  if (index >= 0 && index < totalSteps.value) currentStep.value = index
}

function launchScenario() {
  router.push(`/scenarios/${props.id}`)
}

async function loadWalkthrough() {
  loading.value = true
  error.value = null
  try {
    const { data } = await scenariosApi.getWalkthrough(props.id)
    walkthrough.value = data
  } catch (e) {
    error.value = e.message || 'Failed to load walkthrough'
    toast.error('Failed to load scenario walkthrough')
  } finally {
    loading.value = false
  }
}

function onKeydown(e) {
  if (e.key === 'ArrowRight') nextStep()
  else if (e.key === 'ArrowLeft') prevStep()
}

onMounted(() => {
  loadWalkthrough()
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <LoadingSpinner v-if="loading" label="Loading walkthrough..." />

    <ErrorState
      v-else-if="error"
      title="Failed to load walkthrough"
      :message="error"
      @retry="loadWalkthrough"
    />

    <div v-else-if="walkthrough">
      <!-- Back link -->
      <router-link
        :to="`/scenarios/${id}`"
        class="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors mb-6 inline-block"
      >
        &larr; Back to scenario
      </router-link>

      <!-- Header -->
      <div class="mb-6">
        <div class="flex items-center gap-2 mb-2">
          <span class="px-2 py-0.5 text-[10px] uppercase tracking-wider font-semibold rounded bg-[rgba(32,104,255,0.1)] text-[#2068FF]">
            Guided Tour
          </span>
          <span class="text-xs text-[var(--color-text-muted)]">
            Step {{ currentStep + 1 }} of {{ totalSteps }}
          </span>
        </div>
        <h1 class="text-2xl md:text-3xl font-semibold text-[var(--color-text)]">
          {{ walkthrough.scenario_name }}
        </h1>
      </div>

      <!-- Progress bar -->
      <div class="mb-8">
        <div class="h-1 bg-[var(--color-tint)] rounded-full overflow-hidden">
          <div
            class="h-full bg-[#2068FF] rounded-full transition-all duration-500 ease-out"
            :style="{ width: `${progressPercent}%` }"
          />
        </div>

        <!-- Step dots -->
        <div class="flex justify-between mt-3">
          <button
            v-for="(step, i) in steps"
            :key="step.key"
            @click="goToStep(i)"
            class="flex items-center gap-1.5 group cursor-pointer"
          >
            <span
              class="w-2.5 h-2.5 rounded-full transition-all duration-300"
              :class="i === currentStep
                ? 'bg-[#2068FF] scale-125'
                : i < currentStep
                  ? 'bg-[#2068FF]/40'
                  : 'bg-[var(--color-border)]'"
            />
            <span
              class="text-[10px] hidden md:inline transition-colors"
              :class="i === currentStep
                ? 'text-[#2068FF] font-medium'
                : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-text-secondary)]'"
            >
              {{ step.title }}
            </span>
          </button>
        </div>
      </div>

      <!-- Active step card -->
      <Transition name="step" mode="out-in">
        <WalkthroughStepCard
          :key="activeStep.key"
          :step="activeStep"
          :is-active="true"
        />
      </Transition>

      <!-- Navigation -->
      <div class="flex items-center justify-between mt-6 gap-3">
        <button
          @click="prevStep"
          :disabled="isFirstStep"
          class="px-4 py-2.5 text-sm font-medium rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          &larr; Previous
        </button>

        <div class="flex gap-2">
          <!-- Skip to builder -->
          <button
            @click="launchScenario"
            class="px-4 py-2.5 text-sm font-medium rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors"
          >
            Skip to Builder
          </button>

          <!-- Next / Launch -->
          <button
            v-if="!isLastStep"
            @click="nextStep"
            class="px-5 py-2.5 text-sm font-semibold rounded-lg bg-[#2068FF] hover:bg-[#1a5ae0] text-white transition-colors"
          >
            Next &rarr;
          </button>
          <button
            v-else
            @click="launchScenario"
            class="px-5 py-2.5 text-sm font-semibold rounded-lg bg-[#2068FF] hover:bg-[#1a5ae0] text-white transition-colors"
          >
            Open Scenario Builder &rarr;
          </button>
        </div>
      </div>

      <!-- Keyboard hint -->
      <p class="text-center text-[10px] text-[var(--color-text-muted)] mt-4">
        Use <kbd class="px-1.5 py-0.5 rounded border border-[var(--color-border)] bg-[var(--color-tint)] text-[var(--color-text-secondary)] font-mono">&larr;</kbd>
        <kbd class="px-1.5 py-0.5 rounded border border-[var(--color-border)] bg-[var(--color-tint)] text-[var(--color-text-secondary)] font-mono">&rarr;</kbd>
        arrow keys to navigate
      </p>
    </div>

    <div v-else class="text-center py-20">
      <p class="text-[var(--color-text-muted)]">Walkthrough not found</p>
      <router-link to="/scenarios" class="text-[var(--color-primary)] text-sm mt-2 inline-block hover:underline">Back to Scenarios</router-link>
    </div>
  </div>
</template>

<style scoped>
.step-enter-active,
.step-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.step-enter-from {
  opacity: 0;
  transform: translateX(16px);
}
.step-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}
</style>
