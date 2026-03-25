<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'
import { useToast } from '../composables/useToast'
import { useScenariosStore } from '../stores/scenarios'
import { useSimulationStore } from '../stores/simulation'
import { graphApi } from '../api/graph'

const props = defineProps({ id: String })
const router = useRouter()
const route = useRoute()
const toast = useToast()
const scenariosStore = useScenariosStore()
const simulationStore = useSimulationStore()

const isRerun = computed(() => route.query.rerun === 'true')

const scenario = ref(null)
const loading = ref(true)
const error = ref(null)
const seedText = ref('')
const statusMessage = ref('')
const agentCount = ref(200)
const selectedPersonas = ref([])
const selectedIndustries = ref([])
const duration = ref(72)
const platformMode = ref('parallel')
const running = ref(false)
const activeTab = ref('seed')

const selectedCompanySizes = ref([])
const selectedRegions = ref([])
const minutesPerRound = ref(30)
const showAdvanced = ref(false)

const isCustom = computed(() => props.id === 'custom')

const canRun = computed(() =>
  seedText.value.trim().length > 0 && selectedPersonas.value.length > 0 && !running.value,
)

const scenarioTemplates = [
  {
    name: 'Competitive Displacement Campaign',
    description: 'Target customers of a specific competitor with switching messaging.',
    seedText: `Subject: Why leading support teams are switching from Zendesk to Intercom

Hi {{first_name}},

Your team at {{company}} currently relies on Zendesk for customer support — and while it served you well in the past, the landscape has shifted. Modern CX teams need more than a ticketing system: they need a unified, AI-first platform that handles support, engagement, and proactive outreach in one place.

Here's what teams like yours are telling us after switching:

- Resolution times dropped by 40% within the first quarter thanks to Fin AI Agent handling routine inquiries end-to-end, not just deflecting them.
- Agent onboarding went from weeks to days because Intercom's interface is built for speed, not buried in admin menus and legacy workflows.
- Consolidation savings averaged $45K/year by eliminating bolt-on tools for live chat, knowledge base, and outbound messaging that Zendesk charges separately for.

We're not asking you to take our word for it. We've prepared a personalized migration analysis for {{company}} based on your current plan and team size. It shows exactly what changes on day one, what the timeline looks like, and where the cost savings land.

Would you be open to a 20-minute walkthrough this week? No pressure — just data.

Best,
The Intercom GTM Team`,
    personas: ['VP of Support', 'CX Director', 'IT Leader', 'Technical Evaluator'],
    industries: ['SaaS', 'Healthcare', 'Fintech'],
    agentCount: 250,
  },
  {
    name: 'Product Launch Announcement',
    description: 'Announce a new product or feature to your existing customer base.',
    seedText: `Subject: Introducing Intercom Workflows 2.0 — automation that actually feels personal

Hi {{first_name}},

Today we're launching Workflows 2.0, the biggest update to Intercom's automation engine since we first introduced Workflows three years ago. This isn't an incremental improvement — it's a complete rethink of how automation should work for modern support and sales teams.

What's new:

1. Natural Language Workflow Builder — Describe what you want in plain English ("When a VIP customer submits a billing question after hours, route to the finance team and send a personalized acknowledgment") and Workflows 2.0 builds it for you. No drag-and-drop flowcharts, no conditional logic trees to debug.

2. Cross-Channel Orchestration — A single workflow can now span email, in-app messenger, SMS, and Slack without duplicating logic. A customer who starts in chat and follows up via email stays in the same conversation thread, with full context preserved.

3. Real-Time Performance Dashboard — Every workflow now comes with built-in analytics showing trigger rates, completion rates, drop-off points, and estimated time saved. You'll know within hours whether a new workflow is working, not weeks.

We're rolling this out to all Pro and Premium plans starting today, with a guided migration path for teams currently using legacy workflows. Your existing automations will continue to work — but we think you'll want to rebuild them once you see what's possible.

Check out the launch post and interactive demo at intercom.com/workflows-2.

Best,
The Intercom Product Team`,
    personas: ['Product Manager', 'End User', 'Champion', 'Technical Evaluator'],
    industries: ['SaaS', 'E-commerce', 'Fintech'],
    agentCount: 200,
  },
  {
    name: 'Expansion / Upsell Motion',
    description: 'Upsell existing customers to a higher tier or additional products.',
    seedText: `Subject: {{company}} is outgrowing your current Intercom plan — here's what's next

Hi {{first_name}},

Over the past six months, {{company}} has grown significantly on Intercom. Your team is handling 3x the conversation volume you had when you started on the Essential plan, and your support org has expanded from 5 to 18 agents. That's great news — it means your business is scaling.

But we've also noticed some friction points that suggest your current plan is holding you back:

- Your team is manually routing 60% of conversations because Essential doesn't include skills-based routing or round-robin assignment. That's roughly 12 hours per week of admin work that could be automated.
- You've hit the 5-workflow limit three times this quarter, and your team has been consolidating workflows into overly complex chains to stay under the cap. That creates fragility — one change breaks multiple automations.
- Three of your agents are using personal Slack channels to coordinate on complex tickets because Essential doesn't include team inboxes or internal notes threading.

The Advanced plan unlocks all of this for an incremental $2,400/year at your current seat count. That breaks down to roughly $11 per agent per month — less than the cost of the manual routing time alone.

We've put together a custom upgrade analysis for {{company}} that shows the projected time savings and ROI. It includes a 30-day rollback guarantee: if your team doesn't see measurable improvement in the first month, we'll revert your plan and refund the difference.

Can we set up 15 minutes to walk through the numbers?

Best,
Your Intercom Account Team`,
    personas: ['CFO', 'VP Operations', 'Decision Maker', 'Champion'],
    industries: ['SaaS', 'Healthcare', 'E-commerce', 'Manufacturing'],
    agentCount: 180,
  },
  {
    name: 'Win-back / Churn Prevention',
    description: 'Re-engage churned or at-risk customers before they leave.',
    seedText: `Subject: We heard you — here's what's changed at Intercom since you left

Hi {{first_name}},

It's been about four months since {{company}} moved off Intercom, and we wanted to reach out — not with a generic "we miss you" email, but with specifics about what's changed since your team made that decision.

When you left, your main concerns were:

1. Pricing complexity — Your bill was unpredictable because charges scaled with conversation volume and you couldn't forecast costs month to month. We've since moved to flat per-seat pricing with unlimited conversations included. No overages, no surprises. For a team your size, that would be $890/month flat.

2. Fin AI wasn't ready — At the time, Fin could only answer questions from your help center articles and struggled with anything that required account context. Since then, Fin has shipped three major updates: it can now pull live data from your CRM, execute actions like issuing refunds or updating subscriptions, and handles multi-turn troubleshooting flows. Customer-reported accuracy is at 94%.

3. Reporting gaps — Your ops team needed custom metrics that our reporting couldn't support. We've launched Custom Reports with a SQL-like query builder, scheduled exports to your data warehouse, and pre-built templates for the exact metrics you asked about (first-response time by segment, resolution rate by topic, agent utilization by shift).

We know switching platforms is a significant decision, and we're not asking for a commitment. But we'd love to give {{company}} a free 30-day pilot on the plan that matches your current team size so you can evaluate the changes firsthand.

Would it be worth a conversation?

Best,
The Intercom Win-back Team`,
    personas: ['CX Leader', 'Support Manager', 'Decision Maker', 'VP of Support'],
    industries: ['SaaS', 'Healthcare', 'Fintech', 'E-commerce'],
    agentCount: 200,
  },
]

