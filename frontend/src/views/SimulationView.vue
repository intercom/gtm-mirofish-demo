<script setup>
import { ref, onMounted } from 'vue'
import { useCountUp } from '../composables/useCountUp.js'

const props = defineProps({ taskId: String })
const status = ref('running')
const metrics = ref({ actions: 0, replies: 0, likes: 0, round: '0/24' })
const activities = ref([])
const visible = ref(false)

const animActions = useCountUp(() => metrics.value.actions)
const animReplies = useCountUp(() => metrics.value.replies)
const animLikes = useCountUp(() => metrics.value.likes)

onMounted(() => {
  visible.value = true
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
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div
        class="bg-white border border-black/10 rounded-lg p-4 text-center"
        :class="visible ? 'card-stagger' : 'opacity-0'"
        :style="visible ? { animationDelay: '0ms' } : {}"
      >
        <div class="text-3xl font-semibold text-[#2068FF]">{{ animActions }}</div>
        <div class="text-xs text-[#888] mt-1">Total Actions</div>
      </div>
      <div
        class="bg-white border border-black/10 rounded-lg p-4 text-center"
        :class="visible ? 'card-stagger' : 'opacity-0'"
        :style="visible ? { animationDelay: '80ms' } : {}"
      >
        <div class="text-3xl font-semibold text-[#ff5600]">{{ animReplies }}</div>
        <div class="text-xs text-[#888] mt-1">Replies</div>
      </div>
      <div
        class="bg-white border border-black/10 rounded-lg p-4 text-center"
        :class="visible ? 'card-stagger' : 'opacity-0'"
        :style="visible ? { animationDelay: '160ms' } : {}"
      >
        <div class="text-3xl font-semibold text-[#A0F]">{{ animLikes }}</div>
        <div class="text-xs text-[#888] mt-1">Likes</div>
      </div>
      <div
        class="bg-white border border-black/10 rounded-lg p-4 text-center"
        :class="visible ? 'card-stagger' : 'opacity-0'"
        :style="visible ? { animationDelay: '240ms' } : {}"
      >
        <div class="text-3xl font-semibold text-[#090]">{{ metrics.round }}</div>
        <div class="text-xs text-[#888] mt-1">Round</div>
      </div>
    </div>

    <!-- Activity Feed Placeholder -->
    <div
      class="bg-white border border-black/10 rounded-lg p-6"
      :class="visible ? 'card-stagger' : 'opacity-0'"
      :style="visible ? { animationDelay: '320ms' } : {}"
    >
      <h3 class="text-sm font-semibold text-[#050505] mb-4">Agent Activity Feed</h3>
      <div class="text-center text-[#888] py-8">
        <p class="text-4xl mb-2">🐦</p>
        <p class="text-sm">Real-time agent actions will appear here</p>
        <p class="text-xs mt-2 text-[#aaa]">Showing posts, replies, likes, and reposts from simulated agents</p>
      </div>
    </div>

    <!-- Generate Report Button -->
    <Transition name="page-fade-slide">
      <div v-if="status === 'complete'" class="text-center mt-8">
        <router-link :to="`/report/${taskId}`"
          class="inline-block bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-8 py-3 rounded-lg font-semibold transition-colors no-underline">
          Generate Report →
        </router-link>
      </div>
    </Transition>
  </div>
</template>
