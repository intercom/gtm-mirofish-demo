<script setup>
import { ref, computed, onMounted } from 'vue'
import { useCountUp } from '../composables/useCountUp.js'

const props = defineProps({ taskId: String })
const status = ref('running')
const actions = ref(0)
const replies = ref(0)
const likes = ref(0)
const round = ref(0)
const totalRounds = 24
const activities = ref([])
const showMetrics = ref(false)

const actionsDisplay = useCountUp(actions)
const repliesDisplay = useCountUp(replies)
const likesDisplay = useCountUp(likes)
const roundDisplay = useCountUp(round)

const metricCards = computed(() => [
  { key: 'actions', value: actionsDisplay.value, label: 'Total Actions', color: 'text-[#2068FF]' },
  { key: 'replies', value: repliesDisplay.value, label: 'Replies', color: 'text-[#ff5600]' },
  { key: 'likes', value: likesDisplay.value, label: 'Likes', color: 'text-[#A0F]' },
  { key: 'round', value: `${roundDisplay.value}/${totalRounds}`, label: 'Round', color: 'text-[#090]' },
])

function onCardBeforeEnter(el) {
  el.style.opacity = 0
  el.style.transform = 'translateY(12px)'
}

function onCardEnter(el, done) {
  const delay = el.dataset.index * 100
  setTimeout(() => {
    el.style.transition = 'opacity var(--transition-base), transform var(--transition-base)'
    el.style.opacity = 1
    el.style.transform = 'translateY(0)'
    el.addEventListener('transitionend', done, { once: true })
  }, delay)
}

onMounted(() => {
  showMetrics.value = true
  // Simulate metrics counting up as data arrives
  setTimeout(() => { actions.value = 142 }, 400)
  setTimeout(() => { replies.value = 38 }, 500)
  setTimeout(() => { likes.value = 87 }, 600)
  setTimeout(() => { round.value = 6 }, 700)
})

// TODO: Poll /api/simulation/status every 3s
// Parse JSONL activity logs
// Show real-time metrics and engagement timeline
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-[#050505]">Live Simulation</h1>
        <p class="text-sm text-[#888]">Task: {{ taskId }}</p>
      </div>
      <span class="px-4 py-1.5 rounded-full text-xs font-semibold"
        :class="status === 'running' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'">
        {{ status === 'running' ? '● Running' : '✓ Complete' }}
      </span>
    </div>

    <!-- Metrics -->
    <TransitionGroup
      tag="div"
      class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
      :css="false"
      @before-enter="onCardBeforeEnter"
      @enter="onCardEnter"
    >
      <div
        v-for="(card, i) in showMetrics ? metricCards : []"
        :key="card.key"
        :data-index="i"
        class="bg-white border border-black/10 rounded-lg p-4 text-center"
      >
        <div class="text-3xl font-semibold" :class="card.color">{{ card.value }}</div>
        <div class="text-xs text-[#888] mt-1">{{ card.label }}</div>
      </div>
    </TransitionGroup>

    <!-- Activity Feed Placeholder -->
    <div class="bg-white border border-black/10 rounded-lg p-6">
      <h3 class="text-sm font-semibold text-[#050505] mb-4">Agent Activity Feed</h3>
      <div class="text-center text-[#888] py-8">
        <p class="text-4xl mb-2">🐦</p>
        <p class="text-sm">Real-time agent actions will appear here</p>
        <p class="text-xs mt-2 text-[#aaa]">Showing posts, replies, likes, and reposts from simulated agents</p>
      </div>
    </div>

    <!-- Generate Report Button -->
    <div v-if="status === 'complete'" class="text-center mt-8">
      <router-link :to="`/report/${taskId}`"
        class="inline-block bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-8 py-3 rounded-lg font-semibold transition-colors no-underline">
        Generate Report →
      </router-link>
    </div>
  </div>
</template>
