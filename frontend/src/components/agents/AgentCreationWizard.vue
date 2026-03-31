<script setup>
import { ref, computed, watch } from 'vue'
import { useAgentsStore } from '../../stores/agents'
import { useToast } from '../../composables/useToast'

const props = defineProps({
  open: Boolean,
  editAgent: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'saved'])

const agentsStore = useAgentsStore()
const toast = useToast()

const STEPS = [
  { key: 'basic', label: 'Basic Info' },
  { key: 'personality', label: 'Personality' },
  { key: 'expertise', label: 'Expertise' },
  { key: 'preview', label: 'Preview & Save' },
]

const currentStep = ref(0)
const saving = ref(false)

// ── Form state ──────────────────────────────────────────────────────────────
function defaultFormData() {
  return {
    name: '',
    role: '',
    department: '',
    avatarColor: '#2068FF',
    backstory: '',
    personality: {
      analytical: 50,
      creative: 50,
      assertive: 50,
      empathetic: 50,
      riskTolerant: 50,
    },
    communicationStyle: 'professional',
    expertise: [],
    biases: [],
    goals: [],
  }
}

const formData = ref(defaultFormData())

// Populate from editAgent when provided
watch(
  () => props.editAgent,
  (agent) => {
    if (agent) {
      formData.value = { ...defaultFormData(), ...agent }
      currentStep.value = 0
    }
  },
  { immediate: true },
)

// Reset form when modal opens
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen && !props.editAgent) {
      formData.value = defaultFormData()
      currentStep.value = 0
      validationErrors.value = {}
    }
  },
)

// ── Validation ──────────────────────────────────────────────────────────────
const validationErrors = ref({})

function validateStep(stepIndex) {
  const errors = {}

  if (stepIndex === 0) {
    if (!formData.value.name.trim()) errors.name = 'Name is required'
    if (!formData.value.role.trim()) errors.role = 'Role is required'
  }

  validationErrors.value = errors
  return Object.keys(errors).length === 0
}

const canGoNext = computed(() => {
  if (currentStep.value === 0) {
    return formData.value.name.trim() && formData.value.role.trim()
  }
  return true
})

const isFirstStep = computed(() => currentStep.value === 0)
const isLastStep = computed(() => currentStep.value === STEPS.length - 1)
const currentStepKey = computed(() => STEPS[currentStep.value].key)
const progressPercent = computed(
  () => ((currentStep.value + 1) / STEPS.length) * 100,
)

const isDirty = computed(() => {
  const d = formData.value
  return !!(d.name || d.role || d.department || d.backstory || d.expertise.length || d.goals.length)
})

// ── Navigation ──────────────────────────────────────────────────────────────
function goNext() {
  if (!validateStep(currentStep.value)) return
  if (!isLastStep.value) currentStep.value++
}

function goBack() {
  if (!isFirstStep.value) currentStep.value--
}

function goToStep(index) {
  // Only allow going to steps already visited or the next valid step
  if (index <= currentStep.value) {
    currentStep.value = index
  }
}

// ── Save ────────────────────────────────────────────────────────────────────
async function save() {
  if (!validateStep(0)) {
    currentStep.value = 0
    return
  }

  saving.value = true
  try {
    let result
    if (props.editAgent?.id) {
      result = await agentsStore.updateAgent(props.editAgent.id, formData.value)
    } else {
      result = await agentsStore.createAgent(formData.value)
    }

    if (result) {
      toast.success(props.editAgent ? 'Agent updated' : 'Agent created')
      emit('saved', result)
      emit('close')
    } else if (agentsStore.error) {
      // API not available — save locally as fallback
      const local = agentsStore.addLocal(formData.value)
      toast.success('Agent saved locally')
      emit('saved', local)
      emit('close')
    }
  } catch {
    toast.error('Failed to save agent')
  } finally {
    saving.value = false
  }
}

// ── Cancel ──────────────────────────────────────────────────────────────────
const showCancelConfirm = ref(false)

function requestClose() {
  if (isDirty.value) {
    showCancelConfirm.value = true
  } else {
    emit('close')
  }
}

function confirmClose() {
  showCancelConfirm.value = false
  emit('close')
}

function onBackdropClick(e) {
  if (e.target === e.currentTarget) requestClose()
}

// ── Expertise & Goals helpers ───────────────────────────────────────────────
const newGoal = ref('')

