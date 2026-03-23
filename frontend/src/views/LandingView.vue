<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

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
            v-for="scenario in scenarios"
            :key="scenario.id"
            @click="launchScenario(scenario.id)"
            class="text-left rounded-lg p-5 transition-all duration-300 cursor-pointer border"
            :class="scenario.hero
              ? 'bg-[rgba(32,104,255,0.15)] border-[rgba(32,104,255,0.3)] hover:bg-[rgba(32,104,255,0.25)]'
              : 'bg-white/5 border-white/10 hover:bg-white/10'"
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
          <div>
            <div class="w-12 h-12 rounded-full bg-[rgba(32,104,255,0.1)] flex items-center justify-center mx-auto mb-4">
              <span class="text-xl">🧠</span>
            </div>
            <h3 class="text-sm font-semibold text-[#050505] mb-2">1. Seed Your Scenario</h3>
            <p class="text-xs text-[#555]">Upload campaign copy, signal definitions, or pricing scenarios as seed information.</p>
          </div>
          <div>
            <div class="w-12 h-12 rounded-full bg-[rgba(255,86,0,0.1)] flex items-center justify-center mx-auto mb-4">
              <span class="text-xl">🐟</span>
            </div>
            <h3 class="text-sm font-semibold text-[#050505] mb-2">2. Simulate the Swarm</h3>
            <p class="text-xs text-[#555]">Hundreds of AI agents with unique personas interact, debate, and react on simulated social platforms.</p>
          </div>
          <div>
            <div class="w-12 h-12 rounded-full bg-[rgba(170,0,255,0.1)] flex items-center justify-center mx-auto mb-4">
              <span class="text-xl">📊</span>
            </div>
            <h3 class="text-sm font-semibold text-[#050505] mb-2">3. Get Predictive Reports</h3>
            <p class="text-xs text-[#555]">Multi-chapter analysis reveals engagement patterns, objections, and segment-specific insights.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Banner -->
    <section class="bg-[#050505] text-white px-6 py-10">
      <div class="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
        <div>
          <div class="text-2xl font-semibold text-[#2068FF]">1M+</div>
          <div class="text-xs text-white/40 mt-1">Max Agents</div>
        </div>
        <div>
          <div class="text-2xl font-semibold text-[#ff5600]">23</div>
          <div class="text-xs text-white/40 mt-1">Action Types</div>
        </div>
        <div>
          <div class="text-2xl font-semibold text-[#A0F]">4</div>
          <div class="text-xs text-white/40 mt-1">Analysis Tools</div>
        </div>
        <div>
          <div class="text-2xl font-semibold text-[#090]">2</div>
          <div class="text-xs text-white/40 mt-1">Platforms</div>
        </div>
      </div>
    </section>
  </div>
</template>
