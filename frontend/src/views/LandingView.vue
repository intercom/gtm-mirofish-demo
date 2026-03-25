<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDemoMode } from '../composables/useDemoMode'
import { useCountUp } from '../composables/useCountUp'
import { useLocale } from '../composables/useLocale'
import { API_BASE } from '../api/client'
import HeroSwarm from '../components/landing/HeroSwarm.vue'

const router = useRouter()
const { isDemoMode } = useDemoMode()
const { formatCompactNumber } = useLocale()
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

const scenarioSection = ref(null)

function launchScenario(id) {
  router.push(`/scenarios/${id}`)
}

function scrollToScenarios() {
  const el = scenarioSection.value?.$el || scenarioSection.value
  el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

const statsBanner = ref(null)
const agentTarget = ref(0)
const actionTarget = ref(0)
const toolTarget = ref(0)
const platformTarget = ref(0)

const agentDisplay = useCountUp(agentTarget, { duration: 1200 })
const actionDisplay = useCountUp(actionTarget, { duration: 1200 })
const toolDisplay = useCountUp(toolTarget, { duration: 1200 })
const platformDisplay = useCountUp(platformTarget, { duration: 1200 })

let statsObserver = null

onMounted(() => {
  if (statsBanner.value) {
    statsObserver = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          agentTarget.value = 1000000
          actionTarget.value = 23
          toolTarget.value = 4
          platformTarget.value = 2
          statsObserver.disconnect()
        }
      },
      { threshold: 0.3 },
    )
    statsObserver.observe(statsBanner.value)
  }
})

onUnmounted(() => {
  statsObserver?.disconnect()
})

// FAQ accordion state
const openFaq = ref(null)
function toggleFaq(index) {
  openFaq.value = openFaq.value === index ? null : index
}

const faqs = [
  {
    q: 'How realistic are the AI agent personas?',
    a: 'Each agent is seeded with a unique demographic profile, company role, industry vertical, technology stack, and behavioral tendencies. Personas are generated from real-world ICP distributions, so the simulated population mirrors your actual target market segments.',
  },
  {
    q: 'How many agents can run in a single simulation?',
    a: 'The OASIS backbone supports up to 1 million concurrent agents. For most GTM scenarios, we recommend 500-5,000 agents to balance statistical significance with simulation speed. A typical outbound campaign test with 1,000 agents completes in under 10 minutes.',
  },
  {
    q: 'Can I use my own data to seed simulations?',
    a: 'Yes. You can upload campaign copy, email templates, pricing sheets, signal definitions, or any seed document. The system extracts context and generates a realistic simulation environment around your specific GTM motion.',
  },
  {
    q: 'What kind of reports does MiroFish generate?',
    a: 'Multi-chapter narrative reports covering engagement predictions, objection analysis, segment-specific sentiment, competitive positioning risk, and recommended optimizations. Reports include quantitative metrics alongside qualitative agent reasoning.',
  },
  {
    q: 'How is this different from traditional A/B testing?',
    a: 'Traditional A/B testing requires real traffic and takes weeks. MiroFish simulates outcomes in minutes with zero audience exposure. You get directional insights before spending a single dollar or risking brand reputation with a bad campaign.',
  },
  {
    q: 'Is the simulation deterministic?',
    a: 'No - agents have stochastic behavior patterns, so running the same scenario twice will yield slightly different results (like real markets). However, aggregate trends converge reliably. We recommend running 2-3 iterations for high-confidence insights.',
  },
]

const personas = [
  { emoji: '👩‍💼', role: 'VP of Engineering', company: 'Series B SaaS', trait: 'Skeptical of vendor claims' },
  { emoji: '👨‍💻', role: 'DevOps Lead', company: 'Enterprise Fintech', trait: 'Values technical depth' },
  { emoji: '👩‍🔬', role: 'Data Scientist', company: 'Healthcare AI', trait: 'Needs compliance proof' },
  { emoji: '🧑‍💼', role: 'Head of CS', company: 'PLG Startup', trait: 'Cost-conscious buyer' },
  { emoji: '👨‍🏫', role: 'CTO', company: 'Mid-Market Retail', trait: 'Integration-first mindset' },
  { emoji: '👩‍🎨', role: 'Product Manager', company: 'EdTech Scale-up', trait: 'UX-obsessed evaluator' },
]

