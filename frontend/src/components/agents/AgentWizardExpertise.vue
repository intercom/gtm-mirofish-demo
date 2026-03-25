<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
    validator: (v) => 'expertise_areas' in v && 'biases' in v && 'goals' in v,
  },
})

const emit = defineEmits(['update:modelValue'])

const PRESET_EXPERTISE = [
  'Revenue Operations',
  'Pipeline Management',
  'Product Strategy',
  'Customer Retention',
  'Competitive Analysis',
  'Data Analytics',
  'Marketing Strategy',
  'Financial Planning',
  'Enterprise Sales',
  'Growth Marketing',
]

const COGNITIVE_BIASES = [
  {
    id: 'optimism',
    label: 'Optimism Bias',
    description: 'Tendency to overestimate positive outcomes.',
    effect: 'Agent will project higher win rates and faster deal cycles.',
  },
  {
    id: 'status_quo',
    label: 'Status Quo Bias',
    description: 'Preference for the current state of affairs.',
    effect: 'Agent resists new strategies and favors proven approaches.',
  },
  {
    id: 'recency',
    label: 'Recency Bias',
    description: 'Overweighting recent events over historical data.',
    effect: 'Agent reacts strongly to the latest quarter\'s numbers.',
  },
  {
    id: 'confirmation',
    label: 'Confirmation Bias',
    description: 'Seeking information that confirms existing beliefs.',
    effect: 'Agent filters data to support their initial position.',
  },
  {
    id: 'anchoring',
    label: 'Anchoring',
    description: 'Over-relying on the first piece of information encountered.',
    effect: 'Agent fixates on initial targets or price points in negotiations.',
  },
]

const MAX_EXPERTISE = 5
const MAX_GOALS = 3

const customTagInput = ref('')
const biasesExpanded = ref(false)

const selectedExpertise = computed(() => props.modelValue.expertise_areas)
const selectedBiases = computed(() => props.modelValue.biases)
const goals = computed(() => props.modelValue.goals)

const expertiseAtLimit = computed(() => selectedExpertise.value.length >= MAX_EXPERTISE)

function update(field, value) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

function toggleExpertise(tag) {
  const current = [...selectedExpertise.value]
  const idx = current.indexOf(tag)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else if (!expertiseAtLimit.value) {
    current.push(tag)
  }
  update('expertise_areas', current)
}

function addCustomTag() {
  const tag = customTagInput.value.trim()
  if (!tag) return
  if (selectedExpertise.value.includes(tag)) {
    customTagInput.value = ''
    return
  }
  if (expertiseAtLimit.value) return
  update('expertise_areas', [...selectedExpertise.value, tag])
  customTagInput.value = ''
}

function removeExpertise(tag) {
  update('expertise_areas', selectedExpertise.value.filter((t) => t !== tag))
}

function toggleBias(biasId) {
  const current = [...selectedBiases.value]
  const idx = current.indexOf(biasId)
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    current.push(biasId)
  }
  update('biases', current)
}

function updateGoal(index, value) {
  const updated = [...goals.value]
  updated[index] = value
  update('goals', updated)
}

function addGoal() {
  if (goals.value.length >= MAX_GOALS) return
  update('goals', [...goals.value, ''])
}

function removeGoal(index) {
  const updated = [...goals.value]
  updated.splice(index, 1)
  update('goals', updated)
}
</script>