function applyTemplate(template) {
  seedText.value = template.seedText
  selectedPersonas.value = [...template.personas]
  selectedIndustries.value = [...template.industries]
  agentCount.value = template.agentCount
}

function toggleCompanySize(size) {
  const idx = selectedCompanySizes.value.indexOf(size)
  if (idx === -1) selectedCompanySizes.value.push(size)
  else selectedCompanySizes.value.splice(idx, 1)
}

function toggleRegion(region) {
  const idx = selectedRegions.value.indexOf(region)
  if (idx === -1) selectedRegions.value.push(region)
  else selectedRegions.value.splice(idx, 1)
}


async function loadScenario() {
  loading.value = true
  error.value = null
  try {
    if (props.id === 'custom') {
      scenario.value = {
        id: 'custom',
        name: 'Custom Simulation',
        description: 'Configure your own simulation from scratch — paste any seed document and select your parameters.',
        icon: '+',
        agent_config: {
          count: 200,
          persona_types: [
            'VP of Support', 'CX Director', 'IT Leader', 'Head of Operations',
            'CFO', 'VP Operations', 'CX Leader', 'Product Manager', 'Support Manager',
            'Decision Maker', 'Champion', 'Technical Evaluator', 'Blocker', 'End User',
          ],
          firmographic_mix: {
            industries: ['SaaS', 'Healthcare', 'Fintech', 'E-commerce', 'Manufacturing'],
            company_sizes: ['50-200', '200-500', '500-1000', '1000-2000', '1000-5000'],
            regions: ['North America', 'EMEA', 'APAC', 'LATAM'],
          },
        },
        simulation_config: {
          total_hours: 72,
          minutes_per_round: 30,
          platform_mode: 'parallel',
        },
      }
      seedText.value = ''
      agentCount.value = 200
      duration.value = 72
      platformMode.value = 'parallel'
      selectedPersonas.value = []
      selectedIndustries.value = []
    } else {
      const data = await scenariosStore.fetchScenarioById(props.id)
      if (!data) throw new Error('Scenario not found')
      scenario.value = data

      seedText.value = data.seed_text || ''
      agentCount.value = data.agent_config?.count || 200
      duration.value = data.simulation_config?.total_hours || 72
      platformMode.value = data.simulation_config?.platform_mode || 'parallel'
      selectedPersonas.value = [...(data.agent_config?.persona_types || [])]
      selectedIndustries.value = [...(data.agent_config?.firmographic_mix?.industries || [])]
    }
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadScenario()
  if (route.query.rerun === 'true') {
    if (route.query.seedText) seedText.value = route.query.seedText
    if (route.query.agentCount) agentCount.value = Number(route.query.agentCount)
    if (route.query.duration) duration.value = Number(route.query.duration)
    if (route.query.platformMode) platformMode.value = route.query.platformMode
    if (route.query.personas) {
      try { selectedPersonas.value = JSON.parse(route.query.personas) } catch {}
    }
    if (route.query.industries) {
      try { selectedIndustries.value = JSON.parse(route.query.industries) } catch {}
    }
  }
})