function toggleExpertise(area) {
  const idx = formData.value.expertise.indexOf(area)
  if (idx !== -1) {
    formData.value.expertise.splice(idx, 1)
  } else {
    formData.value.expertise.push(area)
  }
}

function addGoal() {
  const goal = newGoal.value.trim()
  if (goal && formData.value.goals.length < 3) {
    formData.value.goals.push(goal)
    newGoal.value = ''
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="wizard">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click="onBackdropClick"
      >
        <div class="wizard-panel bg-[--color-surface] rounded-xl shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] flex flex-col overflow-hidden">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-[--color-border]">
            <div>
              <h2 class="text-lg font-semibold text-[--color-text]">
                {{ editAgent ? 'Edit Agent' : 'Create Agent' }}
              </h2>
              <p class="text-xs text-[--color-text-muted] mt-0.5">
                Step {{ currentStep + 1 }} of {{ STEPS.length }} — {{ STEPS[currentStep].label }}
              </p>
            </div>
            <button
              class="text-[--color-text-muted] hover:text-[--color-text] transition-colors cursor-pointer"
              aria-label="Close"
              @click="requestClose"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Step indicator -->
          <div class="px-6 pt-4 pb-2">
            <div class="flex items-center gap-1">
              <button
                v-for="(step, i) in STEPS"
                :key="step.key"
                class="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full transition-colors cursor-pointer"
                :class="[
                  i === currentStep
                    ? 'bg-[--color-primary] text-white'
                    : i < currentStep
                      ? 'bg-[--color-primary-light] text-[--color-primary]'
                      : 'bg-[--color-tint] text-[--color-text-muted]',
                ]"
                @click="goToStep(i)"
              >
                <span
                  class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
                  :class="[
                    i < currentStep
                      ? 'bg-[--color-primary] text-white'
                      : i === currentStep
                        ? 'bg-white/20 text-white'
                        : 'bg-[--color-border] text-[--color-text-muted]',
                  ]"
                >
                  <svg v-if="i < currentStep" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                  </svg>
                  <span v-else>{{ i + 1 }}</span>
                </span>
                <span class="hidden sm:inline">{{ step.label }}</span>
              </button>
            </div>
            <!-- Progress bar -->
            <div class="mt-3 h-1 bg-[--color-tint] rounded-full overflow-hidden">
              <div
                class="h-full bg-[--color-primary] rounded-full transition-all duration-300"
                :style="{ width: `${progressPercent}%` }"
              />
            </div>
          </div>

          <!-- Step content area -->
          <div class="flex-1 overflow-y-auto px-6 py-4">
            <!-- Step 1: Basic Info -->
            <div v-if="currentStepKey === 'basic'" class="space-y-4">
              <div>
                <label class="block text-xs font-semibold text-[--color-text] mb-1.5">Name *</label>
                <input
                  v-model="formData.name"
                  type="text"
                  placeholder="e.g. Sarah Chen"
                  class="wizard-input"
                  :class="{ 'border-red-500': validationErrors.name }"
                />
                <p v-if="validationErrors.name" class="text-xs text-red-500 mt-1">{{ validationErrors.name }}</p>
              </div>

              <div>
                <label class="block text-xs font-semibold text-[--color-text] mb-1.5">Role / Title *</label>
                <input
                  v-model="formData.role"
                  type="text"
                  placeholder="e.g. VP of Customer Success"
                  class="wizard-input"
                  :class="{ 'border-red-500': validationErrors.role }"
                />
                <p v-if="validationErrors.role" class="text-xs text-red-500 mt-1">{{ validationErrors.role }}</p>
              </div>

              <div>
                <label class="block text-xs font-semibold text-[--color-text] mb-1.5">Department</label>
                <select v-model="formData.department" class="wizard-input">
                  <option value="">Select department...</option>
                  <option v-for="dept in ['Sales', 'Marketing', 'CS', 'Product', 'Finance', 'Engineering', 'Executive']" :key="dept" :value="dept">
                    {{ dept }}
                  </option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-semibold text-[--color-text] mb-1.5">Backstory</label>
                <textarea
                  v-model="formData.backstory"
                  rows="3"
                  maxlength="500"
                  placeholder="Describe this agent's background, experience, and perspective..."
                  class="wizard-input resize-y"
                />
                <p class="text-xs text-[--color-text-muted] mt-1 text-right">
                  {{ formData.backstory.length }}/500
                </p>
              </div>
            </div>

            <!-- Step 2: Personality (placeholder for AgentWizardPersonality) -->
            <div v-else-if="currentStepKey === 'personality'" class="space-y-4">
              <p class="text-sm text-[--color-text-secondary]">
                Configure personality traits for <strong>{{ formData.name || 'this agent' }}</strong>.
              </p>
              <div v-for="(value, trait) in formData.personality" :key="trait" class="space-y-1">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-semibold text-[--color-text] capitalize">{{ trait.replace(/([A-Z])/g, ' $1').trim() }}</label>
                  <span class="text-xs text-[--color-text-muted] tabular-nums">{{ value }}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  :value="value"
                  class="w-full accent-[--color-primary]"
                  @input="formData.personality[trait] = Number($event.target.value)"
                />
              </div>

              <div>
                <label class="block text-xs font-semibold text-[--color-text] mb-1.5">Communication Style</label>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="style in ['professional', 'casual', 'analytical', 'persuasive']"
                    :key="style"
                    class="px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer"
                    :class="[
                      formData.communicationStyle === style
                        ? 'bg-[--color-primary] text-white'
                        : 'bg-[--color-tint] text-[--color-text-secondary] hover:bg-[--color-primary-light]',
                    ]"
                    @click="formData.communicationStyle = style"
                  >
                    {{ style.charAt(0).toUpperCase() + style.slice(1) }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Step 3: Expertise (placeholder for AgentWizardExpertise) -->
            <div v-else-if="currentStepKey === 'expertise'" class="space-y-4">
              <p class="text-sm text-[--color-text-secondary]">
                Define areas of expertise for <strong>{{ formData.name || 'this agent' }}</strong>.
              </p>

              <div>
                <label class="block text-xs font-semibold text-[--color-text] mb-2">Expertise Areas</label>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="area in [
                      'Revenue Operations', 'Pipeline Management', 'Product Strategy',
                      'Customer Retention', 'Competitive Analysis', 'Data Analytics',
                      'Marketing Strategy', 'Financial Planning', 'Enterprise Sales', 'Growth Marketing',
                    ]"
                    :key="area"
                    class="px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer"
                    :class="[
                      formData.expertise.includes(area)
                        ? 'bg-[--color-primary] text-white'
                        : 'bg-[--color-tint] text-[--color-text-secondary] hover:bg-[--color-primary-light]',
                    ]"
                    @click="toggleExpertise(area)"
                  >
                    {{ area }}
                  </button>
                </div>
              </div>

              <div>
                <label class="block text-xs font-semibold text-[--color-text] mb-2">Goals</label>
                <div class="flex gap-2">
                  <input
                    v-model="newGoal"
                    type="text"
                    placeholder="Add a goal..."
                    class="wizard-input flex-1"
                    @keyup.enter="addGoal"
                  />
                  <button
                    class="px-3 py-2 bg-[--color-primary] text-white text-xs font-semibold rounded-lg hover:bg-[--color-primary-hover] transition-colors cursor-pointer disabled:opacity-50"
                    :disabled="!newGoal.trim()"
                    @click="addGoal"
                  >
                    Add
                  </button>
                </div>
                <div v-if="formData.goals.length" class="mt-2 space-y-1">
                  <div
                    v-for="(goal, i) in formData.goals"
                    :key="i"
                    class="flex items-center justify-between bg-[--color-tint] rounded-lg px-3 py-2 text-xs text-[--color-text]"
                  >
                    <span>{{ goal }}</span>
                    <button
                      class="text-[--color-text-muted] hover:text-[--color-error] cursor-pointer"
                      @click="formData.goals.splice(i, 1)"
                    >
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Step 4: Preview & Save (placeholder for AgentWizardPreview) -->
            <div v-else-if="currentStepKey === 'preview'" class="space-y-4">
              <p class="text-sm text-[--color-text-secondary] mb-4">
                Review your agent before saving.
              </p>

              <!-- Preview card -->
              <div class="border border-[--color-border] rounded-lg p-4 space-y-3">
                <div class="flex items-center gap-3">
                  <div
                    class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white"
                    :style="{ backgroundColor: formData.avatarColor }"
                  >
                    {{ formData.name ? formData.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : '??' }}
                  </div>
                  <div>
                    <h3 class="text-sm font-semibold text-[--color-text]">{{ formData.name || 'Unnamed' }}</h3>
                    <p class="text-xs text-[--color-text-muted]">{{ formData.role || 'No role' }}{{ formData.department ? ` · ${formData.department}` : '' }}</p>
                  </div>
                </div>

                <div v-if="formData.backstory" class="text-xs text-[--color-text-secondary] bg-[--color-tint] rounded-md p-3">
                  {{ formData.backstory }}
                </div>

                <div class="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span class="text-[--color-text-muted]">Style:</span>
                    <span class="ml-1 text-[--color-text] capitalize">{{ formData.communicationStyle }}</span>
                  </div>
                  <div>
                    <span class="text-[--color-text-muted]">Expertise:</span>
                    <span class="ml-1 text-[--color-text]">{{ formData.expertise.length }} areas</span>
                  </div>
                  <div>
                    <span class="text-[--color-text-muted]">Goals:</span>
                    <span class="ml-1 text-[--color-text]">{{ formData.goals.length }} defined</span>
                  </div>
                </div>

                <div v-if="formData.expertise.length" class="flex flex-wrap gap-1">
                  <span
                    v-for="area in formData.expertise"
                    :key="area"
                    class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[--color-primary-light] text-[--color-primary]"
                  >
                    {{ area }}
                  </span>
                </div>
              </div>

              <!-- Edit shortcuts -->
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="(step, i) in STEPS.slice(0, -1)"
                  :key="step.key"
                  class="text-xs text-[--color-primary] hover:underline cursor-pointer"
                  @click="goToStep(i)"
                >
                  Edit {{ step.label }}
                </button>
              </div>
            </div>
          </div>

          <!-- Footer navigation -->
          <div class="flex items-center justify-between px-6 py-4 border-t border-[--color-border]">
            <button
              class="text-sm text-[--color-text-secondary] hover:text-[--color-text] transition-colors cursor-pointer"
              @click="requestClose"
            >
              Cancel
            </button>
            <div class="flex items-center gap-2">
              <button
                v-if="!isFirstStep"
                class="inline-flex items-center px-4 py-2 text-sm font-medium text-[--color-text-secondary] bg-[--color-tint] rounded-lg hover:bg-[--color-border] transition-colors cursor-pointer"
                @click="goBack"
              >
                Back
              </button>
              <button
                v-if="!isLastStep"
                :disabled="!canGoNext"
                class="inline-flex items-center px-5 py-2 text-sm font-semibold text-white bg-[--color-primary] rounded-lg hover:bg-[--color-primary-hover] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                @click="goNext"
              >
                Next
              </button>
              <button
                v-else
                :disabled="saving"
                class="inline-flex items-center px-5 py-2 text-sm font-semibold text-white bg-[--color-primary] rounded-lg hover:bg-[--color-primary-hover] transition-colors cursor-pointer disabled:opacity-50"
                @click="save"
              >
                <svg
                  v-if="saving"
                  class="animate-spin -ml-1 mr-2 h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ editAgent ? 'Save Changes' : 'Create Agent' }}
              </button>
            </div>
          </div>

          <!-- Cancel confirmation overlay -->
          <Transition name="fade">
            <div
              v-if="showCancelConfirm"
              class="absolute inset-0 z-10 flex items-center justify-center bg-black/30 rounded-xl"
            >
              <div class="bg-[--color-surface] rounded-lg shadow-lg p-6 max-w-sm mx-4 text-center">
                <p class="text-sm font-semibold text-[--color-text] mb-1">Discard changes?</p>
                <p class="text-xs text-[--color-text-muted] mb-4">You have unsaved agent data that will be lost.</p>
                <div class="flex items-center justify-center gap-2">
                  <button
                    class="px-4 py-2 text-xs font-medium text-[--color-text-secondary] bg-[--color-tint] rounded-lg hover:bg-[--color-border] transition-colors cursor-pointer"
                    @click="showCancelConfirm = false"
                  >
                    Keep Editing
                  </button>
                  <button
                    class="px-4 py-2 text-xs font-semibold text-white bg-[--color-error] rounded-lg hover:opacity-90 transition-colors cursor-pointer"
                    @click="confirmClose"
                  >
                    Discard
                  </button>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.wizard-input {
  width: 100%;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 0.5rem 0.75rem;
  font-size: var(--text-sm);
  color: var(--color-text);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.wizard-input::placeholder {
  color: var(--color-text-muted);
}

.wizard-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 1px var(--color-primary);
}

.wizard-panel {
  position: relative;
}

.wizard-enter-active,
.wizard-leave-active {
  transition: opacity var(--transition-fast);
}

.wizard-enter-from,
.wizard-leave-to {
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-fast);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
