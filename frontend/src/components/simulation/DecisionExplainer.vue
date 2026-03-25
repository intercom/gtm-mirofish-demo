<script setup>
import { ref, computed } from 'vue'
import { decisionsApi } from '../../api/decisions'

const props = defineProps({
  agentId: { type: String, required: true },
  decision: { type: Object, required: true },
  context: { type: Object, default: () => ({}) },
  outcome: { type: Object, default: null },
})

const explanation = ref(null)
const counterfactual = ref(null)
const qualityScore = ref(null)
const loading = ref(false)
const error = ref(null)
const activeTab = ref('explanation')

const tabs = computed(() => {
  const list = [{ key: 'explanation', label: 'Explanation' }]
  if (counterfactual.value) {
    list.push({ key: 'counterfactual', label: 'What If?' })
  }
  if (qualityScore.value) {
    list.push({ key: 'score', label: 'Quality Score' })
  }
  return list
})

const ratingColor = computed(() => {
  if (!qualityScore.value) return ''
  const map = {
    excellent: 'text-emerald-600',
    good: 'text-[var(--color-primary)]',
    fair: 'text-[var(--color-orange)]',
    poor: 'text-[var(--color-error)]',
  }
  return map[qualityScore.value.rating] || 'text-gray-600'
})

const confidencePercent = computed(() => {
  if (!explanation.value) return 0
  return Math.round(explanation.value.confidence * 100)
})

async function fetchExplanation() {
  loading.value = true
  error.value = null
  try {
    const res = await decisionsApi.explain({
      agent_id: props.agentId,
      decision: props.decision,
      context: props.context,
    })
    explanation.value = res.data.data
  } catch (e) {
    error.value = e.message || 'Failed to generate explanation'
  } finally {
    loading.value = false
  }
}

async function fetchCounterfactual(alternative) {
  loading.value = true
  error.value = null
  try {
    const res = await decisionsApi.counterfactual({
      decision: props.decision,
      alternative,
      context: props.context,
    })
    counterfactual.value = res.data.data
    activeTab.value = 'counterfactual'
  } catch (e) {
    error.value = e.message || 'Failed to generate counterfactual'
  } finally {
    loading.value = false
  }
}

async function fetchScore() {
  if (!props.outcome) return
  loading.value = true
  error.value = null
  try {
    const res = await decisionsApi.score({
      decision: props.decision,
      outcome: props.outcome,
      context: props.context,
    })
    qualityScore.value = res.data.data
    activeTab.value = 'score'
  } catch (e) {
    error.value = e.message || 'Failed to score decision'
  } finally {
    loading.value = false
  }
}

defineExpose({ fetchExplanation, fetchCounterfactual, fetchScore })
</script>

<template>
  <div class="rounded-lg border border-gray-200 bg-white overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
      <div class="flex items-center gap-2">
        <span class="w-6 h-6 rounded-full bg-[var(--color-primary)] text-white text-xs flex items-center justify-center font-semibold">?</span>
        <span class="text-sm font-semibold text-[var(--color-text)]">Decision Explainer</span>
      </div>
      <button
        v-if="!explanation && !loading"
        class="text-xs font-medium px-3 py-1.5 rounded-md bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] transition-colors"
        @click="fetchExplanation"
      >
        Explain This Decision
      </button>
      <div v-if="loading" class="flex items-center gap-1.5 text-xs text-gray-500">
        <svg class="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        Analyzing...
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="px-4 py-3 bg-red-50 text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Content -->
    <div v-if="explanation" class="divide-y divide-gray-100">
      <!-- Tabs -->
      <div v-if="tabs.length > 1" class="flex gap-1 px-4 pt-3 pb-0">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="text-xs font-medium px-3 py-1.5 rounded-t-md transition-colors"
          :class="activeTab === tab.key
            ? 'bg-white border border-b-0 border-gray-200 text-[var(--color-primary)]'
            : 'text-gray-500 hover:text-gray-700'"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Explanation Tab -->
      <div v-if="activeTab === 'explanation'" class="p-4 space-y-3">
        <p class="text-sm text-[var(--color-text)] leading-relaxed">
          {{ explanation.explanation }}
        </p>

        <!-- Factors -->
        <div v-if="explanation.factors?.length">
          <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Factors Considered</p>
          <ul class="space-y-1">
            <li
              v-for="(factor, i) in explanation.factors"
              :key="i"
              class="flex items-start gap-2 text-sm text-gray-700"
            >
              <span
                class="mt-1 w-1.5 h-1.5 rounded-full shrink-0"
                :class="factor === explanation.main_factor ? 'bg-[var(--color-primary)]' : 'bg-gray-300'"
              />
              <span :class="{ 'font-medium text-[var(--color-text)]': factor === explanation.main_factor }">
                {{ factor }}
                <span v-if="factor === explanation.main_factor" class="text-xs text-[var(--color-primary)] ml-1">(primary)</span>
              </span>
            </li>
          </ul>
        </div>

        <!-- Confidence -->
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-500">Confidence</span>
          <div class="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full bg-[var(--color-primary)] transition-all duration-500"
              :style="{ width: confidencePercent + '%' }"
            />
          </div>
          <span class="text-xs font-medium text-gray-600">{{ confidencePercent }}%</span>
        </div>

        <!-- Actions -->
        <div class="flex gap-2 pt-1">
          <button
            v-if="outcome && !qualityScore"
            class="text-xs text-[var(--color-primary)] hover:underline"
            @click="fetchScore"
          >
            Score this decision
          </button>
        </div>
      </div>

      <!-- Counterfactual Tab -->
      <div v-if="activeTab === 'counterfactual' && counterfactual" class="p-4 space-y-3">
        <p class="text-sm text-[var(--color-text)] leading-relaxed">
          {{ counterfactual.narrative }}
        </p>
        <div class="flex items-center gap-4 text-sm">
          <div>
            <span class="text-xs text-gray-500">Impact Delta</span>
            <p class="font-semibold text-[var(--color-text)]">{{ counterfactual.impact_delta }}</p>
          </div>
          <div>
            <span class="text-xs text-gray-500">Likelihood</span>
            <p class="font-semibold text-[var(--color-text)]">{{ Math.round(counterfactual.likelihood * 100) }}%</p>
          </div>
        </div>
      </div>

      <!-- Quality Score Tab -->
      <div v-if="activeTab === 'score' && qualityScore" class="p-4 space-y-3">
        <div class="flex items-center gap-3">
          <div class="text-3xl font-bold text-[var(--color-text)]">{{ qualityScore.score }}</div>
          <div>
            <span class="text-xs text-gray-500">/ 100</span>
            <p class="text-sm font-semibold capitalize" :class="ratingColor">{{ qualityScore.rating }}</p>
          </div>
        </div>
        <p class="text-sm text-gray-700 leading-relaxed">{{ qualityScore.rationale }}</p>
        <div v-if="qualityScore.improvements?.length">
          <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Improvements</p>
          <ul class="space-y-1">
            <li
              v-for="(item, i) in qualityScore.improvements"
              :key="i"
              class="flex items-start gap-2 text-sm text-gray-700"
            >
              <span class="mt-1 w-1.5 h-1.5 rounded-full bg-[var(--color-orange)] shrink-0" />
              {{ item }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
