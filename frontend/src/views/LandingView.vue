<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const visible = ref(false)

onMounted(() => {
  visible.value = true
})

const scenarios = ref([
  {
    id: 'outbound_campaign',
    name: 'Outbound Campaign Pre-Testing',
    description: 'Simulate how AI-generated outbound emails land with synthetic prospect populations.',
    icon: '📧',
    hero: true,
  },
  {
    id: 'signal_validation',
    name: 'Sales Signal Validation',
    description: 'Test whether signals actually predict buying behavior.',
    icon: '📡',
  },
  {
    id: 'pricing_simulation',
    name: 'Pricing Change Simulation',
    description: 'Predict customer reactions to P5 pricing migration.',
    icon: '💰',
  },
  {
    id: 'personalization',
    name: 'Personalization Optimization',
    description: 'Rank email variants by simulated engagement.',
    icon: '✨',
  },
])

function launchScenario(id) {
  router.push(`/scenarios/${id}`)
}
</script>

<template>
  <div>
    <!-- Hero Section -->
    <section class="bg-gradient-to-b from-[#050505] to-[#1a1a3e] text-white px-6 py-20 md:py-32">
      <div class="max-w-4xl mx-auto text-center">
        <p class="text-[#2068FF] text-xs font-semibold tracking-[2px] uppercase mb-4">
          Intercom GTM Systems
        </p>
        <h1 class="text-4xl md:text-6xl font-semibold mb-4">
          MiroFish Swarm Intelligence
        </h1>
        <p class="text-lg text-white/60 max-w-2xl mx-auto mb-12">
          Predict campaign outcomes before they happen. Simulate how prospects react
          to your outbound, signals, and pricing changes.
        </p>

        <!-- Scenario Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
          <button
            v-for="(scenario, index) in scenarios"
            :key="scenario.id"
            @click="launchScenario(scenario.id)"
            class="text-left rounded-lg p-5 transition-all duration-300 cursor-pointer border"
            :class="[
              scenario.hero
                ? 'bg-[rgba(32,104,255,0.15)] border-[rgba(32,104,255,0.3)] hover:bg-[rgba(32,104,255,0.25)]'
                : 'bg-white/5 border-white/10 hover:bg-white/10',
              visible ? 'card-stagger' : 'opacity-0',
            ]"
            :style="visible ? { animationDelay: `${index * 80}ms` } : {}"
          >
            <div class="flex items-start gap-3">
              <span class="text-2xl">{{ scenario.icon }}</span>
              <div>
                <div class="flex items-center gap-2">
                  <h3 class="text-sm font-semibold text-white">{{ scenario.name }}</h3>
                  <span v-if="scenario.hero" class="text-[10px] bg-[#2068FF] text-white px-2 py-0.5 rounded-full">
                    Hero
                  </span>
                </div>
                <p class="text-xs text-white/50 mt-1">{{ scenario.description }}</p>
              </div>
            </div>
          </button>
        </div>
      </div>
    </section>

    <!-- How It Works -->
    <section class="px-6 py-16 bg-[#fafafa]">
      <div class="max-w-4xl mx-auto text-center">
        <h2 class="text-2xl font-semibold text-[#050505] mb-8">How It Works</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div
            v-for="(step, index) in [
              { icon: '🧠', title: '1. Seed Your Scenario', desc: 'Upload campaign copy, signal definitions, or pricing scenarios as seed information.', color: 'rgba(32,104,255,0.1)' },
              { icon: '🐟', title: '2. Simulate the Swarm', desc: 'Hundreds of AI agents with unique personas interact, debate, and react on simulated social platforms.', color: 'rgba(255,86,0,0.1)' },
              { icon: '📊', title: '3. Get Predictive Reports', desc: 'Multi-chapter analysis reveals engagement patterns, objections, and segment-specific insights.', color: 'rgba(170,0,255,0.1)' },
            ]"
            :key="step.title"
            :class="visible ? 'card-stagger' : 'opacity-0'"
            :style="visible ? { animationDelay: `${400 + index * 100}ms` } : {}"
          >
            <div class="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4" :style="{ background: step.color }">
              <span class="text-xl">{{ step.icon }}</span>
            </div>
            <h3 class="text-sm font-semibold text-[#050505] mb-2">{{ step.title }}</h3>
            <p class="text-xs text-[#555]">{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Banner -->
    <section class="bg-[#050505] text-white px-6 py-10">
      <div class="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
        <div
          v-for="(stat, index) in [
            { value: '1M+', label: 'Max Agents', color: '#2068FF' },
            { value: '23', label: 'Action Types', color: '#ff5600' },
            { value: '4', label: 'Analysis Tools', color: '#A0F' },
            { value: '2', label: 'Platforms', color: '#090' },
          ]"
          :key="stat.label"
          :class="visible ? 'card-stagger' : 'opacity-0'"
          :style="visible ? { animationDelay: `${700 + index * 80}ms` } : {}"
        >
          <div class="text-2xl font-semibold" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="text-xs text-white/40 mt-1">{{ stat.label }}</div>
        </div>
      </div>
    </section>
  </div>
</template>
