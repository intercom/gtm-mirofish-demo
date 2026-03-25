<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import AgentKnowledgeGraph from '@/components/graph/AgentKnowledgeGraph.vue'

const route = useRoute()
const graphId = computed(() => route.params.graphId || 'demo')
</script>

<template>
  <AppLayout>
    <div class="flex flex-col h-[calc(100vh-4rem)]">
      <div class="px-6 py-4 border-b border-black/10 dark:border-white/10">
        <h1 class="text-lg font-semibold text-[var(--color-text)]">Knowledge Graph</h1>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
          Explore agent entities, relationships, and facts
        </p>
      </div>
      <div class="flex-1 p-4">
        <AgentKnowledgeGraph :graph-id="graphId" />
      </div>
    </div>
  </AppLayout>
</template>
