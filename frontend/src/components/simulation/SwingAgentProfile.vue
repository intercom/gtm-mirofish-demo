<script setup>
import { computed } from 'vue'

const props = defineProps({
  swingAgents: { type: Array, default: () => [] },
  coalitions: { type: Array, default: () => [] },
})

const COALITION_COLORS = [
  '#2068FF', '#ff5600', '#009900', '#9333ea', '#ea580c',
  '#0891b2', '#be185d', '#4f46e5', '#059669', '#d97706',
]

function getColor(coalitionId) {
  return COALITION_COLORS[coalitionId % COALITION_COLORS.length]
}

function getCoalitionLabel(coalitionId) {
  const c = props.coalitions.find(c => c.coalition_id === coalitionId)
  return c?.label || `Coalition ${coalitionId}`
}

const sortedAgents = computed(() =>
  [...props.swingAgents].sort((a, b) => b.influence_score - a.influence_score)
)

function influenceLevel(score) {
  if (score >= 0.7) return { text: 'High', color: '#ff5600' }
  if (score >= 0.4) return { text: 'Medium', color: '#d97706' }
  return { text: 'Low', color: '#009900' }
}
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Swing Agents</h3>
      <span v-if="swingAgents.length" class="text-xs text-[var(--color-text-muted)]">
        {{ swingAgents.length }} agent{{ swingAgents.length !== 1 ? 's' : '' }} changed coalitions
      </span>
    </div>

    <div v-if="sortedAgents.length" class="space-y-3">
      <div
        v-for="agent in sortedAgents"
        :key="agent.agent_id"
        class="border border-[var(--color-border)] rounded-lg p-3 hover:border-[var(--color-text-muted)] transition-colors"
      >
        <!-- Agent header -->
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <div
              class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-semibold"
              :style="{ background: '#050505' }"
            >
              {{ agent.agent_name.charAt(0) }}
            </div>
            <div>
              <div class="text-sm font-medium text-[var(--color-text)]">{{ agent.agent_name }}</div>
              <div class="text-[11px] text-[var(--color-text-muted)]">
                {{ agent.transition_count }} transition{{ agent.transition_count !== 1 ? 's' : '' }}
              </div>
            </div>
          </div>
          <div class="text-right">
            <div
              class="text-xs font-semibold"
              :style="{ color: influenceLevel(agent.influence_score).color }"
            >
              {{ influenceLevel(agent.influence_score).text }}
            </div>
            <div class="text-[11px] text-[var(--color-text-muted)]">
              influence {{ (agent.influence_score * 100).toFixed(0) }}%
            </div>
          </div>
        </div>

        <!-- Transition timeline -->
        <div class="flex items-center gap-1 overflow-x-auto py-1">
          <template v-for="(t, idx) in agent.transitions" :key="idx">
            <span
              v-if="idx === 0"
              class="shrink-0 px-2 py-0.5 rounded text-[10px] font-medium text-white"
              :style="{ background: getColor(t.from_coalition) }"
            >
              {{ getCoalitionLabel(t.from_coalition) }}
            </span>
            <span class="shrink-0 text-[var(--color-text-muted)] text-[10px]">
              &rarr; R{{ t.at_round }} &rarr;
            </span>
            <span
              class="shrink-0 px-2 py-0.5 rounded text-[10px] font-medium text-white"
              :style="{ background: getColor(t.to_coalition) }"
            >
              {{ getCoalitionLabel(t.to_coalition) }}
            </span>
          </template>
        </div>
      </div>
    </div>

    <div v-else class="flex items-center justify-center h-[120px] text-[var(--color-text-muted)] text-sm">
      <span>No agents changed coalitions during this simulation</span>
    </div>
  </div>
</template>
