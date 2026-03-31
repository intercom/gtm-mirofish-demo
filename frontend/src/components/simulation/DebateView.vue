<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  topic: { type: String, default: '' },
  format: { type: String, default: 'oxford', validator: v => ['oxford', 'panel', 'roundtable'].includes(v) },
  agents: { type: Array, default: () => [] },
  messages: { type: Array, default: () => [] },
  currentPhase: { type: String, default: 'opening' },
  voteResults: { type: Object, default: null },
  crossExamPair: { type: Object, default: null },
  isLive: { type: Boolean, default: false },
})

const emit = defineEmits(['phase-change', 'agent-click'])

// ── Phase definitions ──────────────────────────────────────────────
const PHASES = [
  { key: 'opening', label: 'Opening', icon: '\u{1F399}' },
  { key: 'rebuttal', label: 'Rebuttal', icon: '\u{1F4AC}' },
  { key: 'cross-examination', label: 'Cross-Exam', icon: '\u{2753}' },
  { key: 'closing', label: 'Closing', icon: '\u{1F3C1}' },
  { key: 'vote', label: 'Vote', icon: '\u{1F5F3}' },
]

const activePhase = ref(props.currentPhase)
const phaseTimer = ref(0)
let timerInterval = null

watch(() => props.currentPhase, (val) => {
  activePhase.value = val
  resetTimer()
})

function resetTimer() {
  phaseTimer.value = 0
  if (timerInterval) clearInterval(timerInterval)
  if (props.isLive) {
    timerInterval = setInterval(() => phaseTimer.value++, 1000)
  }
}

