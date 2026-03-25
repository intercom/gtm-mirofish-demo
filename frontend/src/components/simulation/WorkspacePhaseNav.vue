<script setup>
import { computed } from 'vue'

const props = defineProps({
  activeTab: { type: String, required: true },
  taskId: { type: String, required: true },
  polling: { type: Object, required: true },
})

defineEmits(['update:activeTab'])

const tabs = computed(() => {
  const nodeCount = props.polling.graphData.value?.nodes?.length || 0
  const runStatus = props.polling.runStatus.value
  const simStatus = props.polling.simStatus.value

  let simMetric = null
  if (simStatus === 'running' && runStatus) {
    const current = runStatus.current_round ?? 0
    const total = runStatus.total_rounds ?? 0
    if (total > 0) {
      simMetric = `Round ${current}/${total}`
    }
  } else if (simStatus === 'completed') {
    simMetric = '(Complete)'
  }

  return [
    {
      key: 'graph',
      label: 'Graph',
      metric: nodeCount > 0 ? `${nodeCount} nodes` : null,
    },
    {
      key: 'simulation',
      label: 'Simulation',
      metric: simMetric,
    },
    {
      key: 'network',
      label: 'Network',
      metric: null,
    },
  ]
})
</script>

<template>
  <nav class="flex items-center gap-1 border-b border-[var(--color-border)]">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      @click="$emit('update:activeTab', tab.key)"
      class="relative px-4 py-3 text-sm font-medium transition-colors"
      :class="activeTab === tab.key
        ? 'text-[#050505]'
        : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
    >
      {{ tab.label }}
      <span
        v-if="tab.metric"
        class="ml-1.5 text-xs font-normal opacity-60"
      >{{ tab.metric }}</span>
      <span
        v-if="activeTab === tab.key"
        class="absolute bottom-0 left-0 right-0 h-0.5 bg-[#2068FF] transition-all duration-300"
      />
    </button>

    <!-- Spacer -->
    <div class="flex-1" />

    <!-- Status indicator -->
    <div class="flex items-center gap-2 text-xs text-[var(--color-text-muted)] pr-2">
      <template v-if="polling.graphStatus.value === 'building'">
        <svg class="w-3.5 h-3.5 animate-spin text-[#2068FF]" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span>Building graph... {{ polling.graphProgress.value }}%</span>
      </template>
      <template v-else-if="polling.simStatus.value === 'running'">
        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <span>Running simulation...</span>
      </template>
      <template v-else-if="polling.simStatus.value === 'completed'">
        <span class="text-emerald-600 font-medium">Complete</span>
      </template>
    </div>

    <!-- Report link -->
    <router-link
      v-if="polling.simStatus.value === 'completed'"
      :to="`/report/${taskId}`"
      class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-white bg-[#2068FF] hover:bg-[#1a5ae0] rounded-md no-underline transition-colors"
    >Report &rarr;</router-link>
  </nav>
</template>
