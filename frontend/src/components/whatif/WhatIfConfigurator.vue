<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from '../common/Card.vue'
import Button from '../common/Button.vue'
import Badge from '../common/Badge.vue'
import { useWhatifStore } from '../../stores/whatif'
import { useSimulationStore } from '../../stores/simulation'
import { useToast } from '../../composables/useToast'

const props = defineProps({
  simulationId: { type: String, default: null },
})

const router = useRouter()
const toast = useToast()
const whatifStore = useWhatifStore()
const simulationStore = useSimulationStore()

if (props.simulationId && !whatifStore.baseSimulationId) {
  whatifStore.setBaseSimulation(props.simulationId)
}

const availableSimulations = computed(() =>
  simulationStore.sessionRuns.filter((r) => r.status === 'completed'),
)

const selectedRun = computed(() =>
  simulationStore.sessionRuns.find(
    (r) => r.id === whatifStore.baseSimulationId,
  ),
)

function getParamDefault(paramDef) {
  if (!selectedRun.value) return paramDef.defaultValue
  const map = {
    agent_count: selectedRun.value.agentCount,
    rounds: selectedRun.value.totalRounds,
    duration_hours: selectedRun.value.duration,
  }
  return map[paramDef.key] ?? paramDef.defaultValue
}

function getModValue(paramKey) {
  const mod = whatifStore.modifications.find((m) => m.parameter === paramKey)
  return mod ? mod.value : null
}

function getChangeAmount(paramDef) {
  const modVal = getModValue(paramDef.key)
  if (modVal === null) return null
  const base = getParamDefault(paramDef)
  return modVal - base
}

function handleSliderInput(paramDef, event) {
  const val = Number(event.target.value)
  const base = getParamDefault(paramDef)
  if (val === base) {
    whatifStore.removeModification(paramDef.key)
  } else {
    whatifStore.addModification(paramDef.key, val)
  }
}

function nudge(paramDef, direction) {
  const current = getModValue(paramDef.key) ?? getParamDefault(paramDef)
  const next = current + paramDef.step * direction
  const clamped = Math.min(paramDef.max, Math.max(paramDef.min, next))
  const base = getParamDefault(paramDef)
  if (clamped === base) {
    whatifStore.removeModification(paramDef.key)
  } else {
    whatifStore.addModification(paramDef.key, clamped)
  }
}

async function handleRun() {
  await whatifStore.runWhatIf()
  if (whatifStore.isComplete) {
    toast.success('What-if scenario complete!')
  } else if (whatifStore.error) {
    toast.error(`What-if failed: ${whatifStore.error}`)
  }
}

function handlePreset(presetId) {
  whatifStore.applyPreset(presetId)
}

function handleReset() {
  whatifStore.clearModifications()
}
</script>

