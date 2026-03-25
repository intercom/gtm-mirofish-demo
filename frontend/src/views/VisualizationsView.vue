<script setup>
import { ref, onMounted } from 'vue'
import NetworkViz from '../components/visualizations/NetworkViz.vue'
import WaveViz from '../components/visualizations/WaveViz.vue'
import BubbleViz from '../components/visualizations/BubbleViz.vue'
import FunnelViz from '../components/visualizations/FunnelViz.vue'

const visible = ref(false)

onMounted(() => {
  requestAnimationFrame(() => { visible.value = true })
})

const cards = [
  {
    key: 'network',
    title: 'Agent Network',
    description: 'Force-directed graph showing how simulated agents connect and influence each other across platforms.',
  },
  {
    key: 'waves',
    title: 'Engagement Waves',
    description: 'Layered wave animation representing engagement intensity across campaign channels over time.',
  },
  {
    key: 'bubbles',
    title: 'Platform Activity',
    description: 'Floating bubbles sized by engagement volume across different social platforms.',
  },
  {
    key: 'funnel',
    title: 'Conversion Funnel',
    description: 'Particle flow visualization showing prospects moving through GTM conversion stages.',
  },
]
</script>

<template>
  <div class="min-h-screen bg-[var(--color-bg)] px-4 md:px-8 py-8">
    <div class="max-w-7xl mx-auto">
      <header
        class="mb-8 transition-all duration-500"
        :class="visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'"
      >
        <h1 class="text-3xl font-bold text-[var(--color-text)] tracking-tight">
          Animated Visualizations
        </h1>
        <p class="mt-2 text-[var(--color-text-secondary)] max-w-2xl">
          Interactive D3.js visualizations showcasing data patterns from MiroFish swarm simulations.
        </p>
      </header>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div
          v-for="(card, i) in cards"
          :key="card.key"
          class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden transition-all duration-500"
          :class="visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'"
          :style="{ transitionDelay: `${(i + 1) * 100}ms` }"
        >
          <div class="px-5 py-4 border-b border-[var(--color-border)]">
            <h2 class="text-lg font-semibold text-[var(--color-text)]">{{ card.title }}</h2>
            <p class="text-sm text-[var(--color-text-secondary)] mt-1">{{ card.description }}</p>
          </div>
          <div class="h-72 relative">
            <NetworkViz v-if="card.key === 'network'" />
            <WaveViz v-else-if="card.key === 'waves'" />
            <BubbleViz v-else-if="card.key === 'bubbles'" />
            <FunnelViz v-else-if="card.key === 'funnel'" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