<template>
  <div class="space-y-8">
    <!-- Expertise Areas -->
    <section>
      <div class="flex items-baseline justify-between mb-1.5">
        <label class="block text-xs font-semibold text-[--color-text]">Expertise Areas</label>
        <span
          class="text-xs"
          :class="expertiseAtLimit ? 'text-[--color-fin-orange]' : 'text-[--color-text-muted]'"
        >
          {{ selectedExpertise.length }}/{{ MAX_EXPERTISE }}
        </span>
      </div>
      <p class="text-xs text-[--color-text-muted] mb-3">
        Select up to {{ MAX_EXPERTISE }} areas of expertise that define this agent's knowledge.
      </p>

      <!-- Selected tags -->
      <div v-if="selectedExpertise.length" class="flex flex-wrap gap-2 mb-3">
        <span
          v-for="tag in selectedExpertise"
          :key="tag"
          class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium bg-[--color-primary-light] text-[--color-primary]"
        >
          {{ tag }}
          <button
            type="button"
            class="ml-0.5 hover:text-[--color-primary-hover] cursor-pointer"
            @click="removeExpertise(tag)"
          >
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </span>
      </div>

      <!-- Preset chips -->
      <div class="flex flex-wrap gap-1.5 mb-3">
        <button
          v-for="tag in PRESET_EXPERTISE"
          :key="tag"
          type="button"
          :disabled="expertiseAtLimit && !selectedExpertise.includes(tag)"
          :class="[
            'rounded-full px-2.5 py-1 text-xs font-medium border transition-colors cursor-pointer',
            selectedExpertise.includes(tag)
              ? 'bg-[--color-primary] text-white border-[--color-primary]'
              : 'bg-[--color-surface] text-[--color-text-secondary] border-[--color-border] hover:border-[--color-primary] hover:text-[--color-primary]',
            expertiseAtLimit && !selectedExpertise.includes(tag) && 'opacity-40 cursor-not-allowed',
          ]"
          @click="toggleExpertise(tag)"
        >
          {{ tag }}
        </button>
      </div>

      <!-- Custom tag input -->
      <div class="flex gap-2">
        <input
          v-model="customTagInput"
          type="text"
          placeholder="Add custom expertise..."
          :disabled="expertiseAtLimit"
          class="flex-1 bg-[--color-surface] border border-[--color-border] rounded-lg px-3 py-2 text-sm text-[--color-text] placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-primary] focus:ring-1 focus:ring-[--color-primary] transition-colors disabled:opacity-40"
          @keydown.enter.prevent="addCustomTag"
        />
        <button
          type="button"
          :disabled="expertiseAtLimit || !customTagInput.trim()"
          class="px-3 py-2 text-xs font-semibold rounded-lg bg-[--color-primary] text-white hover:bg-[--color-primary-hover] transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          @click="addCustomTag"
        >
          Add
        </button>
      </div>
    </section>

    <!-- Goals -->
    <section>
      <div class="flex items-baseline justify-between mb-1.5">
        <label class="block text-xs font-semibold text-[--color-text]">Goals</label>
        <span class="text-xs text-[--color-text-muted]">{{ goals.length }}/{{ MAX_GOALS }}</span>
      </div>
      <p class="text-xs text-[--color-text-muted] mb-3">
        Define 1–{{ MAX_GOALS }} goals that drive this agent's behavior in simulations.
      </p>

      <div class="space-y-2">
        <div v-for="(goal, i) in goals" :key="i" class="flex gap-2">
          <input
            :value="goal"
            type="text"
            :placeholder="`Goal ${i + 1}, e.g. 'Maximize pipeline conversion rate'`"
            class="flex-1 bg-[--color-surface] border border-[--color-border] rounded-lg px-3 py-2 text-sm text-[--color-text] placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-primary] focus:ring-1 focus:ring-[--color-primary] transition-colors"
            @input="updateGoal(i, $event.target.value)"
          />
          <button
            v-if="goals.length > 1"
            type="button"
            class="px-2 text-[--color-text-muted] hover:text-[--color-error] transition-colors cursor-pointer"
            @click="removeGoal(i)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      <button
        v-if="goals.length < MAX_GOALS"
        type="button"
        class="mt-2 text-xs font-medium text-[--color-primary] hover:text-[--color-primary-hover] transition-colors cursor-pointer"
        @click="addGoal"
      >
        + Add goal
      </button>
    </section>

    <!-- Cognitive Biases (collapsible) -->
    <section class="border border-[--color-border] rounded-lg overflow-hidden">
      <button
        type="button"
        class="w-full flex items-center justify-between px-4 py-3 bg-[--color-surface] hover:bg-[--color-bg] transition-colors cursor-pointer"
        @click="biasesExpanded = !biasesExpanded"
      >
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold text-[--color-text]">Cognitive Biases</span>
          <span class="text-xs text-[--color-text-muted]">Optional</span>
          <span
            v-if="selectedBiases.length"
            class="inline-flex items-center justify-center w-4.5 h-4.5 rounded-full bg-[--color-primary] text-white text-[10px] font-bold leading-none px-1.5 py-0.5"
          >
            {{ selectedBiases.length }}
          </span>
        </div>
        <svg
          class="w-4 h-4 text-[--color-text-muted] transition-transform"
          :class="biasesExpanded && 'rotate-180'"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <div v-if="biasesExpanded" class="px-4 pb-4">
        <p class="text-xs text-[--color-text-muted] mb-3 mt-1">
          Select cognitive biases that influence how this agent processes information and makes decisions.
        </p>

        <div class="space-y-3">
          <label
            v-for="bias in COGNITIVE_BIASES"
            :key="bias.id"
            class="flex gap-3 p-3 rounded-lg border transition-colors cursor-pointer"
            :class="selectedBiases.includes(bias.id)
              ? 'border-[--color-primary-border] bg-[--color-primary-lighter]'
              : 'border-[--color-border] hover:border-[--color-border-strong]'"
          >
            <input
              type="checkbox"
              :checked="selectedBiases.includes(bias.id)"
              class="mt-0.5 accent-[--color-primary]"
              @change="toggleBias(bias.id)"
            />
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-[--color-text]">{{ bias.label }}</div>
              <div class="text-xs text-[--color-text-secondary] mt-0.5">{{ bias.description }}</div>
              <div class="text-xs text-[--color-text-muted] mt-1 italic">{{ bias.effect }}</div>
            </div>
          </label>
        </div>
      </div>
    </section>
  </div>
</template>
