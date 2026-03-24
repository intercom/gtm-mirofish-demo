<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { listScenarios } from '../api.js'

const router = useRouter()
const showCards = ref(false)
const showSteps = ref(false)

function onStaggerBeforeEnter(el) {
  el.style.opacity = 0
  el.style.transform = 'translateY(12px)'
}

function onStaggerEnter(el, done) {
  const delay = el.dataset.index * 80
  setTimeout(() => {
    el.style.transition = 'opacity var(--transition-base), transform var(--transition-base)'
    el.style.opacity = 1
    el.style.transform = 'translateY(0)'
    el.addEventListener('transitionend', done, { once: true })
  }, delay)
}

onMounted(() => {
  showCards.value = true
  setTimeout(() => { showSteps.value = true }, 200)
})

const steps = [
  {
    icon: '🧠',
    bgClass: 'bg-[rgba(32,104,255,0.1)]',
    title: '1. Seed Your Scenario',
    description: 'Upload campaign copy, signal definitions, or pricing scenarios as seed information.',
  },
  {
    icon: '🐟',
    bgClass: 'bg-[rgba(255,86,0,0.1)]',
    title: '2. Simulate the Swarm',
    description: 'Hundreds of AI agents with unique personas interact, debate, and react on simulated social platforms.',
  },
  {
    icon: '📊',
    bgClass: 'bg-[rgba(170,0,255,0.1)]',
    title: '3. Get Predictive Reports',
    description: 'Multi-chapter analysis reveals engagement patterns, objections, and segment-specific insights.',
  },
]

const ICON_MAP = {
  mail: '📧',
  signal: '📡',
  dollar: '💰',
  sparkle: '✨',
}

function resolveIcon(icon) {
  if (!icon) return '🐟'
  if (/\p{Emoji}/u.test(icon)) return icon
  return ICON_MAP[icon] || '🐟'
}

const scenarios = ref([])
const loading = ref(true)
const error = ref(null)

async function loadScenarios() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch('/api/gtm/scenarios')
    if (!res.ok) throw new Error(`Failed to load scenarios (${res.status})`)
    const json = await res.json()
    const list = json.scenarios || json
    if (list.length) list[0].hero = true
    scenarios.value = list
  } catch (e) {
    error.value = e.message
    // Fallback to hardcoded scenarios so the page is still usable
    scenarios.value = [
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
    ]
    error.value = null
  } finally {
    loading.value = false
  }
}

onMounted(loadScenarios)

function launchScenario(id) {
  router.push(`/scenarios/${id}`)
}
</script>

<template>
  <div>
    <!-- Hero Section -->
    <section class="bg-gradient-to-b from-[#050505] to-[#1a1a3e] text-white px-4 md:px-6 py-12 md:py-32">
      <div class="max-w-4xl mx-auto text-center">
        <p class="text-[#2068FF] text-xs font-semibold tracking-[2px] uppercase mb-3 md:mb-4">
          Intercom GTM Systems
        </p>
        <h1 class="text-3xl md:text-6xl font-semibold mb-3 md:mb-4">
          MiroFish Swarm Intelligence
        </h1>
        <p class="text-base md:text-lg text-white/60 max-w-2xl mx-auto mb-8 md:mb-12">
          Predict campaign outcomes before they happen. Simulate how prospects react
          to your outbound, signals, and pricing changes.
        </p>

        <!-- Loading State -->
        <div v-if="loading" class="max-w-2xl mx-auto">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="n in 4" :key="n"
              class="rounded-lg p-5 border border-white/10 bg-white/5 animate-pulse">
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded bg-white/10"></div>
                <div class="flex-1 space-y-2">
                  <div class="h-4 bg-white/10 rounded w-3/4"></div>
                  <div class="h-3 bg-white/10 rounded w-full"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Error State (within dark hero context) -->
        <div v-else-if="error" class="max-w-md mx-auto text-center py-8">
          <div class="w-14 h-14 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
            <svg class="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
          </div>
          <h3 class="text-base font-semibold text-white mb-1">Failed to load scenarios</h3>
          <p class="text-sm text-white/50 mb-4">{{ error }}</p>
          <button @click="loadScenarios"
            class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors">
            Try Again
          </button>
        </div>

        <!-- Empty State -->
        <div v-else-if="scenarios.length === 0" class="max-w-md mx-auto text-center py-8">
          <div class="w-16 h-16 rounded-full bg-[rgba(32,104,255,0.15)] flex items-center justify-center mx-auto mb-4">
            <span class="text-3xl">🐟</span>
          </div>
          <h3 class="text-base font-semibold text-white mb-1">No scenarios available</h3>
          <p class="text-sm text-white/50">Check back soon — scenarios are being configured.</p>
        </div>

        <!-- Scenario Cards -->
        <TransitionGroup
          v-else
          tag="div"
          class="grid grid-cols-1 gap-3 md:gap-4 max-w-2xl mx-auto md:grid-cols-2"
          :css="false"
          @before-enter="onStaggerBeforeEnter"
          @enter="onStaggerEnter"
        >
          <button
            v-for="(scenario, i) in showCards ? scenarios : []"
            :key="scenario.id"
            :data-index="i"
            @click="launchScenario(scenario.id)"
            class="text-left rounded-lg p-5 transition-all duration-300 cursor-pointer border"
            :class="[
              scenario.hero
                ? 'bg-[rgba(32,104,255,0.15)] border-[rgba(32,104,255,0.3)] hover:bg-[rgba(32,104,255,0.25)]'
                : 'bg-white/5 border-white/10 hover:bg-white/10',
            ]"
          >
            <div class="flex items-start gap-3">
              <span class="text-2xl">{{ resolveIcon(scenario.icon) }}</span>
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
        </TransitionGroup>
      </div>
    </section>

    <!-- How It Works -->
    <section class="px-4 md:px-6 py-10 md:py-16 bg-[var(--color-bg)]">
      <div class="max-w-4xl mx-auto text-center">
        <h2 class="text-xl md:text-2xl font-semibold text-[var(--color-text)] mb-6 md:mb-8">How It Works</h2>
        <TransitionGroup
          tag="div"
          class="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8"
          :css="false"
          @before-enter="onStaggerBeforeEnter"
          @enter="onStaggerEnter"
        >
          <div v-for="(step, i) in showSteps ? steps : []" :key="step.title" :data-index="i">
            <div class="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4" :class="step.bgClass">
              <span class="text-xl">{{ step.icon }}</span>
            </div>
            <h3 class="text-sm font-semibold text-[var(--color-text)] mb-2">{{ step.title }}</h3>
            <p class="text-xs text-[var(--color-text-secondary)]">{{ step.description }}</p>
          </div>
        </TransitionGroup>
      </div>
    </section>

    <!-- Stats Banner -->
    <section class="bg-[#050505] text-white px-4 md:px-6 py-8 md:py-10">
      <div class="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 text-center">
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
