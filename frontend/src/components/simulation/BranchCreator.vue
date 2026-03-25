<script setup>
import { ref, computed } from 'vue'
import { AppButton, AppInput, AppBadge } from '../common'

const props = defineProps({
  simulationId: { type: String, required: true },
  totalRounds: { type: Number, default: 144 },
  currentRound: { type: Number, default: 0 },
})

const emit = defineEmits(['branch-created', 'cancel'])

const selectedRound = ref(null)
const branchLabel = ref('')
const creating = ref(false)

// Modification state
const modifications = ref([])
const modType = ref('inject_event')
const modValue = ref('')

const MODIFICATION_TYPES = [
  { value: 'inject_event', label: 'Inject event', placeholder: 'e.g., A competitor launches a product' },
  { value: 'add_agent', label: 'Add agent', placeholder: 'e.g., Finance analyst at a hedge fund' },
  { value: 'remove_agent', label: 'Remove agent', placeholder: 'e.g., Agent name or ID to remove' },
  { value: 'change_personality', label: 'Change agent personality', placeholder: 'e.g., Make the CTO agent more skeptical' },
  { value: 'change_constraint', label: 'Change constraint', placeholder: 'e.g., Limit agents to 2 posts per round' },
]

const currentModPlaceholder = computed(() =>
  MODIFICATION_TYPES.find(m => m.value === modType.value)?.placeholder || ''
)

const currentModLabel = computed(() =>
  MODIFICATION_TYPES.find(m => m.value === modType.value)?.label || ''
)

// Round markers — group into segments for display
const roundSegmentSize = computed(() => {
  if (props.totalRounds <= 24) return 1
  if (props.totalRounds <= 72) return 3
  return 6
})

const roundMarkers = computed(() => {
  const markers = []
  const maxRound = Math.max(props.currentRound, props.totalRounds)
  for (let r = 1; r <= maxRound; r += roundSegmentSize.value) {
    markers.push({
      round: r,
      label: `R${r}`,
      completed: r <= props.currentRound,
    })
  }
  return markers
})

const canAddModification = computed(() => modValue.value.trim().length > 0)

const canCreate = computed(() =>
  selectedRound.value !== null &&
  branchLabel.value.trim().length > 0 &&
  modifications.value.length > 0 &&
  !creating.value
)

const previewText = computed(() => {
  if (selectedRound.value === null) return null
  const modSummaries = modifications.value.map(m => {
    const typeLabel = MODIFICATION_TYPES.find(t => t.value === m.type)?.label || m.type
    return `${typeLabel}: ${m.value}`
  })
  const modText = modSummaries.length
    ? modSummaries.join('; ')
    : 'No modifications added yet'
  return `Branch from Round ${selectedRound.value} with ${modifications.value.length} modification${modifications.value.length !== 1 ? 's' : ''}: ${modText}`
})

function selectRound(round) {
  selectedRound.value = round
}

function addModification() {
  if (!canAddModification.value) return
  modifications.value.push({
    type: modType.value,
    value: modValue.value.trim(),
  })
  modValue.value = ''
}

function removeModification(index) {
  modifications.value.splice(index, 1)
}

async function createBranch() {
  if (!canCreate.value) return
  creating.value = true
  try {
    emit('branch-created', {
      simulationId: props.simulationId,
      at_round: selectedRound.value,
      label: branchLabel.value.trim(),
      modifications: modifications.value,
    })
  } finally {
    creating.value = false
  }
}