function togglePersona(persona) {
  const idx = selectedPersonas.value.indexOf(persona)
  if (idx === -1) {
    selectedPersonas.value.push(persona)
  } else {
    selectedPersonas.value.splice(idx, 1)
  }
}

function toggleIndustry(industry) {
  const idx = selectedIndustries.value.indexOf(industry)
  if (idx === -1) {
    selectedIndustries.value.push(industry)
  } else {
    selectedIndustries.value.splice(idx, 1)
  }
}

async function runSimulation() {
  if (running.value || !seedText.value) return
  running.value = true
  error.value = ''

  try {
    const { data } = await graphApi.build({
      seed_text: seedText.value,
      agent_count: agentCount.value,
      persona_types: selectedPersonas.value,
      industries: selectedIndustries.value,
      company_sizes: selectedCompanySizes.value,
      regions: selectedRegions.value,
      duration_hours: duration.value,
      minutes_per_round: minutesPerRound.value,
      platform_mode: platformMode.value,
    })
    const taskId = data.task_id
    simulationStore.setScenarioConfig({
      scenarioId: props.id,
      scenarioName: scenario.value?.name || (props.id === 'custom' ? 'Custom Simulation' : 'Untitled Scenario'),
      seedText: seedText.value,
      agentCount: agentCount.value,
      personas: selectedPersonas.value,
      industries: selectedIndustries.value,
      companySizes: selectedCompanySizes.value,
      regions: selectedRegions.value,
      duration: duration.value,
      minutesPerRound: minutesPerRound.value,
      platformMode: platformMode.value,
    })
    simulationStore.startGraphBuild(taskId)
    simulationStore.addSessionRun({
      id: taskId,
      scenarioId: props.id,
      scenarioName: scenario.value?.name || 'Untitled Scenario',
      status: 'building_graph',
    })
    toast.success('Building knowledge graph...')
    router.push(`/workspace/${taskId}`)
  } catch (e) {
    error.value = e.message
    toast.error(`Failed to start simulation: ${e.message}`)
  } finally {
    running.value = false
    statusMessage.value = ''
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <LoadingSpinner v-if="loading" label="Loading scenario..." />

    <ErrorState
      v-else-if="error"
      title="Failed to load scenario"
      :message="error"
      @retry="loadScenario"
    />

    <div v-else-if="scenario">
      <!-- Header -->
      <router-link to="/" class="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors mb-4 inline-block">&larr; Back to scenarios</router-link>

      <div
        v-if="isRerun"
        class="flex items-center gap-2 mb-4 px-4 py-2.5 rounded-lg border border-[#2068FF]/20 bg-[rgba(32,104,255,0.05)] text-sm text-[#2068FF]"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
        </svg>
        <span>Re-running from previous simulation.</span>
        <router-link to="/simulations" class="font-medium hover:underline no-underline text-[#2068FF]">Back to Simulations</router-link>
      </div>

      <h1 class="text-2xl md:text-3xl font-semibold text-[var(--color-text)] mb-2">{{ scenario.name }}</h1>
      <p class="text-sm text-[var(--color-text-secondary)] mb-6 md:mb-8">{{ scenario.description }}</p>

      <!-- Mobile: tab switcher -->
      <div class="md:hidden flex gap-2 mb-4">
        <button
          @click="activeTab = 'seed'"
          class="flex-1 py-2 text-sm font-medium rounded-lg transition-colors"
          :class="activeTab === 'seed' ? 'bg-[#2068FF] text-white' : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)]'"
        >
          Seed Document
        </button>
        <button
          @click="activeTab = 'config'"
          class="flex-1 py-2 text-sm font-medium rounded-lg transition-colors"
          :class="activeTab === 'config' ? 'bg-[#2068FF] text-white' : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)]'"
        >
          Configuration
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Seed Document (left 2/3) -->
        <div class="lg:col-span-2" :class="{ 'hidden md:block': activeTab !== 'seed' }">
          <!-- Template Selector (custom scenario only) -->
          <div v-if="isCustom" class="mb-6">
            <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-3">Start from a template</label>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                v-for="template in scenarioTemplates"
                :key="template.name"
                @click="applyTemplate(template)"
                class="text-left p-3.5 rounded-lg border card-interactive group"
                :class="seedText === template.seedText
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
                  : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)]'"
              >
                <span class="block text-sm font-semibold text-[var(--color-text)] mb-1">{{ template.name }}</span>
                <span class="block text-xs text-[var(--color-text-muted)] leading-relaxed mb-2">{{ template.description }}</span>
                <span
                  class="text-xs font-medium transition-colors"
                  :class="seedText === template.seedText
                    ? 'text-[var(--color-primary)]'
                    : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-primary)]'"
                >
                  {{ seedText === template.seedText ? 'Applied' : 'Use template' }} &rarr;
                </span>
              </button>
            </div>
          </div>

          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Seed Document</label>
          <textarea
            v-model="seedText"
            rows="16"
            class="w-full border border-[var(--color-border)] rounded-lg p-3 md:p-4 text-sm leading-relaxed focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent resize-y bg-[var(--color-surface)]"
            placeholder="Describe your scenario: What campaign are you testing? What messaging will prospects see? Include email copy, target audience details, and any competitive context. The more realistic the seed document, the more useful the simulation results will be."
          ></textarea>

          <!-- Persona Types Multiselect -->
          <div v-if="scenario.agent_config?.persona_types?.length" class="mt-6">
            <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-3">Persona Types</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="persona in scenario.agent_config.persona_types"
                :key="persona"
                @click="togglePersona(persona)"
                class="px-3 py-1.5 text-xs rounded-full border transition-colors"
                :class="selectedPersonas.includes(persona)
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
              >
                {{ persona }}
              </button>
            </div>
          </div>

          <!-- Industry Mix Checkboxes -->
          <div v-if="scenario.agent_config?.firmographic_mix?.industries?.length" class="mt-6">
            <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-3">Industry Mix</label>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <label
                v-for="industry in scenario.agent_config.firmographic_mix.industries"
                :key="industry"
                class="flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer transition-colors text-sm"
                :class="selectedIndustries.includes(industry)
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
                  : 'border-[var(--color-border)] hover:border-[var(--color-primary)]'"
              >
                <input
                  type="checkbox"
                  :checked="selectedIndustries.includes(industry)"
                  @change="toggleIndustry(industry)"
                  class="accent-[var(--color-primary)]"
                />
                <span :class="selectedIndustries.includes(industry) ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-secondary)]'">{{ industry }}</span>
              </label>
            </div>
          </div>

          <!-- Advanced Options (collapsible) -->
          <div class="mt-6">
            <button
              @click="showAdvanced = !showAdvanced"
              class="flex items-center gap-2 text-xs uppercase tracking-wider text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors"
            >
              <svg
                class="w-3.5 h-3.5 transition-transform"
                :class="{ 'rotate-90': showAdvanced }"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
              Advanced Options
            </button>

            <div v-show="showAdvanced" class="mt-4 space-y-5">
              <!-- Company Sizes -->
              <div v-if="scenario.agent_config?.firmographic_mix?.company_sizes?.length">
                <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-3">Company Size</label>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="size in scenario.agent_config.firmographic_mix.company_sizes"
                    :key="size"
                    @click="toggleCompanySize(size)"
                    class="px-3 py-1.5 text-xs rounded-full border transition-colors"
                    :class="selectedCompanySizes.includes(size)
                      ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                      : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
                  >
                    {{ size }} employees
                  </button>
                </div>
              </div>

              <!-- Regions -->
              <div v-if="scenario.agent_config?.firmographic_mix?.regions?.length">
                <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-3">Regions</label>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="region in scenario.agent_config.firmographic_mix.regions"
                    :key="region"
                    @click="toggleRegion(region)"
                    class="px-3 py-1.5 text-xs rounded-full border transition-colors"
                    :class="selectedRegions.includes(region)
                      ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                      : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
                  >
                    {{ region }}
                  </button>
                </div>
              </div>

              <!-- Minutes per Round -->
              <div>
                <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Minutes per Round</label>
                <div class="flex gap-2">
                  <button
                    v-for="mins in [15, 30, 60]"
                    :key="mins"
                    @click="minutesPerRound = mins"
                    class="flex-1 px-3 py-2 text-xs rounded-lg border transition-colors"
                    :class="minutesPerRound === mins
                      ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                      : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
                  >
                    {{ mins }}m
                  </button>
                </div>
                <p class="text-[10px] text-[var(--color-text-muted)] mt-1.5">
                  {{ duration }}h at {{ minutesPerRound }}m/round = {{ Math.ceil(duration * 60 / minutesPerRound) }} rounds
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Config Panel (right 1/3) -->
        <div class="space-y-6" :class="{ 'hidden md:block': activeTab !== 'config' }">
          <div>
            <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Agent Count</label>
            <input
              type="range"
              v-model.number="agentCount"
              min="50"
              max="500"
              step="10"
              class="w-full accent-[var(--color-primary)]"
            />
            <div class="text-center text-2xl font-semibold text-[var(--color-primary)]">{{ agentCount }}</div>
          </div>

          <!-- Simulation Duration -->
          <div>
            <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Duration</label>
            <div class="flex gap-2">
              <button
                v-for="hours in [24, 48, 72]"
                :key="hours"
                @click="duration = hours"
                class="flex-1 px-3 py-2 text-xs rounded-lg border transition-colors"
                :class="duration === hours
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
              >
                {{ hours }}h
              </button>
            </div>
          </div>

          <!-- Platform Mode Toggle -->
          <div>
            <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Platform</label>
            <div class="flex gap-2">
              <button
                v-for="mode in ['twitter', 'reddit', 'parallel']"
                :key="mode"
                @click="platformMode = mode"
                class="flex-1 px-3 py-2 text-xs rounded-lg border transition-colors capitalize"
                :class="platformMode === mode
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
              >
                {{ mode === 'parallel' ? 'Both' : mode }}
              </button>
            </div>
          </div>

          <!-- Error display -->
          <div v-if="error" class="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-lg p-3">
            {{ error }}
          </div>

          <!-- Status display -->
          <div v-if="statusMessage" class="text-xs text-[var(--color-primary)] bg-[rgba(32,104,255,0.05)] border border-[var(--color-primary)]/20 rounded-lg p-3">
            {{ statusMessage }}
          </div>

          <!-- Run Simulation Button -->
          <button
            @click="runSimulation"
            :disabled="!canRun"
            class="w-full bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] disabled:opacity-50 text-white font-semibold py-3 rounded-lg transition-colors mt-4"
          >
            {{ running ? 'Starting...' : 'Run Simulation' }}
          </button>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-20">
      <p class="text-[var(--color-text-muted)]">Scenario not found</p>
      <router-link to="/" class="text-[var(--color-primary)] text-sm mt-2 inline-block hover:underline">Back to Home</router-link>
    </div>
  </div>
</template>
