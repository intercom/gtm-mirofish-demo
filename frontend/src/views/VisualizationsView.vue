<script setup>
import { ref, onMounted } from 'vue'
import NetworkViz from '../components/visualizations/NetworkViz.vue'
import WaveViz from '../components/visualizations/WaveViz.vue'
import BubbleViz from '../components/visualizations/BubbleViz.vue'
import FunnelViz from '../components/visualizations/FunnelViz.vue'

const visible = ref(false)
const selected = ref(null)

onMounted(() => {
  requestAnimationFrame(() => { visible.value = true })
})

function select(key) {
  selected.value = selected.value === key ? null : key
}

const selectedCard = ref(null)
// Keep a computed for the selected card object
const activeCard = ref(null)

function openCard(card) {
  selected.value = card.key
}

function closeCard() {
  selected.value = null
}

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

      <!-- Expanded single visualization -->
      <div v-if="selected" class="transition-all duration-300">
        <button
          @click="closeCard"
          class="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
          </svg>
          Back to all visualizations
        </button>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden">
          <div class="px-5 py-4 border-b border-[var(--color-border)]">
            <h2 class="text-lg font-semibold text-[var(--color-text)]">{{ cards.find(c => c.key === selected)?.title }}</h2>
            <p class="text-sm text-[var(--color-text-secondary)] mt-1">{{ cards.find(c => c.key === selected)?.description }}</p>
          </div>
          <div class="h-[70vh] relative">
            <NetworkViz v-if="selected === 'network'" />
            <WaveViz v-else-if="selected === 'waves'" />
            <BubbleViz v-else-if="selected === 'bubbles'" />
            <FunnelViz v-else-if="selected === 'funnel'" />
          </div>
        </div>
      </div>

      <!-- Grid view -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div
          v-for="(card, i) in cards"
          :key="card.key"
          class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden transition-all duration-500 cursor-pointer hover:border-[#2068FF]/50 hover:shadow-lg hover:shadow-[#2068FF]/5"
          :class="visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'"
          :style="{ transitionDelay: `${(i + 1) * 100}ms` }"
          @click="openCard(card)"
        >
          <div class="px-5 py-4 border-b border-[var(--color-border)]">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-[var(--color-text)]">{{ card.title }}</h2>
              <svg class="w-4 h-4 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
              </svg>
            </div>
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