function resetForm() {
  selectedRound.value = null
  branchLabel.value = ''
  modifications.value = []
  modValue.value = ''
  modType.value = 'inject_event'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold text-[var(--color-text)]">Create Branch</h2>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
          Fork this simulation at any completed round with modifications
        </p>
      </div>
      <button
        class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-lg leading-none"
        @click="$emit('cancel')"
      >
        &times;
      </button>
    </div>

    <!-- Step 1: Select Round -->
    <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">
        <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-[var(--color-primary)] text-white text-xs font-bold mr-2">1</span>
        Select Branch Point
      </h3>
      <p class="text-xs text-[var(--color-text-muted)] mb-4">
        Click a round on the timeline to set where the branch diverges.
      </p>

      <!-- Timeline -->
      <div class="relative">
        <div class="overflow-x-auto pb-2">
          <div class="flex items-center gap-0.5 min-w-max px-1">
            <div
              v-for="marker in roundMarkers"
              :key="marker.round"
              class="flex flex-col items-center cursor-pointer group"
              @click="marker.completed ? selectRound(marker.round) : null"
            >
              <!-- Round dot -->
              <div
                :class="[
                  'w-4 h-4 rounded-full border-2 transition-all duration-150',
                  selectedRound === marker.round
                    ? 'bg-[var(--color-primary)] border-[var(--color-primary)] scale-125 shadow-md'
                    : marker.completed
                      ? 'bg-[var(--color-primary)]/20 border-[var(--color-primary)] group-hover:bg-[var(--color-primary)] group-hover:scale-110'
                      : 'bg-[var(--color-tint)] border-[var(--color-border)] opacity-40 cursor-not-allowed',
                ]"
              />
              <!-- Round label -->
              <span
                :class="[
                  'text-[9px] mt-1 font-medium whitespace-nowrap',
                  selectedRound === marker.round
                    ? 'text-[var(--color-primary)] font-bold'
                    : marker.completed
                      ? 'text-[var(--color-text-muted)]'
                      : 'text-[var(--color-text-muted)] opacity-40',
                ]"
              >
                {{ marker.label }}
              </span>
            </div>
          </div>
        </div>

        <!-- Selected round indicator -->
        <Transition name="fade">
          <div v-if="selectedRound !== null" class="mt-3 flex items-center gap-2">
            <AppBadge variant="primary">Round {{ selectedRound }}</AppBadge>
            <span class="text-xs text-[var(--color-text-muted)]">selected as branch point</span>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Step 2: Add Modifications -->
    <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">
        <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-[var(--color-primary)] text-white text-xs font-bold mr-2">2</span>
        Define Modifications
      </h3>
      <p class="text-xs text-[var(--color-text-muted)] mb-4">
        What changes should this branch apply? Add one or more modifications for A/B/C testing.
      </p>

      <!-- Modification input row -->
      <div class="flex flex-col sm:flex-row gap-2 mb-3">
        <div class="sm:w-48 shrink-0">
          <AppInput
            type="select"
            v-model="modType"
            :options="MODIFICATION_TYPES"
          />
        </div>
        <div class="flex-1">
          <AppInput
            v-model="modValue"
            :placeholder="currentModPlaceholder"
            @keyup.enter="addModification"
          />
        </div>
        <AppButton
          size="sm"
          :disabled="!canAddModification"
          @click="addModification"
        >
          Add
        </AppButton>
      </div>

      <!-- Modification list -->
      <div v-if="modifications.length" class="space-y-2 mt-4">
        <div
          v-for="(mod, idx) in modifications"
          :key="idx"
          class="flex items-start gap-2 bg-[var(--color-tint)] rounded-lg px-3 py-2.5"
        >
          <AppBadge :variant="mod.type === 'remove_agent' ? 'error' : mod.type === 'inject_event' ? 'warning' : 'primary'">
            {{ MODIFICATION_TYPES.find(t => t.value === mod.type)?.label || mod.type }}
          </AppBadge>
          <span class="text-sm text-[var(--color-text)] flex-1 break-words">{{ mod.value }}</span>
          <button
            class="text-[var(--color-text-muted)] hover:text-[var(--color-error)] text-sm shrink-0 mt-0.5"
            @click="removeModification(idx)"
          >
            &times;
          </button>
        </div>
      </div>

      <div v-else class="text-center py-6 text-[var(--color-text-muted)]">
        <p class="text-sm">No modifications added yet</p>
        <p class="text-xs mt-1">Add at least one modification to create a meaningful branch</p>
      </div>
    </div>

    <!-- Step 3: Branch Label -->
    <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
      <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">
        <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-[var(--color-primary)] text-white text-xs font-bold mr-2">3</span>
        Name Your Branch
      </h3>
      <AppInput
        v-model="branchLabel"
        placeholder="e.g., With finance agent added at midpoint"
      />
    </div>

    <!-- Preview -->
    <Transition name="fade">
      <div
        v-if="previewText"
        class="bg-[rgba(32,104,255,0.04)] border border-[rgba(32,104,255,0.15)] rounded-lg px-4 py-3"
      >
        <div class="flex items-start gap-2">
          <svg class="w-4 h-4 text-[var(--color-primary)] mt-0.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 3v12" /><circle cx="18" cy="6" r="3" /><circle cx="6" cy="18" r="3" /><path d="M18 9a9 9 0 01-9 9" />
          </svg>
          <p class="text-xs text-[var(--color-text-secondary)]">{{ previewText }}</p>
        </div>
      </div>
    </Transition>

    <!-- Actions -->
    <div class="flex items-center justify-between pt-2">
      <button
        class="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
        @click="resetForm"
      >
        Reset
      </button>
      <div class="flex items-center gap-3">
        <AppButton variant="ghost" @click="$emit('cancel')">
          Cancel
        </AppButton>
        <AppButton
          :disabled="!canCreate"
          :loading="creating"
          @click="createBranch"
        >
          Create Branch
        </AppButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