const useCases = [
  {
    role: 'Sales Development',
    icon: '📞',
    color: '#2068FF',
    bg: 'rgba(32, 104, 255, 0.1)',
    items: [
      'Pre-test outbound sequences before sending',
      'Identify which signals correlate with replies',
      'Optimize subject lines by persona segment',
    ],
  },
  {
    role: 'Product Marketing',
    icon: '📣',
    color: '#ff5600',
    bg: 'rgba(255, 86, 0, 0.1)',
    items: [
      'Validate positioning against competitive alternatives',
      'Test launch messaging across buyer segments',
      'Predict objection patterns before enablement',
    ],
  },
  {
    role: 'Revenue Operations',
    icon: '⚙️',
    color: '#AA00FF',
    bg: 'rgba(170, 0, 255, 0.1)',
    items: [
      'Simulate pricing change impact on pipeline',
      'Model lead scoring accuracy with synthetic data',
      'Stress-test routing rules against edge cases',
    ],
  },
  {
    role: 'Growth & Demand Gen',
    icon: '📈',
    color: '#009900',
    bg: 'rgba(0, 153, 0, 0.1)',
    items: [
      'Rank content variants by predicted engagement',
      'Test nurture sequences on simulated cohorts',
      'Forecast campaign ROI before budget allocation',
    ],
  },
]

const pipelineSteps = [
  { label: 'Seed Document', sub: 'Campaign copy, signals, pricing', icon: '📄', color: '#2068FF' },
  { label: 'Persona Generation', sub: 'ICP-matched agent population', icon: '👥', color: '#ff5600' },
  { label: 'Swarm Simulation', sub: 'Multi-platform interactions', icon: '🐟', color: '#AA00FF' },
  { label: 'Graph Analysis', sub: 'Network effects & influence', icon: '🕸️', color: '#009900' },
  { label: 'Predictive Report', sub: 'Actionable GTM insights', icon: '📊', color: '#2068FF' },
]

const year = new Date().getFullYear()
</script>

