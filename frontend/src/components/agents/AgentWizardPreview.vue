<script setup>
import { ref, computed, onMounted } from 'vue'
import { agentsApi } from '../../api/agents'
import { useToast } from '../../composables/useToast'
import AppButton from '../common/AppButton.vue'
import AppBadge from '../common/AppBadge.vue'
import AppCard from '../common/AppCard.vue'

const props = defineProps({
  formData: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['edit', 'save', 'save-and-add'])

const toast = useToast()

const saving = ref(false)
const saveSuccess = ref(false)
const savedAgent = ref(null)
const sampleResponse = ref('')
const loadingResponse = ref(false)

const basic = computed(() => props.formData.basic || {})
const personality = computed(() => props.formData.personality || {})
const expertise = computed(() => props.formData.expertise || {})

const initial = computed(() => (basic.value.name || '?')[0].toUpperCase())

const personalityTraits = computed(() => [
  { key: 'analytical', label: 'Analytical', value: personality.value.analytical ?? 50, color: '#2068FF' },
  { key: 'creative', label: 'Creative', value: personality.value.creative ?? 50, color: '#8B5CF6' },
  { key: 'assertive', label: 'Assertive', value: personality.value.assertive ?? 50, color: '#ff5600' },
  { key: 'empathetic', label: 'Empathetic', value: personality.value.empathetic ?? 50, color: '#10B981' },
  { key: 'riskTolerant', label: 'Risk Tolerant', value: personality.value.riskTolerant ?? 50, color: '#F59E0B' },
])

const communicationStyles = {
  analytical: 'Analytical — data-driven, detail-oriented',
  executive: 'Executive — concise, outcome-focused',
  collaborative: 'Collaborative — consensus-building, inclusive',
  creative: 'Creative — innovative, exploratory',
  balanced: 'Balanced — adaptable, context-aware',
}

const communicationStyleLabel = computed(() => {
  const style = personality.value.communicationStyle || 'balanced'
  return communicationStyles[style] || style
})

function generateFallbackResponse() {
  const role = basic.value.role || 'Stakeholder'
  const analytical = personality.value.analytical ?? 50
  const creative = personality.value.creative ?? 50
  const assertive = personality.value.assertive ?? 50
  const riskTolerant = personality.value.riskTolerant ?? 50

  if (analytical > 70) {
    return `As ${role}, I'd need to see concrete metrics before committing. Show me the ROI data, integration benchmarks, and a comparison against our current stack.`
  }
  if (creative > 70) {
    return `Interesting approach — I can see some creative applications for our team. I'd love to explore how we could customize this beyond the standard use cases.`
  }
  if (assertive > 70) {
    return `Let's cut to the chase — what makes this different from the dozen other tools I've evaluated? I need clear differentiation and a pilot timeline within 2 weeks.`
  }
  if (riskTolerant > 70) {
    return `I'm intrigued. Our team has been looking for something like this. Let's set up a pilot — I'm willing to test this in production with a small segment.`
  }
  return `This looks promising, but I'd want to involve the broader team in the evaluation. Can you provide case studies from companies similar to ours and arrange a demo for my colleagues?`
}

async function generateSampleResponse() {
  loadingResponse.value = true
  try {
    const { data } = await agentsApi.previewResponse(props.formData)
    sampleResponse.value = data.response
  } catch {
    sampleResponse.value = generateFallbackResponse()
  } finally {
    loadingResponse.value = false
  }
}

async function handleSave(addToSimulation = false) {
  saving.value = true
  try {
    const { data } = await agentsApi.create(props.formData)
    savedAgent.value = data.agent
    saveSuccess.value = true
    toast.success('Agent created successfully')
    if (addToSimulation) {
      emit('save-and-add', data.agent)
    } else {
      emit('save', data.agent)
    }
  } catch (err) {
    toast.error(err.message || 'Failed to create agent')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  generateSampleResponse()
})
</script>

<template>
  <!-- Success state -->
  <div v-if="saveSuccess" class="text-center py-12">
    <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-100 mb-6 animate-success-pop">
      <svg class="w-10 h-10 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" class="animate-check-draw" />
      </svg>
    </div>
    <h2 class="text-xl font-semibold text-[var(--color-text)] mb-2">Agent Created</h2>
    <p class="text-sm text-[var(--color-text-muted)] mb-1">
      <span class="font-medium text-[var(--color-text)]">{{ savedAgent?.basic?.name }}</span>
      is ready to participate in simulations.
    </p>
    <p class="text-xs text-[var(--color-text-muted)]">
      {{ savedAgent?.basic?.role }}
      <span v-if="savedAgent?.basic?.department"> · {{ savedAgent.basic.department }}</span>
    </p>
  </div>

  <!-- Preview state -->
  <div v-else class="space-y-6">
    <!-- Agent persona card -->
    <AppCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-sm font-semibold text-[var(--color-text)]">Agent Profile</span>
          <button
            class="text-xs text-[var(--color-primary)] hover:underline cursor-pointer"
            @click="emit('edit', 0)"
          >
            Edit
          </button>
        </div>
      </template>

      <div class="flex items-start gap-4">
        <div
          class="w-14 h-14 rounded-full bg-[var(--color-primary)] text-white flex items-center justify-center text-xl font-semibold shrink-0"
        >
          {{ initial }}
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-lg font-semibold text-[var(--color-text)]">{{ basic.name || 'Unnamed Agent' }}</h3>
          <p class="text-sm text-[var(--color-text-muted)]">
            {{ basic.role || 'No role specified' }}
            <span v-if="basic.department" class="text-[var(--color-text-muted)]"> · {{ basic.department }}</span>
          </p>
          <p v-if="basic.backstory" class="text-sm text-[var(--color-text-secondary)] mt-2 leading-relaxed">
            {{ basic.backstory }}
          </p>
        </div>
      </div>
    </AppCard>

    <!-- Personality traits -->
    <AppCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-sm font-semibold text-[var(--color-text)]">Personality</span>
          <button
            class="text-xs text-[var(--color-primary)] hover:underline cursor-pointer"
            @click="emit('edit', 1)"
          >
            Edit
          </button>
        </div>
      </template>

      <div class="space-y-3">
        <div v-for="trait in personalityTraits" :key="trait.key" class="flex items-center gap-3">
          <span class="text-sm text-[var(--color-text-secondary)] w-28 shrink-0">{{ trait.label }}</span>
          <div class="flex-1 h-2 bg-black/5 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :style="{ width: trait.value + '%', backgroundColor: trait.color }"
            />
          </div>
          <span class="text-xs font-medium text-[var(--color-text-muted)] w-8 text-right">{{ trait.value }}</span>
        </div>
      </div>

      <div class="mt-4 pt-4 border-t border-[var(--color-border)]">
        <span class="text-xs text-[var(--color-text-muted)]">Communication Style</span>
        <p class="text-sm text-[var(--color-text)] mt-0.5">{{ communicationStyleLabel }}</p>
      </div>
    </AppCard>

    <!-- Expertise -->
    <AppCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-sm font-semibold text-[var(--color-text)]">Expertise</span>
          <button
            class="text-xs text-[var(--color-primary)] hover:underline cursor-pointer"
            @click="emit('edit', 2)"
          >
            Edit
          </button>
        </div>
      </template>

      <div class="space-y-4">
        <!-- Tags -->
        <div v-if="expertise.tags?.length">
          <span class="text-xs text-[var(--color-text-muted)] block mb-2">Expertise Areas</span>
          <div class="flex flex-wrap gap-1.5">
            <AppBadge v-for="tag in expertise.tags" :key="tag" variant="primary">{{ tag }}</AppBadge>
          </div>
        </div>

        <!-- Biases -->
        <div v-if="expertise.biases?.length">
          <span class="text-xs text-[var(--color-text-muted)] block mb-2">Known Biases</span>
          <div class="flex flex-wrap gap-1.5">
            <AppBadge v-for="bias in expertise.biases" :key="bias" variant="warning">{{ bias }}</AppBadge>
          </div>
        </div>

        <!-- Goals -->
        <div v-if="expertise.goals?.length">
          <span class="text-xs text-[var(--color-text-muted)] block mb-2">Goals</span>
          <div class="flex flex-wrap gap-1.5">
            <AppBadge v-for="goal in expertise.goals" :key="goal" variant="success">{{ goal }}</AppBadge>
          </div>
        </div>

        <p
          v-if="!expertise.tags?.length && !expertise.biases?.length && !expertise.goals?.length"
          class="text-sm text-[var(--color-text-muted)] italic"
        >
          No expertise configured
        </p>
      </div>
    </AppCard>

    <!-- Sample interaction preview -->
    <AppCard>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-sm font-semibold text-[var(--color-text)]">Sample Interaction</span>
          <button
            v-if="!loadingResponse"
            class="text-xs text-[var(--color-primary)] hover:underline cursor-pointer"
            @click="generateSampleResponse"
          >
            Regenerate
          </button>
        </div>
      </template>

      <p class="text-xs text-[var(--color-text-muted)] mb-3">
        Here's how this agent might respond to a typical scenario:
      </p>

      <!-- Scenario prompt -->
      <div class="bg-[var(--color-primary-light)] rounded-lg px-4 py-3 mb-3">
        <p class="text-xs font-medium text-[var(--color-primary)] mb-1">Scenario</p>
        <p class="text-sm text-[var(--color-text)]">
          A vendor is pitching a new AI-powered customer support platform to your organization.
        </p>
      </div>

      <!-- Agent response -->
      <div class="bg-[var(--color-bg-alt,var(--color-surface))] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="flex items-center gap-2 mb-2">
          <div
            class="w-6 h-6 rounded-full bg-[var(--color-primary)] text-white flex items-center justify-center text-xs font-semibold"
          >
            {{ initial }}
          </div>
          <span class="text-xs font-medium text-[var(--color-text)]">{{ basic.name || 'Agent' }}</span>
        </div>

        <!-- Loading state -->
        <div v-if="loadingResponse" class="flex items-center gap-1.5 py-1">
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-bounce [animation-delay:0ms]" />
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-bounce [animation-delay:150ms]" />
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-bounce [animation-delay:300ms]" />
        </div>

        <p v-else class="text-sm text-[var(--color-text-secondary)] leading-relaxed">
          {{ sampleResponse }}
        </p>
      </div>
    </AppCard>

    <!-- Action buttons -->
    <div class="flex items-center justify-end gap-3 pt-2">
      <AppButton variant="secondary" @click="handleSave(false)" :loading="saving" :disabled="saving">
        Save Agent
      </AppButton>
      <AppButton variant="primary" @click="handleSave(true)" :loading="saving" :disabled="saving">
        Save &amp; Add to Simulation
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
@keyframes success-pop {
  0% { transform: scale(0); opacity: 0; }
  60% { transform: scale(1.15); }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes check-draw {
  0% { stroke-dashoffset: 24; }
  100% { stroke-dashoffset: 0; }
}

.animate-success-pop {
  animation: success-pop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.animate-check-draw {
  stroke-dasharray: 24;
  stroke-dashoffset: 24;
  animation: check-draw 0.4s ease-out 0.3s forwards;
}
</style>
