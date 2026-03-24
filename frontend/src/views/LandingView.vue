<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listScenarios } from '../api.js'
import { useDemoMode } from '../composables/useDemoMode'
import { API_BASE } from '../api/client'

const router = useRouter()
const { isDemoMode } = useDemoMode()
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
    const res = await fetch(`${API_BASE}/gtm/scenarios`)
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
        <p class="text-base md:text-lg text-white/60 max-w-2xl mx-auto" :class="isDemoMode ? 'mb-3' : 'mb-8 md:mb-12'">
          Predict campaign outcomes before they happen. Simulate how prospects react
          to your outbound, signals, and pricing changes.
        </p>
        <p v-if="isDemoMode" class="text-sm text-white/35 mb-8 md:mb-12">
          Interactive demo with simulated swarm intelligence
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
            class="text-left rounded-lg transition-all duration-300 cursor-pointer border"
            :class="[
              scenario.hero
                ? 'md:col-span-2 p-6 bg-[rgba(32,104,255,0.15)] border-[rgba(32,104,255,0.3)] hover:bg-[rgba(32,104,255,0.25)]'
                : 'p-5 bg-white/5 border-white/10 hover:bg-white/10',
            ]"
          >
            <div class="flex items-start gap-3">
              <span :class="scenario.hero ? 'text-3xl' : 'text-2xl'">{{ resolveIcon(scenario.icon) }}</span>
              <div>
                <h3 :class="scenario.hero ? 'text-base font-semibold text-white' : 'text-sm font-semibold text-white'">{{ scenario.name }}</h3>
                <p :class="scenario.hero ? 'text-sm text-white/50 mt-1.5' : 'text-xs text-white/50 mt-1'">{{ scenario.description }}</p>
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

    <!-- Capabilities -->
    <section class="px-4 md:px-6 py-14 md:py-20 bg-[var(--color-bg)]">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-xl md:text-2xl font-semibold text-[var(--color-text)] text-center mb-10 md:mb-14">What You Can Simulate</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
          <div class="flex gap-4">
            <div class="shrink-0 w-10 h-10 rounded-lg bg-[rgba(32,104,255,0.1)] flex items-center justify-center">
              <svg class="w-5 h-5 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" /></svg>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">Outbound Email Testing</h3>
              <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed">Test subject lines, messaging angles, and cadence sequences against hundreds of AI personas before sending a single real email.</p>
            </div>
          </div>
          <div class="flex gap-4">
            <div class="shrink-0 w-10 h-10 rounded-lg bg-[rgba(255,86,0,0.1)] flex items-center justify-center">
              <svg class="w-5 h-5 text-[#ff5600]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" /></svg>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">Signal Validation</h3>
              <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed">Test whether your sales signals actually predict buying behavior. Identify false positives before routing them to reps.</p>
            </div>
          </div>
          <div class="flex gap-4">
            <div class="shrink-0 w-10 h-10 rounded-lg bg-[rgba(170,0,255,0.1)] flex items-center justify-center">
              <svg class="w-5 h-5 text-[#A0F]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">Pricing Impact</h3>
              <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed">Predict churn risk, competitive switching, and sentiment before rolling out pricing changes to real customers.</p>
            </div>
          </div>
          <div class="flex gap-4">
            <div class="shrink-0 w-10 h-10 rounded-lg bg-[rgba(0,153,0,0.1)] flex items-center justify-center">
              <svg class="w-5 h-5 text-[#090]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" /></svg>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">Personalization Ranking</h3>
              <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed">Rank message variants by simulated engagement, not LLM self-assessment. Find the best tone, length, and CTA for each segment.</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Technology Stack -->
    <section class="px-4 md:px-6 py-14 md:py-20 bg-gradient-to-b from-[var(--color-bg)] to-[#f0f2f5]">
      <div class="max-w-4xl mx-auto text-center">
        <h2 class="text-xl md:text-2xl font-semibold text-[var(--color-text)] mb-3">Powered by Open-Source Intelligence</h2>
        <p class="text-sm text-[var(--color-text-secondary)] max-w-xl mx-auto mb-10">
          Built on battle-tested open-source foundations with enterprise-grade AI orchestration.
        </p>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-white border border-black/5 rounded-xl p-5 text-center">
            <div class="text-2xl mb-2">🐟</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">MiroFish</div>
            <div class="text-[10px] text-[var(--color-text-muted)] mt-1">Swarm Intelligence</div>
          </div>
          <div class="bg-white border border-black/5 rounded-xl p-5 text-center">
            <div class="text-2xl mb-2">🌐</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">OASIS</div>
            <div class="text-[10px] text-[var(--color-text-muted)] mt-1">1M Agent Simulation</div>
          </div>
          <div class="bg-white border border-black/5 rounded-xl p-5 text-center">
            <div class="text-2xl mb-2">🧠</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">Zep GraphRAG</div>
            <div class="text-[10px] text-[var(--color-text-muted)] mt-1">Knowledge Graphs</div>
          </div>
          <div class="bg-white border border-black/5 rounded-xl p-5 text-center">
            <div class="text-2xl mb-2">🤖</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">Multi-LLM</div>
            <div class="text-[10px] text-[var(--color-text-muted)] mt-1">Claude / GPT / Gemini</div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="bg-gradient-to-b from-[#050505] to-[#1a1a3e] text-white px-4 md:px-6 py-16 md:py-24">
      <div class="max-w-2xl mx-auto text-center">
        <h2 class="text-2xl md:text-3xl font-semibold mb-4">Stop guessing. Start simulating.</h2>
        <p class="text-sm md:text-base text-white/50 mb-8 max-w-lg mx-auto">
          Every campaign is a production deployment today. MiroFish gives you a staging environment for your GTM strategy.
        </p>
        <button
          @click="window.scrollTo({ top: 0, behavior: 'smooth' })"
          class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-semibold px-8 py-3.5 rounded-lg transition-colors"
        >
          Try a Scenario
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" /></svg>
        </button>
      </div>
    </section>
  </div>
</template>