<template>
  <div>
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 1. HERO SECTION                                                    -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section class="relative overflow-hidden bg-gradient-to-b from-[#050505] to-[#1a1a3e] text-white px-4 md:px-6 py-12 md:py-32">
      <HeroSwarm />
      <div class="relative max-w-4xl mx-auto text-center">
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

        <!-- Error State -->
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
          ref="scenarioSection"
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

          <!-- Custom simulation card -->
          <button
            v-if="showCards && scenarios.length"
            key="custom"
            :data-index="scenarios.length"
            @click="launchScenario('custom')"
            class="text-left rounded-lg transition-all duration-300 cursor-pointer border p-5 border-dashed border-white/20 hover:bg-white/10 hover:border-white/30 group"
          >
            <div class="flex items-start gap-3">
              <span class="text-2xl opacity-60 group-hover:opacity-100 transition-opacity">
                <svg class="w-6 h-6 text-white/50 group-hover:text-[#2068FF] transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
              </span>
              <div>
                <h3 class="text-sm font-semibold text-white/80 group-hover:text-white transition-colors">Custom Simulation</h3>
                <p class="text-xs text-white/40 mt-1">Bring your own seed document and configure a simulation from scratch.</p>
              </div>
            </div>
          </button>
        </TransitionGroup>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 2. SOCIAL PROOF BAR                                                -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section class="bg-[#050505] border-t border-b border-white/5 px-4 md:px-6 py-6">
      <div class="max-w-5xl mx-auto">
        <p class="text-[10px] uppercase tracking-[2px] text-white/30 text-center mb-4">Built for GTM teams who ship</p>
        <div class="flex flex-wrap justify-center gap-3 md:gap-4">
          <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-white/50">
            <span class="w-1.5 h-1.5 rounded-full bg-[#2068FF]"></span> Sales Development
          </span>
          <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-white/50">
            <span class="w-1.5 h-1.5 rounded-full bg-[#ff5600]"></span> Product Marketing
          </span>
          <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-white/50">
            <span class="w-1.5 h-1.5 rounded-full bg-[#AA00FF]"></span> Revenue Operations
          </span>
          <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-white/50">
            <span class="w-1.5 h-1.5 rounded-full bg-[#009900]"></span> Growth & Demand Gen
          </span>
          <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-white/50">
            <span class="w-1.5 h-1.5 rounded-full bg-[#f59e0b]"></span> Pricing & Packaging
          </span>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 3. HOW IT WORKS                                                    -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
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

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 4. STATS BANNER                                                    -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section ref="statsBanner" class="bg-[#050505] text-white px-4 md:px-6 py-8 md:py-10">
      <div class="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 text-center">
        <div>
          <div class="text-2xl font-semibold text-[#2068FF]">{{ formatCompactNumber(agentDisplay) }}</div>
          <div class="text-xs text-white/40 mt-1">Max Agents</div>
        </div>
        <div>
          <div class="text-2xl font-semibold text-[#ff5600]">{{ actionDisplay > 0 ? `${actionDisplay}` : '0' }}</div>
          <div class="text-xs text-white/40 mt-1">Action Types</div>
        </div>
        <div>
          <div class="text-2xl font-semibold text-[#A0F]">{{ toolDisplay > 0 ? `${toolDisplay}` : '0' }}</div>
          <div class="text-xs text-white/40 mt-1">Analysis Tools</div>
        </div>
        <div>
          <div class="text-2xl font-semibold text-[#090]">{{ platformDisplay > 0 ? `${platformDisplay}` : '0' }}</div>
          <div class="text-xs text-white/40 mt-1">Platforms</div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 5. AGENT PERSONAS                                                  -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section class="px-4 md:px-6 py-14 md:py-20 bg-[var(--color-bg)]">
      <div class="max-w-5xl mx-auto">
        <div class="text-center mb-10 md:mb-14">
          <h2 class="text-xl md:text-2xl font-semibold text-[var(--color-text)] mb-3">Meet the Swarm</h2>
          <p class="text-sm text-[var(--color-text-secondary)] max-w-xl mx-auto">
            Every agent is a unique buyer persona with realistic demographics, motivations, and objection patterns drawn from your ICP.
          </p>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div
            v-for="persona in personas"
            :key="persona.role"
            class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 hover:shadow-md transition-shadow"
          >
            <div class="text-3xl mb-3">{{ persona.emoji }}</div>
            <h3 class="text-sm font-semibold text-[var(--color-text)]">{{ persona.role }}</h3>
            <p class="text-[11px] text-[var(--color-text-muted)] mt-0.5">{{ persona.company }}</p>
            <p class="text-xs text-[var(--color-text-secondary)] mt-2 italic">"{{ persona.trait }}"</p>
          </div>
        </div>
        <p class="text-center text-xs text-[var(--color-text-muted)] mt-6">
          + thousands more generated from your ICP distribution
        </p>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 6. CAPABILITIES                                                    -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section class="px-4 md:px-6 py-14 md:py-20 bg-gradient-to-b from-[var(--color-bg)] to-[var(--color-bg-alt)]">
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

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 7. BEFORE / AFTER COMPARISON                                       -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section class="bg-[#050505] text-white px-4 md:px-6 py-14 md:py-20">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-xl md:text-2xl font-semibold text-center mb-3">Traditional Testing vs. Swarm Simulation</h2>
        <p class="text-sm text-white/50 text-center max-w-xl mx-auto mb-10">
          Stop waiting weeks for statistical significance. Get directional insights in minutes.
        </p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Traditional -->
          <div class="rounded-xl border border-white/10 bg-white/5 p-6 md:p-8">
            <div class="flex items-center gap-2 mb-6">
              <div class="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center">
                <svg class="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
              </div>
              <h3 class="text-sm font-semibold">Traditional A/B Testing</h3>
            </div>
            <ul class="space-y-3">
              <li class="flex items-start gap-2.5 text-xs text-white/50">
                <svg class="w-4 h-4 text-red-400/60 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                Weeks to reach statistical significance
              </li>
              <li class="flex items-start gap-2.5 text-xs text-white/50">
                <svg class="w-4 h-4 text-red-400/60 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 18.72a9.094 9.094 0 0 0 3.741-.479 3 3 0 0 0-4.682-2.72m.94 3.198.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0 1 12 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 0 1 6 18.719m12 0a5.971 5.971 0 0 0-.941-3.197m0 0A5.995 5.995 0 0 0 12 12.75a5.995 5.995 0 0 0-5.058 2.772m0 0a3 3 0 0 0-4.681 2.72 8.986 8.986 0 0 0 3.74.477m.94-3.197a5.971 5.971 0 0 0-.94 3.197M15 6.75a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm6 3a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Zm-13.5 0a2.25 2.25 0 1 1-4.5 0 2.25 2.25 0 0 1 4.5 0Z" /></svg>
                Requires real audience exposure
              </li>
              <li class="flex items-start gap-2.5 text-xs text-white/50">
                <svg class="w-4 h-4 text-red-400/60 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5" /></svg>
                Limited to 2-3 variants at a time
              </li>
              <li class="flex items-start gap-2.5 text-xs text-white/50">
                <svg class="w-4 h-4 text-red-400/60 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z" /></svg>
                Risk of brand damage from bad variants
              </li>
              <li class="flex items-start gap-2.5 text-xs text-white/50">
                <svg class="w-4 h-4 text-red-400/60 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                No insight into <em>why</em> variants win or lose
              </li>
            </ul>
          </div>
          <!-- Swarm -->
          <div class="rounded-xl border border-[rgba(32,104,255,0.3)] bg-[rgba(32,104,255,0.08)] p-6 md:p-8">
            <div class="flex items-center gap-2 mb-6">
              <div class="w-8 h-8 rounded-full bg-[rgba(32,104,255,0.2)] flex items-center justify-center">
                <span class="text-sm">🐟</span>
              </div>
              <h3 class="text-sm font-semibold">MiroFish Swarm Simulation</h3>
            </div>
            <ul class="space-y-3">
              <li class="flex items-start gap-2.5 text-xs text-white/70">
                <svg class="w-4 h-4 text-[#2068FF] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
                Results in minutes, not weeks
              </li>
              <li class="flex items-start gap-2.5 text-xs text-white/70">
                <svg class="w-4 h-4 text-[#2068FF] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
                Zero real audience exposure required
              </li>
              <li class="flex items-start gap-2.5 text-xs text-white/70">
                <svg class="w-4 h-4 text-[#2068FF] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
                Test unlimited variants simultaneously
              </li>
              <li class="flex items-start gap-2.5 text-xs text-white/70">
                <svg class="w-4 h-4 text-[#2068FF] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
                Safe sandbox — no brand risk
              </li>
              <li class="flex items-start gap-2.5 text-xs text-white/70">
                <svg class="w-4 h-4 text-[#2068FF] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
                Agents explain their reasoning in natural language
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 8. SIMULATION PIPELINE                                             -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section class="px-4 md:px-6 py-14 md:py-20 bg-[var(--color-bg)]">
      <div class="max-w-5xl mx-auto">
        <div class="text-center mb-10 md:mb-14">
          <h2 class="text-xl md:text-2xl font-semibold text-[var(--color-text)] mb-3">The Simulation Pipeline</h2>
          <p class="text-sm text-[var(--color-text-secondary)] max-w-xl mx-auto">
            From raw campaign input to actionable intelligence in five automated stages.
          </p>
        </div>
        <div class="flex flex-col md:flex-row items-stretch gap-3 md:gap-0">
          <div
            v-for="(step, i) in pipelineSteps"
            :key="step.label"
            class="flex-1 relative"
          >
            <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 text-center h-full">
              <div
                class="w-10 h-10 rounded-full mx-auto mb-3 flex items-center justify-center text-lg"
                :style="{ backgroundColor: step.color + '15' }"
              >
                {{ step.icon }}
              </div>
              <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">{{ step.label }}</h3>
              <p class="text-[11px] text-[var(--color-text-muted)]">{{ step.sub }}</p>
            </div>
            <!-- Connector arrow (hidden on last item and mobile) -->
            <div
              v-if="i < pipelineSteps.length - 1"
              class="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-[var(--color-bg)] border border-[var(--color-border)] items-center justify-center"
            >
              <svg class="w-3 h-3 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
            </div>
            <!-- Mobile down-arrow connector -->
            <div
              v-if="i < pipelineSteps.length - 1"
              class="md:hidden flex justify-center py-1"
            >
              <svg class="w-4 h-4 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 9. TECHNOLOGY STACK                                                -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section class="px-4 md:px-6 py-14 md:py-20 bg-gradient-to-b from-[var(--color-bg)] to-[var(--color-bg-alt)]">
      <div class="max-w-4xl mx-auto text-center">
        <h2 class="text-xl md:text-2xl font-semibold text-[var(--color-text)] mb-3">Powered by Open-Source Intelligence</h2>
        <p class="text-sm text-[var(--color-text-secondary)] max-w-xl mx-auto mb-10">
          Built on battle-tested open-source foundations with enterprise-grade AI orchestration.
        </p>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 text-center">
            <div class="text-2xl mb-2">🐟</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">MiroFish</div>
            <div class="text-[10px] text-[var(--color-text-muted)] mt-1">Swarm Intelligence</div>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 text-center">
            <div class="text-2xl mb-2">🌐</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">OASIS</div>
            <div class="text-[10px] text-[var(--color-text-muted)] mt-1">1M Agent Simulation</div>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 text-center">
            <div class="text-2xl mb-2">🧠</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">Zep GraphRAG</div>
            <div class="text-[10px] text-[var(--color-text-muted)] mt-1">Knowledge Graphs</div>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 text-center">
            <div class="text-2xl mb-2">🤖</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">Multi-LLM</div>
            <div class="text-[10px] text-[var(--color-text-muted)] mt-1">Claude / GPT / Gemini</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 10. USE CASES BY ROLE                                              -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section class="bg-[#050505] text-white px-4 md:px-6 py-14 md:py-20">
      <div class="max-w-5xl mx-auto">
        <div class="text-center mb-10 md:mb-14">
          <h2 class="text-xl md:text-2xl font-semibold mb-3">Built for Every GTM Role</h2>
          <p class="text-sm text-white/50 max-w-xl mx-auto">
            Whether you're writing sequences, setting pricing, or building pipeline models, MiroFish adapts to your workflow.
          </p>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div
            v-for="uc in useCases"
            :key="uc.role"
            class="rounded-xl border border-white/10 bg-white/5 p-6"
          >
            <div class="flex items-center gap-3 mb-4">
              <div
                class="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                :style="{ backgroundColor: uc.bg }"
              >
                {{ uc.icon }}
              </div>
              <h3 class="text-sm font-semibold" :style="{ color: uc.color }">{{ uc.role }}</h3>
            </div>
            <ul class="space-y-2">
              <li
                v-for="item in uc.items"
                :key="item"
                class="flex items-start gap-2 text-xs text-white/60"
              >
                <svg class="w-3.5 h-3.5 shrink-0 mt-0.5" :style="{ color: uc.color }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
                {{ item }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 11. SAMPLE REPORT PREVIEW                                          -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section class="px-4 md:px-6 py-14 md:py-20 bg-[var(--color-bg)]">
      <div class="max-w-5xl mx-auto">
        <div class="text-center mb-10 md:mb-14">
          <h2 class="text-xl md:text-2xl font-semibold text-[var(--color-text)] mb-3">Reports That Actually Help</h2>
          <p class="text-sm text-[var(--color-text-secondary)] max-w-xl mx-auto">
            Every simulation produces a multi-chapter analysis with quantitative metrics and qualitative agent reasoning.
          </p>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl overflow-hidden shadow-lg">
          <!-- Mock report header -->
          <div class="bg-gradient-to-r from-[#050505] to-[#1a1a3e] px-6 py-4 flex items-center gap-3">
            <div class="flex gap-1.5">
              <div class="w-3 h-3 rounded-full bg-red-500/60"></div>
              <div class="w-3 h-3 rounded-full bg-yellow-500/60"></div>
              <div class="w-3 h-3 rounded-full bg-green-500/60"></div>
            </div>
            <span class="text-xs text-white/40 font-mono">simulation-report-outbound-q2.html</span>
          </div>
          <!-- Mock report content -->
          <div class="p-6 md:p-8 space-y-6">
            <div class="flex flex-wrap gap-4">
              <div class="flex-1 min-w-[140px] bg-[rgba(32,104,255,0.06)] border border-[rgba(32,104,255,0.15)] rounded-lg p-4">
                <div class="text-2xl font-semibold text-[#2068FF]">73%</div>
                <div class="text-[11px] text-[var(--color-text-muted)] mt-1">Predicted Open Rate</div>
              </div>
              <div class="flex-1 min-w-[140px] bg-[rgba(255,86,0,0.06)] border border-[rgba(255,86,0,0.15)] rounded-lg p-4">
                <div class="text-2xl font-semibold text-[#ff5600]">12.4%</div>
                <div class="text-[11px] text-[var(--color-text-muted)] mt-1">Reply Rate</div>
              </div>
              <div class="flex-1 min-w-[140px] bg-[rgba(170,0,255,0.06)] border border-[rgba(170,0,255,0.15)] rounded-lg p-4">
                <div class="text-2xl font-semibold text-[#AA00FF]">8</div>
                <div class="text-[11px] text-[var(--color-text-muted)] mt-1">Objections Found</div>
              </div>
              <div class="flex-1 min-w-[140px] bg-[rgba(0,153,0,0.06)] border border-[rgba(0,153,0,0.15)] rounded-lg p-4">
                <div class="text-2xl font-semibold text-[#009900]">3</div>
                <div class="text-[11px] text-[var(--color-text-muted)] mt-1">Top Segments</div>
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="bg-[var(--color-bg)] rounded-lg p-4">
                <h4 class="text-xs font-semibold text-[var(--color-text)] mb-2">Top Objection Themes</h4>
                <div class="space-y-2">
                  <div class="flex items-center gap-2">
                    <div class="h-2 rounded-full bg-[#2068FF]" style="width: 80%"></div>
                    <span class="text-[10px] text-[var(--color-text-muted)] whitespace-nowrap">Pricing concern</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <div class="h-2 rounded-full bg-[#ff5600]" style="width: 60%"></div>
                    <span class="text-[10px] text-[var(--color-text-muted)] whitespace-nowrap">Integration risk</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <div class="h-2 rounded-full bg-[#AA00FF]" style="width: 35%"></div>
                    <span class="text-[10px] text-[var(--color-text-muted)] whitespace-nowrap">Competitor lock-in</span>
                  </div>
                </div>
              </div>
              <div class="bg-[var(--color-bg)] rounded-lg p-4">
                <h4 class="text-xs font-semibold text-[var(--color-text)] mb-2">Segment Performance</h4>
                <div class="space-y-2">
                  <div class="flex justify-between items-center">
                    <span class="text-[11px] text-[var(--color-text-secondary)]">Enterprise (1k+ emp)</span>
                    <span class="text-[11px] font-semibold text-[#009900]">High engagement</span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-[11px] text-[var(--color-text-secondary)]">Mid-Market (200-1k)</span>
                    <span class="text-[11px] font-semibold text-[#2068FF]">Medium engagement</span>
                  </div>
                  <div class="flex justify-between items-center">
                    <span class="text-[11px] text-[var(--color-text-secondary)]">SMB (&lt;200 emp)</span>
                    <span class="text-[11px] font-semibold text-[#ff5600]">Price sensitive</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 12. FAQ                                                            -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section class="px-4 md:px-6 py-14 md:py-20 bg-[var(--color-bg-alt)]">
      <div class="max-w-3xl mx-auto">
        <h2 class="text-xl md:text-2xl font-semibold text-[var(--color-text)] text-center mb-10">Frequently Asked Questions</h2>
        <div class="space-y-3">
          <div
            v-for="(faq, i) in faqs"
            :key="i"
            class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden"
          >
            <button
              @click="toggleFaq(i)"
              class="w-full flex items-center justify-between px-5 py-4 text-left cursor-pointer"
            >
              <span class="text-sm font-semibold text-[var(--color-text)] pr-4">{{ faq.q }}</span>
              <svg
                class="w-5 h-5 shrink-0 text-[var(--color-text-muted)] transition-transform duration-200"
                :class="{ 'rotate-180': openFaq === i }"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
            <Transition name="faq">
              <div v-if="openFaq === i" class="px-5 pb-4">
                <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed">{{ faq.a }}</p>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- 13. CTA                                                            -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section class="bg-gradient-to-b from-[#050505] to-[#1a1a3e] text-white px-4 md:px-6 py-16 md:py-24">
      <div class="max-w-2xl mx-auto text-center">
        <h2 class="text-2xl md:text-3xl font-semibold mb-4">Stop guessing. Start simulating.</h2>
        <p class="text-sm md:text-base text-white/50 mb-8 max-w-lg mx-auto">
          Every campaign is a production deployment today. MiroFish gives you a staging environment for your GTM strategy.
        </p>
        <button
          @click="scrollToScenarios"
          class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-semibold px-8 py-3.5 rounded-lg transition-colors cursor-pointer"
        >
          Try a Scenario
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" /></svg>
        </button>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- FOOTER                                                             -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <footer class="bg-[#050505] text-white border-t border-white/10">
      <!-- Main footer content -->
      <div class="max-w-5xl mx-auto px-4 md:px-6 py-12 md:py-16">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12">
          <!-- Brand column -->
          <div class="col-span-2 md:col-span-1">
            <div class="flex items-center gap-2 mb-4">
              <span class="text-xl">🐟</span>
              <span class="text-sm font-semibold">MiroFish</span>
            </div>
            <p class="text-xs text-white/40 leading-relaxed max-w-[200px]">
              Swarm intelligence for go-to-market teams. Predict outcomes before they happen.
            </p>
          </div>

          <!-- Product column -->
          <div>
            <h4 class="text-xs font-semibold uppercase tracking-[1.5px] text-white/50 mb-4">Product</h4>
            <ul class="space-y-2.5">
              <li><button @click="scrollToScenarios" class="text-xs text-white/40 hover:text-white transition-colors cursor-pointer">Scenarios</button></li>
              <li><router-link to="/simulations" class="text-xs text-white/40 hover:text-white transition-colors">Simulations</router-link></li>
              <li><router-link to="/settings" class="text-xs text-white/40 hover:text-white transition-colors">Settings</router-link></li>
            </ul>
          </div>

          <!-- Resources column -->
          <div>
            <h4 class="text-xs font-semibold uppercase tracking-[1.5px] text-white/50 mb-4">Resources</h4>
            <ul class="space-y-2.5">
              <li>
                <a href="https://github.com/666ghj/MiroFish" target="_blank" rel="noopener noreferrer" class="text-xs text-white/40 hover:text-white transition-colors">
                  MiroFish GitHub
                </a>
              </li>
              <li>
                <a href="https://arxiv.org/abs/2411.11581" target="_blank" rel="noopener noreferrer" class="text-xs text-white/40 hover:text-white transition-colors">
                  OASIS Paper
                </a>
              </li>
              <li>
                <a href="https://www.getzep.com/" target="_blank" rel="noopener noreferrer" class="text-xs text-white/40 hover:text-white transition-colors">
                  Zep GraphRAG
                </a>
              </li>
            </ul>
          </div>

          <!-- Technology column -->
          <div>
            <h4 class="text-xs font-semibold uppercase tracking-[1.5px] text-white/50 mb-4">Technology</h4>
            <ul class="space-y-2.5">
              <li><span class="text-xs text-white/40">Vue 3 + Vite</span></li>
              <li><span class="text-xs text-white/40">Flask + Python</span></li>
              <li><span class="text-xs text-white/40">D3.js Visualization</span></li>
              <li><span class="text-xs text-white/40">Multi-LLM Orchestration</span></li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Bottom bar -->
      <div class="border-t border-white/5 px-4 md:px-6 py-4">
        <div class="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-2">
          <p class="text-[11px] text-white/30">
            &copy; {{ year }} Intercom GTM Systems. Powered by
            <a href="https://github.com/666ghj/MiroFish" target="_blank" rel="noopener noreferrer" class="text-[#2068FF]/60 hover:text-[#2068FF] transition-colors">MiroFish</a>
            Swarm Intelligence.
          </p>
          <p class="text-[11px] text-white/20">
            Built with care by the GTM Engineering team
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.faq-enter-active,
.faq-leave-active {
  transition: max-height 0.2s ease, opacity 0.2s ease;
  overflow: hidden;
}
.faq-enter-from,
.faq-leave-to {
  max-height: 0;
  opacity: 0;
}
.faq-enter-to,
.faq-leave-from {
  max-height: 200px;
  opacity: 1;
}
</style>
