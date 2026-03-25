<script setup>
import { computed, inject } from 'vue'

const polling = inject('polling')

const actions = computed(() => polling.recentActions.value || [])

const metrics = computed(() => {
  let replies = 0, likes = 0, reposts = 0, posts = 0
  for (const a of actions.value) {
    const t = (a.action_type || '').toUpperCase()
    if (t.includes('REPLY') || t.includes('COMMENT')) replies++
    else if (t.includes('LIKE') || t.includes('UPVOTE')) likes++
    else if (t.includes('REPOST') || t.includes('RETWEET') || t.includes('SHARE')) reposts++
    else if (t.includes('POST') || t.includes('CREATE') || t.includes('THREAD')) posts++
  }
  return { posts, replies, likes, reposts }
})

const uniqueAgents = computed(() => {
  const names = new Set()
  for (const a of actions.value) {
    if (a.agent_name) names.add(a.agent_name)
  }
  return names.size
})

const metricCards = computed(() => [
  { label: 'Posts', value: metrics.value.posts, color: 'var(--color-primary)' },
  { label: 'Replies', value: metrics.value.replies, color: 'var(--color-fin-orange)' },
  { label: 'Likes', value: metrics.value.likes, color: 'var(--color-success)' },
  { label: 'Reposts', value: metrics.value.reposts, color: 'var(--color-text-secondary)' },
  { label: 'Agents', value: uniqueAgents.value, color: '#AA00FF' },
])
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 h-full flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Metrics</h3>
      <span
        v-if="polling.simStatus.value === 'running'"
        class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-red-500/10 text-red-500"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
        Live
      </span>
    </div>

    <div class="flex-1 grid grid-cols-2 gap-2 auto-rows-min content-start">
      <div
        v-for="card in metricCards"
        :key="card.label"
        class="bg-[var(--color-tint)] rounded-lg p-3 text-center"
      >
        <div class="text-xl font-semibold" :style="{ color: card.color }">{{ card.value }}</div>
        <div class="text-[10px] text-[var(--color-text-muted)] mt-0.5">{{ card.label }}</div>
      </div>
    </div>

    <!-- Placeholder for future mini-charts -->
    <div
      v-if="!actions.length"
      class="flex-1 flex items-center justify-center text-xs text-[var(--color-text-muted)]"
    >
      Metrics will update as agents interact
    </div>
  </div>
</template>