function formatTimer(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

const activePhaseIndex = computed(() =>
  PHASES.findIndex(p => p.key === activePhase.value)
)

// ── Agent teams ────────────────────────────────────────────────────
const forAgents = computed(() =>
  resolvedAgents.value.filter(a => a.side === 'for')
)

const againstAgents = computed(() =>
  resolvedAgents.value.filter(a => a.side === 'against')
)

// ── Demo data ──────────────────────────────────────────────────────
const DEMO_AGENTS = [
  { id: 'a1', name: 'Sarah Chen', role: 'VP of Support', company: 'TechFlow', side: 'for' },
  { id: 'a2', name: 'Marcus Williams', role: 'CX Director', company: 'RetailCo', side: 'for' },
  { id: 'a3', name: 'Priya Patel', role: 'Operations Lead', company: 'FinServe', side: 'for' },
  { id: 'a4', name: 'David Kim', role: 'CTO', company: 'ScaleUp', side: 'against' },
  { id: 'a5', name: 'Rachel Torres', role: 'Finance Director', company: 'MedTech', side: 'against' },
  { id: 'a6', name: 'James Murphy', role: 'IT Leader', company: 'LogiCorp', side: 'against' },
]

const DEMO_TOPIC = 'Should we prioritize AI-first customer support over traditional channels?'

const DEMO_MESSAGES = [
  { id: 'm1', agentId: 'a1', phase: 'opening', side: 'for', content: 'Our pilot data shows Fin AI resolves 47% of tickets without human intervention. That\'s not a projection — it\'s current performance with real customers. The question isn\'t whether AI works, but how fast we scale it.' },
  { id: 'm2', agentId: 'a4', phase: 'opening', side: 'against', content: 'Resolution rate doesn\'t tell the full story. We need to look at customer satisfaction for those AI-resolved tickets vs. human-handled ones. In our tests, CSAT dropped 12 points for complex issues routed through AI.' },
  { id: 'm3', agentId: 'a2', phase: 'opening', side: 'for', content: 'Our CX data shows customers under 35 actually prefer AI chat — 68% choose it when given the option. We\'re not replacing humans; we\'re meeting customers where they want to be.' },
  { id: 'm4', agentId: 'a5', phase: 'opening', side: 'against', content: 'The ROI math doesn\'t add up yet. Implementation costs, training data curation, and ongoing model fine-tuning total $400K in year one. Traditional channel optimization costs a fraction.' },
  { id: 'm5', agentId: 'a3', phase: 'rebuttal', side: 'for', content: 'David, that CSAT drop was with last-gen models. Current LLM-powered agents handle nuance far better. Our updated pilot shows CSAT parity on 80% of issue types.' },
  { id: 'm6', agentId: 'a6', phase: 'rebuttal', side: 'against', content: 'Even if AI handles simple tickets, the hard problems still need humans. Over-investing in AI means under-investing in agent training and tooling — the things that actually move NPS.' },
  { id: 'm7', agentId: 'a1', phase: 'rebuttal', side: 'for', content: 'James, that\'s exactly backwards. AI handling the simple stuff frees human agents to focus on complex issues. Our support team\'s average handle time on escalations improved 23% when AI took the easy tickets.' },
  { id: 'm8', agentId: 'a4', phase: 'rebuttal', side: 'against', content: 'Freedom to focus is great in theory. In practice, most orgs cut headcount after AI rollout. Let\'s be honest about the real motivation here.' },
  { id: 'm9', agentId: 'a2', phase: 'cross-examination', side: 'for', type: 'question', content: 'Rachel, you mentioned ROI concerns. What if I told you our AI-first teams show 3.2x return within 18 months? Would that change your position?' },
  { id: 'm10', agentId: 'a5', phase: 'cross-examination', side: 'against', type: 'answer', content: 'I\'d need to see the methodology. Most AI ROI studies cherry-pick metrics and ignore hidden costs like customer churn from bad AI experiences.' },
  { id: 'm11', agentId: 'a6', phase: 'cross-examination', side: 'against', type: 'question', content: 'Priya, your operations data is impressive, but what happens when the AI makes a mistake on a high-value customer? What\'s the cost of that single failure?' },
  { id: 'm12', agentId: 'a3', phase: 'cross-examination', side: 'for', type: 'answer', content: 'Fair point, but human agents make mistakes too. Our AI has guardrails — it escalates uncertain cases. The error rate is actually lower than our human-only baseline.' },
  { id: 'm13', agentId: 'a1', phase: 'closing', side: 'for', content: 'The evidence is clear: AI-first support delivers faster resolution, higher satisfaction among key demographics, and better economics. The companies that move now will have an insurmountable advantage in 18 months.' },
  { id: 'm14', agentId: 'a4', phase: 'closing', side: 'against', content: 'Moving fast is not the same as moving smart. I advocate for a balanced approach: invest in AI for clear-cut use cases, but double down on human expertise for everything else. The either/or framing is a false choice.' },
]

const DEMO_VOTE = { for: 8, against: 5, total: 13, winner: 'for' }

const resolvedTopic = computed(() => props.topic || DEMO_TOPIC)
const resolvedAgents = computed(() => props.agents.length ? props.agents : DEMO_AGENTS)
const resolvedMessages = computed(() => props.messages.length ? props.messages : DEMO_MESSAGES)
const resolvedVote = computed(() => props.voteResults || DEMO_VOTE)

// ── Filtered messages by phase ─────────────────────────────────────
const phaseMessages = computed(() =>
  resolvedMessages.value.filter(m => m.phase === activePhase.value)
)

// ── Agent initial & color helpers ──────────────────────────────────
function agentInitials(name) {
  return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
}

function agentById(id) {
  return resolvedAgents.value.find(a => a.id === id) || { name: 'Unknown', role: '', side: 'for' }
}

const SIDE_COLORS = {
  for: { bg: 'rgba(32, 104, 255, 0.08)', border: 'rgba(32, 104, 255, 0.2)', text: 'var(--color-primary)', solid: '#2068FF' },
  against: { bg: 'rgba(255, 86, 0, 0.08)', border: 'rgba(255, 86, 0, 0.2)', text: 'var(--color-fin-orange)', solid: '#ff5600' },
}

// ── Vote animation ─────────────────────────────────────────────────
const voteAnimated = ref(false)
const voteForWidth = ref(0)
const voteAgainstWidth = ref(0)

watch(activePhase, (phase) => {
  if (phase === 'vote') {
    voteAnimated.value = false
    voteForWidth.value = 0
    voteAgainstWidth.value = 0
    setTimeout(() => {
      const total = resolvedVote.value.total || 1
      voteForWidth.value = (resolvedVote.value.for / total) * 100
      voteAgainstWidth.value = (resolvedVote.value.against / total) * 100
      voteAnimated.value = true
    }, 100)
  }
})

// ── Auto-scroll feed ───────────────────────────────────────────────
const feedRef = ref(null)

watch(phaseMessages, () => {
  if (feedRef.value) {
    setTimeout(() => {
      feedRef.value.scrollTop = feedRef.value.scrollHeight
    }, 50)
  }
}, { deep: true })

// ── Lifecycle ──────────────────────────────────────────────────────
onMounted(() => {
  if (props.isLive) resetTimer()
  if (activePhase.value === 'vote') {
    setTimeout(() => {
      const total = resolvedVote.value.total || 1
      voteForWidth.value = (resolvedVote.value.for / total) * 100
      voteAgainstWidth.value = (resolvedVote.value.against / total) * 100
      voteAnimated.value = true
    }, 300)
  }
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})
</script>

<template>
  <div class="h-full overflow-y-auto">
    <div class="max-w-6xl mx-auto px-4 md:px-6 py-6">

      <!-- Debate Header -->
      <div class="mb-6">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full"
            :class="format === 'oxford'
              ? 'bg-[var(--color-primary-tint)] text-[var(--color-primary)]'
              : format === 'panel'
                ? 'bg-[var(--color-accent-tint)] text-[var(--color-accent)]'
                : 'bg-[var(--color-success-light)] text-[var(--color-success)]'"
          >
            {{ format }} format
          </span>
          <span v-if="isLive" class="flex items-center gap-1 text-xs text-[var(--color-error)]">
            <span class="w-2 h-2 rounded-full bg-[var(--color-error)] animate-pulse" />
            Live
          </span>
        </div>
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)] leading-tight">
          {{ resolvedTopic }}
        </h1>
      </div>

      <!-- Phase Navigation -->
      <div class="flex items-center gap-1 mb-6 p-1 bg-[var(--color-tint)] rounded-lg overflow-x-auto">
        <button
          v-for="(phase, idx) in PHASES"
          :key="phase.key"
          class="flex items-center gap-1.5 px-3 py-2 text-sm rounded-md font-medium transition-all whitespace-nowrap"
          :class="activePhase === phase.key
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : idx < activePhaseIndex
              ? 'text-[var(--color-primary)] hover:bg-[rgba(32,104,255,0.05)]'
              : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="activePhase = phase.key; emit('phase-change', phase.key)"
        >
          <span class="text-sm">{{ phase.icon }}</span>
          {{ phase.label }}
          <svg v-if="idx < activePhaseIndex" class="w-3.5 h-3.5 text-[var(--color-success)]" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
        </button>

        <!-- Timer -->
        <div v-if="isLive" class="ml-auto pl-3 pr-2 text-xs font-mono text-[var(--color-text-muted)] whitespace-nowrap">
          {{ formatTimer(phaseTimer) }}
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════════ -->
      <!-- OXFORD FORMAT: Two columns (For / Against)         -->
      <!-- ═══════════════════════════════════════════════════ -->
      <template v-if="format === 'oxford'">

        <!-- Team Headers -->
        <div class="grid grid-cols-2 gap-4 mb-4">
          <!-- For Team -->
          <div class="rounded-lg p-4 border"
            :style="{ backgroundColor: SIDE_COLORS.for.bg, borderColor: SIDE_COLORS.for.border }">
            <div class="flex items-center gap-2 mb-3">
              <span class="text-xs font-bold uppercase tracking-wider" :style="{ color: SIDE_COLORS.for.text }">For</span>
              <div class="flex-1 h-px" :style="{ backgroundColor: SIDE_COLORS.for.border }" />
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="agent in forAgents"
                :key="agent.id"
                class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[var(--color-primary-border)] transition-colors"
                @click="emit('agent-click', agent)"
              >
                <span class="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold text-white"
                  :style="{ backgroundColor: SIDE_COLORS.for.solid }">
                  {{ agentInitials(agent.name) }}
                </span>
                <div class="text-left">
                  <div class="text-xs font-medium text-[var(--color-text)]">{{ agent.name }}</div>
                  <div class="text-[10px] text-[var(--color-text-muted)]">{{ agent.role }}</div>
                </div>
              </button>
            </div>
          </div>

          <!-- Against Team -->
          <div class="rounded-lg p-4 border"
            :style="{ backgroundColor: SIDE_COLORS.against.bg, borderColor: SIDE_COLORS.against.border }">
            <div class="flex items-center gap-2 mb-3">
              <span class="text-xs font-bold uppercase tracking-wider" :style="{ color: SIDE_COLORS.against.text }">Against</span>
              <div class="flex-1 h-px" :style="{ backgroundColor: SIDE_COLORS.against.border }" />
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="agent in againstAgents"
                :key="agent.id"
                class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[rgba(255,86,0,0.3)] transition-colors"
                @click="emit('agent-click', agent)"
              >
                <span class="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold text-white"
                  :style="{ backgroundColor: SIDE_COLORS.against.solid }">
                  {{ agentInitials(agent.name) }}
                </span>
                <div class="text-left">
                  <div class="text-xs font-medium text-[var(--color-text)]">{{ agent.name }}</div>
                  <div class="text-[10px] text-[var(--color-text-muted)]">{{ agent.role }}</div>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- Vote Results Phase -->
        <template v-if="activePhase === 'vote'">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 mb-6">
            <h3 class="text-sm font-semibold text-[var(--color-text)] mb-4 text-center">Vote Results</h3>

            <!-- Vote bar -->
            <div class="mb-4">
              <div class="flex items-center justify-between text-xs font-medium mb-2">
                <span :style="{ color: SIDE_COLORS.for.text }">For ({{ resolvedVote.for }})</span>
                <span :style="{ color: SIDE_COLORS.against.text }">Against ({{ resolvedVote.against }})</span>
              </div>
              <div class="flex h-10 rounded-lg overflow-hidden gap-0.5">
                <div
                  class="flex items-center justify-center text-white text-sm font-bold rounded-l-lg"
                  :style="{
                    backgroundColor: SIDE_COLORS.for.solid,
                    width: voteAnimated ? voteForWidth + '%' : '0%',
                    transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)',
                  }"
                >
                  <span v-if="voteForWidth > 15">{{ Math.round(voteForWidth) }}%</span>
                </div>
                <div
                  class="flex items-center justify-center text-white text-sm font-bold rounded-r-lg"
                  :style="{
                    backgroundColor: SIDE_COLORS.against.solid,
                    width: voteAnimated ? voteAgainstWidth + '%' : '0%',
                    transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)',
                  }"
                >
                  <span v-if="voteAgainstWidth > 15">{{ Math.round(voteAgainstWidth) }}%</span>
                </div>
              </div>
            </div>

            <!-- Winner -->
            <div v-if="resolvedVote.winner" class="text-center">
              <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold"
                :style="{
                  backgroundColor: SIDE_COLORS[resolvedVote.winner].bg,
                  color: SIDE_COLORS[resolvedVote.winner].text,
                }">
                {{ resolvedVote.winner === 'for' ? '\u2705' : '\u274C' }}
                {{ resolvedVote.winner === 'for' ? 'Motion Carries' : 'Motion Fails' }}
              </span>
            </div>
          </div>
        </template>

        <!-- Message Feed (Oxford: two-column) -->
        <template v-if="activePhase !== 'vote'">
          <div ref="feedRef" class="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            <div v-if="!phaseMessages.length" class="flex flex-col items-center justify-center py-16 text-[var(--color-text-muted)]">
              <span class="text-3xl mb-2">{{ PHASES[activePhaseIndex]?.icon || '\u{1F399}' }}</span>
              <p class="text-sm">No {{ PHASES[activePhaseIndex]?.label?.toLowerCase() || '' }} statements yet</p>
            </div>

            <div
              v-for="msg in phaseMessages"
              :key="msg.id"
              class="flex gap-3"
              :class="agentById(msg.agentId).side === 'against' ? 'flex-row-reverse' : ''"
            >
              <!-- Avatar -->
              <span class="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold text-white shrink-0"
                :style="{ backgroundColor: SIDE_COLORS[agentById(msg.agentId).side]?.solid || '#888' }">
                {{ agentInitials(agentById(msg.agentId).name) }}
              </span>

              <!-- Message bubble -->
              <div class="max-w-[75%] min-w-0">
                <div class="flex items-center gap-2 mb-1"
                  :class="agentById(msg.agentId).side === 'against' ? 'justify-end' : ''">
                  <span class="text-xs font-medium text-[var(--color-text)]">{{ agentById(msg.agentId).name }}</span>
                  <span class="text-[10px] text-[var(--color-text-muted)]">{{ agentById(msg.agentId).role }}</span>
                  <span v-if="msg.type === 'question'" class="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--color-warning-light)] text-[var(--color-warning)] font-medium">Q</span>
                  <span v-if="msg.type === 'answer'" class="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--color-success-light)] text-[var(--color-success)] font-medium">A</span>
                </div>
                <div
                  class="rounded-lg px-3.5 py-2.5 text-sm text-[var(--color-text)] border"
                  :class="[
                    activePhase === 'cross-examination' && msg.type
                      ? 'ring-1 ring-offset-1'
                      : '',
                  ]"
                  :style="{
                    backgroundColor: SIDE_COLORS[agentById(msg.agentId).side]?.bg || 'var(--color-tint)',
                    borderColor: SIDE_COLORS[agentById(msg.agentId).side]?.border || 'var(--color-border)',
                    ringColor: msg.type ? (SIDE_COLORS[agentById(msg.agentId).side]?.border || 'transparent') : 'transparent',
                  }"
                >
                  {{ msg.content }}
                </div>
              </div>
            </div>
          </div>
        </template>
      </template>

      <!-- ═══════════════════════════════════════════════════ -->
      <!-- PANEL / ROUNDTABLE FORMAT: Circular arrangement    -->
      <!-- ═══════════════════════════════════════════════════ -->
      <template v-else>

        <!-- Circular seating -->
        <div class="relative mx-auto mb-6" style="width: 280px; height: 280px">
          <!-- Center topic -->
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="w-20 h-20 rounded-full bg-[var(--color-tint)] border border-[var(--color-border)] flex items-center justify-center">
              <span class="text-2xl">{{ format === 'panel' ? '\u{1F399}' : '\u{1F465}' }}</span>
            </div>
          </div>

          <!-- Agent seats arranged in circle -->
          <button
            v-for="(agent, idx) in resolvedAgents"
            :key="agent.id"
            class="absolute flex flex-col items-center transition-all"
            :style="{
              left: `${50 + 42 * Math.cos(2 * Math.PI * idx / resolvedAgents.length - Math.PI / 2)}%`,
              top: `${50 + 42 * Math.sin(2 * Math.PI * idx / resolvedAgents.length - Math.PI / 2)}%`,
              transform: 'translate(-50%, -50%)',
            }"
            @click="emit('agent-click', agent)"
          >
            <span
              class="w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold text-white border-2 transition-all"
              :class="phaseMessages.some(m => m.agentId === agent.id)
                ? 'border-[var(--color-primary)] shadow-md scale-110'
                : 'border-transparent'"
              :style="{ backgroundColor: agent.side === 'for' ? SIDE_COLORS.for.solid : agent.side === 'against' ? SIDE_COLORS.against.solid : 'var(--color-text-muted)' }"
            >
              {{ agentInitials(agent.name) }}
            </span>
            <span class="text-[10px] font-medium text-[var(--color-text)] mt-1 text-center max-w-[70px] truncate">
              {{ agent.name.split(' ')[0] }}
            </span>
          </button>
        </div>

        <!-- Vote Results (panel/roundtable) -->
        <template v-if="activePhase === 'vote'">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 mb-6">
            <h3 class="text-sm font-semibold text-[var(--color-text)] mb-4 text-center">Vote Results</h3>
            <div class="flex items-center justify-center gap-8">
              <div class="text-center">
                <div class="text-3xl font-bold" :style="{ color: SIDE_COLORS.for.solid }">{{ resolvedVote.for }}</div>
                <div class="text-xs text-[var(--color-text-muted)] mt-1">For</div>
              </div>
              <div class="text-2xl text-[var(--color-text-muted)]">vs</div>
              <div class="text-center">
                <div class="text-3xl font-bold" :style="{ color: SIDE_COLORS.against.solid }">{{ resolvedVote.against }}</div>
                <div class="text-xs text-[var(--color-text-muted)] mt-1">Against</div>
              </div>
            </div>
          </div>
        </template>

        <!-- Message Feed (panel/roundtable: single column with speaker indicator) -->
        <template v-if="activePhase !== 'vote'">
          <div ref="feedRef" class="space-y-3 max-h-[400px] overflow-y-auto pr-1">
            <div v-if="!phaseMessages.length" class="flex flex-col items-center justify-center py-16 text-[var(--color-text-muted)]">
              <span class="text-3xl mb-2">{{ PHASES[activePhaseIndex]?.icon || '\u{1F399}' }}</span>
              <p class="text-sm">Waiting for discussion to begin...</p>
            </div>

            <div
              v-for="msg in phaseMessages"
              :key="msg.id"
              class="flex items-start gap-3 p-3 rounded-lg border transition-colors"
              :class="phaseMessages[phaseMessages.length - 1]?.id === msg.id && isLive
                ? 'bg-[var(--color-primary-light)] border-[var(--color-primary-border)]'
                : 'bg-[var(--color-surface)] border-[var(--color-border)]'"
            >
              <span class="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold text-white shrink-0"
                :style="{ backgroundColor: agentById(msg.agentId).side === 'for' ? SIDE_COLORS.for.solid : agentById(msg.agentId).side === 'against' ? SIDE_COLORS.against.solid : '#888' }">
                {{ agentInitials(agentById(msg.agentId).name) }}
              </span>
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs font-medium text-[var(--color-text)]">{{ agentById(msg.agentId).name }}</span>
                  <span class="text-[10px] text-[var(--color-text-muted)]">{{ agentById(msg.agentId).role }}</span>
                </div>
                <p class="text-sm text-[var(--color-text-secondary)]">{{ msg.content }}</p>
              </div>
            </div>
          </div>
        </template>
      </template>

      <!-- Cross-examination indicator -->
      <div
        v-if="activePhase === 'cross-examination' && crossExamPair"
        class="mt-4 flex items-center justify-center gap-3 px-4 py-3 bg-[var(--color-warning-light)] border border-[rgba(245,158,11,0.2)] rounded-lg"
      >
        <span class="text-xs font-medium text-[var(--color-warning)]">
          {{ agentById(crossExamPair.questioner).name }} is questioning {{ agentById(crossExamPair.respondent).name }}
        </span>
      </div>

    </div>
  </div>
</template>

<style scoped>
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
