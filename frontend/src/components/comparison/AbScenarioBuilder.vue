<script setup>
import { ref } from 'vue'
import { useSimulationStore } from '../../stores/simulation'

const store = useSimulationStore()

const variable = ref('provider')
const variantA = ref('')
const variantB = ref('')

const variables = [
  { value: 'provider', label: 'LLM Provider', optionsA: ['anthropic', 'openai', 'gemini'], optionsB: ['anthropic', 'openai', 'gemini'] },
  { value: 'agents', label: 'Agent Count', optionsA: ['10', '15', '20', '25'], optionsB: ['10', '15', '20', '25'] },
  { value: 'rounds', label: 'Round Count', optionsA: ['24', '48', '72', '144'], optionsB: ['24', '48', '72', '144'] },
  { value: 'platform', label: 'Platform Mode', optionsA: ['twitter', 'reddit', 'parallel'], optionsB: ['twitter', 'reddit', 'parallel'] },
]

const selectedVar = ref(variables[0])

function selectVariable(v) {
  const found = variables.find(x => x.value === v)
  if (found) {
    selectedVar.value = found
    variable.value = v
    variantA.value = ''
    variantB.value = ''
  }
}
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5 space-y-5">
    <div>
      <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">A/B Test Builder</h3>
      <p class="text-xs text-[var(--color-text-muted)]">
        Run two simulations with a single variable changed to compare outcomes.
      </p>
    </div>

    <!-- Variable selector -->
    <div>
      <label class="text-xs font-medium text-[var(--color-text-secondary)] mb-1.5 block">Variable to test</label>
      <select
        :value="variable"
        @change="selectVariable($event.target.value)"
        class="w-full text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
      >
        <option v-for="v in variables" :key="v.value" :value="v.value">{{ v.label }}</option>
      </select>
    </div>

    <!-- Variant A -->
    <div>
      <label class="flex items-center gap-1.5 text-xs font-medium mb-1.5">
        <span class="w-2 h-2 rounded-full bg-[#2068FF]" />
        <span class="text-[#2068FF]">Variant A</span>
      </label>
      <select
        v-model="variantA"
        class="w-full text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
      >
        <option value="" disabled>Select...</option>
        <option v-for="opt in selectedVar.optionsA" :key="opt" :value="opt">{{ opt }}</option>
      </select>
    </div>

    <!-- Variant B -->
    <div>
      <label class="flex items-center gap-1.5 text-xs font-medium mb-1.5">
        <span class="w-2 h-2 rounded-full bg-[#ff5600]" />
        <span class="text-[#ff5600]">Variant B</span>
      </label>
      <select
        v-model="variantB"
        class="w-full text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
      >
        <option value="" disabled>Select...</option>
        <option v-for="opt in selectedVar.optionsB" :key="opt" :value="opt">{{ opt }}</option>
      </select>
    </div>

    <!-- Run button -->
    <button
      :disabled="!variantA || !variantB || variantA === variantB"
      class="w-full flex items-center justify-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
      </svg>
      Run A/B Test
    </button>

    <p v-if="variantA && variantB && variantA === variantB" class="text-xs text-[var(--color-warning, #f59e0b)]">
      Variants must be different to run a meaningful comparison.
    </p>

    <!-- Previous runs hint -->
    <div v-if="store.hasRuns" class="border-t border-[var(--color-border)] pt-4">
      <p class="text-xs text-[var(--color-text-muted)]">
        Or compare existing simulations using the dropdowns above.
      </p>
    </div>
  </div>
</template>