<template>
  <div class="space-y-5">
    <!-- Base Simulation Selector -->
    <Card>
      <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
        Base Simulation
      </label>
      <select
        :value="whatifStore.baseSimulationId || ''"
        @change="whatifStore.setBaseSimulation($event.target.value || null)"
        class="w-full border border-[var(--input-border)] rounded-[var(--input-radius)] px-4 py-2 text-sm bg-[var(--input-bg)] text-[var(--input-text)] focus:ring-2 focus:ring-[var(--input-ring)] focus:border-transparent outline-none"
      >
        <option value="" disabled>Select a completed simulation...</option>
        <option
          v-for="run in availableSimulations"
          :key="run.id"
          :value="run.id"
        >
          {{ run.scenarioName }} — {{ run.agentCount }} agents, {{ run.totalRounds || '?' }} rounds
        </option>
      </select>
      <p v-if="availableSimulations.length === 0" class="text-xs text-[var(--color-text-muted)] mt-2">
        No completed simulations yet. Run a simulation first.
      </p>
    </Card>

    <!-- Quick Presets -->
    <Card v-if="whatifStore.baseSimulationId">
      <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-3">
        Quick Presets
      </label>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="preset in whatifStore.presets"
          :key="preset.id"
          @click="handlePreset(preset.id)"
          class="px-3 py-1.5 text-xs rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] transition-colors"
        >
          {{ preset.icon }} {{ preset.label }}
        </button>
      </div>
    </Card>

    <!-- Parameter Modifications -->
    <Card v-if="whatifStore.baseSimulationId">
      <div class="flex items-center justify-between mb-4">
        <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
          Parameter Modifications
        </label>
        <button
          v-if="whatifStore.hasModifications"
          @click="handleReset"
          class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors"
        >
          Reset all
        </button>
      </div>

      <div class="space-y-5">
        <div
          v-for="param in whatifStore.parameterDefs"
          :key="param.key"
          class="group"
        >
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-sm font-medium text-[var(--color-text)]">
              {{ param.label }}
            </span>
            <div class="flex items-center gap-2 text-xs">
              <span class="text-[var(--color-text-muted)]">
                {{ param.format(getParamDefault(param)) }}
              </span>
              <template v-if="getModValue(param.key) !== null">
                <span class="text-[var(--color-text-muted)]">&rarr;</span>
                <span class="font-semibold text-[var(--color-primary)]">
                  {{ param.format(getModValue(param.key)) }}
                </span>
                <Badge
                  :variant="getChangeAmount(param) > 0 ? 'success' : getChangeAmount(param) < 0 ? 'error' : 'default'"
                >
                  {{ getChangeAmount(param) > 0 ? '+' : '' }}{{ param.key === 'temperature' ? getChangeAmount(param).toFixed(1) : getChangeAmount(param) }}
                </Badge>
              </template>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button
              @click="nudge(param, -1)"
              class="w-7 h-7 flex items-center justify-center rounded border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] transition-colors text-sm shrink-0"
            >
              −
            </button>

            <input
              type="range"
              :min="param.min"
              :max="param.max"
              :step="param.step"
              :value="getModValue(param.key) ?? getParamDefault(param)"
              @input="handleSliderInput(param, $event)"
              class="flex-1 accent-[var(--color-primary)]"
            />

            <button
              @click="nudge(param, 1)"
              class="w-7 h-7 flex items-center justify-center rounded border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] transition-colors text-sm shrink-0"
            >
              +
            </button>
          </div>
        </div>
      </div>

      <!-- Active Modifications Summary -->
      <div
        v-if="whatifStore.hasModifications"
        class="mt-5 pt-4 border-t border-[var(--color-border)]"
      >
        <div class="flex flex-wrap gap-2">
          <span
            v-for="mod in whatifStore.modifications"
            :key="mod.parameter"
            class="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-[var(--color-primary-light)] text-[var(--color-primary)]"
          >
            {{ whatifStore.parameterDefs.find(p => p.key === mod.parameter)?.label }}:
            {{ whatifStore.parameterDefs.find(p => p.key === mod.parameter)?.format(mod.value) }}
            <button
              @click="whatifStore.removeModification(mod.parameter)"
              class="ml-0.5 hover:text-[var(--color-primary-hover)] transition-colors"
            >
              &times;
            </button>
          </span>
        </div>
      </div>
    </Card>

    <!-- Progress -->
    <Card v-if="whatifStore.isRunning">
      <div class="space-y-3">
        <div class="flex items-center justify-between text-sm">
          <span class="text-[var(--color-text-secondary)]">{{ whatifStore.progressMessage }}</span>
          <span class="font-medium text-[var(--color-primary)]">{{ whatifStore.progress }}%</span>
        </div>
        <div class="w-full h-2 bg-[var(--color-border)] rounded-full overflow-hidden">
          <div
            class="h-full bg-[var(--color-primary)] rounded-full transition-all duration-500"
            :style="{ width: `${whatifStore.progress}%` }"
          />
        </div>
      </div>
    </Card>

    <!-- Error -->
    <div
      v-if="whatifStore.error"
      class="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-lg p-3"
    >
      {{ whatifStore.error }}
    </div>

    <!-- Result -->
    <Card v-if="whatifStore.isComplete && whatifStore.resultVariantId">
      <div class="flex items-center gap-3 mb-3">
        <div class="w-8 h-8 rounded-full bg-[var(--badge-success-bg-soft)] flex items-center justify-center">
          <svg class="w-4 h-4 text-[var(--color-success)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </div>
        <div>
          <p class="text-sm font-semibold text-[var(--color-text)]">What-If Scenario Complete</p>
          <p class="text-xs text-[var(--color-text-muted)]">
            Variant ID: {{ whatifStore.resultVariantId }}
          </p>
        </div>
      </div>

      <!-- Demo metrics preview -->
      <div
        v-if="whatifStore.variants.length"
        class="grid grid-cols-2 gap-3 mb-4"
      >
        <div
          v-for="(value, key) in whatifStore.variants[whatifStore.variants.length - 1].metrics"
          :key="key"
          class="px-3 py-2 rounded-lg bg-[var(--color-tint)]"
        >
          <span class="block text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">
            {{ key.replace(/_/g, ' ') }}
          </span>
          <span class="text-sm font-semibold text-[var(--color-text)]">
            {{ typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value }}
          </span>
        </div>
      </div>

      <Button
        variant="secondary"
        size="sm"
        @click="router.push(`/workspace/${whatifStore.baseSimulationId}`)"
      >
        View Base Simulation &rarr;
      </Button>
    </Card>

    <!-- Run Button -->
    <Button
      v-if="whatifStore.baseSimulationId && !whatifStore.isRunning"
      variant="primary"
      size="lg"
      :disabled="!whatifStore.canRun"
      :loading="whatifStore.isRunning"
      class="w-full"
      @click="handleRun"
    >
      Run What-If Analysis
    </Button>
  </div>
</template>
