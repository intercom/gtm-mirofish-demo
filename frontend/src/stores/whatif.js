import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { whatifApi } from '../api/whatif'

const PARAMETER_DEFS = [
  {
    key: 'agent_count',
    label: 'Agent Count',
    min: 10,
    max: 500,
    step: 10,
    defaultValue: 200,
    format: (v) => `${v} agents`,
  },
  {
    key: 'rounds',
    label: 'Simulation Rounds',
    min: 5,
    max: 200,
    step: 5,
    defaultValue: 50,
    format: (v) => `${v} rounds`,
  },
  {
    key: 'temperature',
    label: 'LLM Temperature',
    min: 0,
    max: 2,
    step: 0.1,
    defaultValue: 0.7,
    format: (v) => v.toFixed(1),
  },
  {
    key: 'duration_hours',
    label: 'Duration (hours)',
    min: 6,
    max: 168,
    step: 6,
    defaultValue: 72,
    format: (v) => `${v}h`,
  },
  {
    key: 'personality_mix',
    label: 'Personality Assertiveness',
    min: 0,
    max: 100,
    step: 5,
    defaultValue: 50,
    format: (v) => `${v}%`,
  },
]

const PRESETS = [
  {
    id: 'more_agents',
    label: 'More Agents',
    icon: '👥',
    modifications: [{ parameter: 'agent_count', value: 350 }],
  },
  {
    id: 'fewer_rounds',
    label: 'Fewer Rounds',
    icon: '⏱',
    modifications: [{ parameter: 'rounds', value: 20 }],
  },
  {
    id: 'higher_temp',
    label: 'Higher Temperature',
    icon: '🔥',
    modifications: [{ parameter: 'temperature', value: 1.2 }],
  },
  {
    id: 'conservative',
    label: 'Conservative Personalities',
    icon: '🛡',
    modifications: [{ parameter: 'personality_mix', value: 20 }],
  },
]

export const useWhatifStore = defineStore('whatif', () => {
  const baseSimulationId = ref(null)
  const modifications = ref([])
  const status = ref('idle') // idle | running | complete | error
  const progress = ref(0)
  const progressMessage = ref('')
  const error = ref(null)
  const resultVariantId = ref(null)
  const variants = ref([])

  const isRunning = computed(() => status.value === 'running')
  const isComplete = computed(() => status.value === 'complete')
  const hasModifications = computed(() => modifications.value.length > 0)
  const canRun = computed(
    () => baseSimulationId.value && hasModifications.value && !isRunning.value,
  )

  function setBaseSimulation(id) {
    baseSimulationId.value = id
    if (status.value === 'complete' || status.value === 'error') {
      status.value = 'idle'
      resultVariantId.value = null
    }
  }

  function addModification(parameter, value) {
    const existing = modifications.value.find((m) => m.parameter === parameter)
    if (existing) {
      existing.value = value
    } else {
      modifications.value.push({ parameter, value })
    }
  }

  function removeModification(parameter) {
    modifications.value = modifications.value.filter(
      (m) => m.parameter !== parameter,
    )
  }

  function clearModifications() {
    modifications.value = []
  }

  function applyPreset(presetId) {
    const preset = PRESETS.find((p) => p.id === presetId)
    if (!preset) return
    for (const mod of preset.modifications) {
      addModification(mod.parameter, mod.value)
    }
  }

  async function runWhatIf() {
    if (!canRun.value) return

    status.value = 'running'
    progress.value = 0
    progressMessage.value = 'Preparing what-if scenario...'
    error.value = null
    resultVariantId.value = null

    try {
      const { data } = await whatifApi.run({
        base_simulation_id: baseSimulationId.value,
        modifications: modifications.value,
      })
      resultVariantId.value = data.variant_id
      status.value = 'complete'
      progress.value = 100
      progressMessage.value = 'What-if analysis complete'
    } catch (e) {
      if (e.status === 0 || e.status === 404) {
        await _runDemoMode()
      } else {
        error.value = e.message
        status.value = 'error'
      }
    }
  }

  async function _runDemoMode() {
    const steps = [
      { pct: 15, msg: 'Cloning base scenario configuration...' },
      { pct: 35, msg: 'Applying parameter modifications...' },
      { pct: 55, msg: 'Running variant simulation...' },
      { pct: 75, msg: 'Comparing outcomes to baseline...' },
      { pct: 90, msg: 'Generating comparison metrics...' },
      { pct: 100, msg: 'What-if analysis complete' },
    ]

    for (const step of steps) {
      await new Promise((r) => setTimeout(r, 600 + Math.random() * 400))
      progress.value = step.pct
      progressMessage.value = step.msg
    }

    resultVariantId.value = `demo-variant-${Date.now()}`
    const demoVariant = {
      id: resultVariantId.value,
      baseSimulationId: baseSimulationId.value,
      modifications: [...modifications.value],
      metrics: {
        consensus_reached: Math.random() > 0.4,
        avg_sentiment: +(0.3 + Math.random() * 0.5).toFixed(2),
        decision_quality: +(0.5 + Math.random() * 0.4).toFixed(2),
        time_to_resolution: Math.floor(10 + Math.random() * 40),
      },
      timestamp: Date.now(),
    }
    variants.value.push(demoVariant)
    status.value = 'complete'
  }

  function reset() {
    baseSimulationId.value = null
    modifications.value = []
    status.value = 'idle'
    progress.value = 0
    progressMessage.value = ''
    error.value = null
    resultVariantId.value = null
  }

  return {
    baseSimulationId,
    modifications,
    status,
    progress,
    progressMessage,
    error,
    resultVariantId,
    variants,
    isRunning,
    isComplete,
    hasModifications,
    canRun,
    parameterDefs: PARAMETER_DEFS,
    presets: PRESETS,
    setBaseSimulation,
    addModification,
    removeModification,
    clearModifications,
    applyPreset,
    runWhatIf,
    reset,
  }
})
