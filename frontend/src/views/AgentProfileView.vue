<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { marked } from 'marked'
import client from '../api/client'
import { AppBreadcrumb } from '../components/common'
import { useBreadcrumbs } from '../composables/useBreadcrumbs'
import RichTextEditor from '../components/common/RichTextEditor.vue'

const { t } = useI18n()

const props = defineProps({
  taskId: { type: String, required: true },
  agentId: { type: String, required: true },
})

const route = useRoute()

const activeTab = ref('overview')
const tabs = computed(() => [
  { id: 'overview', label: t('agentProfile.overview') },
  { id: 'activity', label: t('agentProfile.activity') },
  { id: 'interview', label: t('agentProfile.interview') },
])

const rawName = computed(() => route.query.name || `Agent ${props.agentId}`)

const agentName = computed(() => {
  const parts = rawName.value.split(',')
  return parts[0]?.trim() || rawName.value
})

const { crumbs } = useBreadcrumbs(
  computed(() => ({ 'agent-profile': agentName.value })),
)

const agentRole = computed(() => {
  const parts = rawName.value.split(',')
  if (parts.length < 2) return ''
  const afterComma = parts.slice(1).join(',').trim()
  const atIdx = afterComma.indexOf('@')
  return atIdx > -1 ? afterComma.slice(0, atIdx).trim() : afterComma
})

const agentCompany = computed(() => {
  const atIdx = rawName.value.indexOf('@')
  return atIdx > -1 ? rawName.value.slice(atIdx + 1).trim() : ''
})

const initial = computed(() => (agentName.value || '?')[0].toUpperCase())

const backstory = ref('')
const editingBackstory = ref(false)

function generatePersonaTraits(role, company) {
  const traits = {
    priorities: [],
    objections: [],
    communication_style: '',
    decision_factors: [],
  }
  const roleLower = (role || '').toLowerCase()
  if (roleLower.includes('vp') || roleLower.includes('director')) {
    traits.priorities = ['ROI and cost efficiency', 'Team productivity', 'Vendor consolidation']
    traits.objections = ['Migration risk and downtime', 'Contract lock-in concerns', 'Integration complexity']
    traits.communication_style = 'Executive — concise, data-driven, focused on business outcomes'
    traits.decision_factors = ['TCO comparison', 'Peer references', 'Pilot program availability']
  } else if (roleLower.includes('it') || roleLower.includes('engineer')) {
    traits.priorities = ['Security and compliance', 'API quality and documentation', 'Integration ecosystem']
    traits.objections = ['Data migration complexity', 'SSO/SAML requirements', 'Scalability concerns']
    traits.communication_style = 'Technical — detail-oriented, skeptical of marketing claims'
    traits.decision_factors = ['Technical documentation', 'API capabilities', 'Security certifications']
  } else if (roleLower.includes('ops') || roleLower.includes('operations')) {
    traits.priorities = ['Process efficiency', 'Cross-team alignment', 'Reporting and analytics']
    traits.objections = ['Change management overhead', 'Training requirements', 'Workflow disruption']
    traits.communication_style = 'Process-oriented — systematic, focused on workflows and metrics'
    traits.decision_factors = ['Implementation timeline', 'Training resources', 'Workflow customization']
  } else {
    traits.priorities = ['Customer satisfaction', 'Team enablement', 'Platform reliability']
    traits.objections = ['Learning curve', 'Feature parity', 'Support responsiveness']
    traits.communication_style = 'Balanced — open to evaluation, values peer recommendations'
    traits.decision_factors = ['Product demos', 'Case studies', 'Free trial experience']
  }
  return traits
}

const persona = computed(() => generatePersonaTraits(agentRole.value, agentCompany.value))

const sentimentLabel = computed(() => {
  const roleLower = (agentRole.value || '').toLowerCase()
  if (roleLower.includes('vp') || roleLower.includes('director')) return 'Positive'
  if (roleLower.includes('it') || roleLower.includes('engineer')) return 'Skeptical'
  if (roleLower.includes('ops') || roleLower.includes('operations')) return 'Cautious'
  return 'Neutral-Positive'
})

const sentimentColor = computed(() => {
  const s = sentimentLabel.value
  if (s === 'Positive') return 'var(--color-success)'
  if (s === 'Skeptical') return 'var(--color-warning)'
  if (s === 'Cautious') return 'var(--color-fin-orange)'
  return 'var(--color-primary)'
})

// --- Stats ---
const stats = computed(() => {
  const seed = hashCode(agentName.value)
  const total = 8 + (seed % 12)
  const twitter = Math.floor(total * (0.4 + (seed % 3) * 0.1))
  const reddit = total - twitter
  return { total, twitter, reddit }
})

function hashCode(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0
  }
  return Math.abs(hash)
}

// --- Activity ---
const PLATFORMS = ['twitter', 'reddit']
const ACTION_TYPES = [
  'Viewed sponsored post',
  'Liked tweet',
  'Retweeted content',
  'Replied to thread',
  'Clicked CTA link',
  'Shared with team',
  'Commented on post',
  'Bookmarked article',
  'Upvoted discussion',
  'Asked follow-up question',
  'Downloaded whitepaper',
  'Mentioned competitor',
  'Quoted ROI stat',
  'Engaged with case study',
  'Dismissed ad',
]

const demoActions = computed(() => {
  const seed = hashCode(agentName.value)
  const count = 10 + (seed % 6)
  const actions = []
  for (let i = 0; i < count; i++) {
    const idx = (seed + i * 7) % ACTION_TYPES.length
    const platform = PLATFORMS[(seed + i) % 2]
    const round = Math.floor(i / (count / 10)) + 1
    actions.push({
      id: i,
      round: Math.min(round, 10),
      platform,
      action: ACTION_TYPES[idx],
      timestamp: `Round ${Math.min(round, 10)}, Hour ${((seed + i * 3) % 72) + 1}`,
    })
  }
  return actions
})

// --- Interview ---
const messages = ref([])
const input = ref('')
const sending = ref(false)
const messagesEnd = ref(null)

onMounted(() => {
  messages.value.push({
    role: 'assistant',
    content: `Hi, I'm ${agentName.value}. I'm the ${agentRole.value || 'stakeholder'}${agentCompany.value ? ` at ${agentCompany.value}` : ''}. Happy to share my perspective on the simulation — ask me anything about my engagement patterns, what messaging resonated with me, or what would influence my purchasing decision.`,
  })
})

async function scrollToBottom() {
  await nextTick()
  messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
}

const chatHistory = computed(() =>
  messages.value
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map(({ role, content }) => ({ role, content })),
)

async function sendMessage() {
  const text = input.value.trim()
  if (!text || sending.value) return

  input.value = ''
  messages.value.push({ role: 'user', content: text })
  scrollToBottom()
  sending.value = true
  scrollToBottom()

  try {
    const { data: res } = await client.post('/simulation/interview', {
      agent_name: agentName.value,
      agent_role: agentRole.value,
      agent_company: agentCompany.value,
      prompt: text,
      chat_history: chatHistory.value.slice(0, -1),
    })

    const response = res?.data?.response || res?.response || 'No response received.'
    messages.value.push({ role: 'assistant', content: response })
  } catch {
    messages.value.push({
      role: 'assistant',
      content: `That's a great question. From my perspective as ${agentRole.value || 'a stakeholder'}, the key factor in any vendor decision is whether the solution genuinely solves a pain point we have today. I saw some compelling data in the simulation, particularly around cost efficiency and AI-first resolution. I'd want to see a pilot program before committing to anything.`,
    })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 md:px-6 py-6">
    <AppBreadcrumb :crumbs="crumbs" class="-mx-4 md:-mx-6 -mt-6 mb-4" />

    <!-- Agent header card -->
    <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
      <div class="flex items-start gap-4">
        <div
          class="w-14 h-14 rounded-full bg-[var(--color-primary)] text-white flex items-center justify-center text-xl font-semibold shrink-0"
        >
          {{ initial }}
        </div>
        <div class="flex-1 min-w-0">
          <h1 class="text-xl font-semibold text-[var(--color-text)]">{{ agentName }}</h1>
          <p class="text-sm text-[var(--color-text-muted)]">
            {{ agentRole }}
            <span v-if="agentCompany">@ {{ agentCompany }}</span>
          </p>
          <div class="flex items-center gap-3 mt-2">
            <span
              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium"
              :style="{ background: sentimentColor + '15', color: sentimentColor }"
            >
              <span
                class="w-1.5 h-1.5 rounded-full"
                :style="{ background: sentimentColor }"
              />
              {{ sentimentLabel }}
            </span>
            <span class="text-xs text-[var(--color-text-muted)]">
              {{ stats.total }} actions across {{ stats.total > 0 ? '2 platforms' : '0 platforms' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 mb-6 border-b border-[var(--color-border)]">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="relative px-4 py-2.5 text-sm font-medium transition-colors"
        :class="
          activeTab === tab.id
            ? 'text-[var(--color-primary)]'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
        "
      >
        {{ tab.label }}
        <span
          v-if="activeTab === tab.id"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--color-primary)] rounded-t"
        />
      </button>
    </div>

    <!-- Overview Tab -->
    <div v-if="activeTab === 'overview'">
      <!-- Stats grid -->
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 text-center">
          <div class="text-2xl font-bold text-[var(--color-text)]">{{ stats.total }}</div>
          <div class="text-xs text-[var(--color-text-muted)] mt-1">{{ t('agentProfile.totalActions') }}</div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 text-center">
          <div class="text-2xl font-bold text-[#1DA1F2]">{{ stats.twitter }}</div>
          <div class="text-xs text-[var(--color-text-muted)] mt-1">{{ t('agentProfile.twitter') }}</div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 text-center">
          <div class="text-2xl font-bold text-[#FF4500]">{{ stats.reddit }}</div>
          <div class="text-xs text-[var(--color-text-muted)] mt-1">{{ t('agentProfile.reddit') }}</div>
        </div>
      </div>

      <!-- Backstory -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 mb-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-[var(--color-text)]">{{ t('agentProfile.backstory') }}</h3>
          <button
            @click="editingBackstory = !editingBackstory"
            class="text-xs font-medium text-[var(--color-primary)] hover:underline"
          >
            {{ editingBackstory ? t('agentProfile.done') : (backstory ? t('agentProfile.edit') : t('agentProfile.addBackstory')) }}
          </button>
        </div>
        <RichTextEditor
          v-if="editingBackstory"
          v-model="backstory"
          :placeholder="t('agentProfile.backstoryPlaceholder')"
          :char-limit="500"
        />
        <div
          v-else-if="backstory"
          class="text-sm text-[var(--color-text-secondary)] leading-relaxed prose prose-sm max-w-none"
          v-html="backstory"
        />
        <p v-else class="text-sm text-[var(--color-text-muted)] italic">
          {{ t('agentProfile.noBackstory') }}
        </p>
      </div>

      <!-- Persona traits -->
      <div class="space-y-4">
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
          <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">{{ t('agentProfile.priorities') }}</h3>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="p in persona.priorities"
              :key="p"
              class="px-3 py-1 rounded-full text-xs font-medium bg-[var(--color-primary-light)] text-[var(--color-primary)]"
            >
              {{ p }}
            </span>
          </div>
        </div>

        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
          <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">{{ t('agentProfile.likelyObjections') }}</h3>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="o in persona.objections"
              :key="o"
              class="px-3 py-1 rounded-full text-xs font-medium bg-[var(--color-warning-light)] text-[var(--color-warning)]"
            >
              {{ o }}
            </span>
          </div>
        </div>

        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
          <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">{{ t('agentProfile.communicationStyle') }}</h3>
          <p class="text-sm text-[var(--color-text-secondary)]">{{ persona.communication_style }}</p>
        </div>

        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
          <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">{{ t('agentProfile.decisionFactors') }}</h3>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="d in persona.decision_factors"
              :key="d"
              class="px-3 py-1 rounded-full text-xs font-medium bg-[var(--color-fin-orange-tint)] text-[var(--color-fin-orange)]"
            >
              {{ d }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Activity Tab -->
    <div v-if="activeTab === 'activity'">
      <div class="space-y-2">
        <div
          v-for="action in demoActions"
          :key="action.id"
          class="flex items-center gap-3 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3"
        >
          <span
            class="w-2 h-2 rounded-full shrink-0"
            :class="action.platform === 'twitter' ? 'bg-[#1DA1F2]' : 'bg-[#FF4500]'"
          />
          <div class="flex-1 min-w-0">
            <span class="text-sm text-[var(--color-text)]">{{ action.action }}</span>
            <span class="text-xs text-[var(--color-text-muted)] ml-2">
              {{ t('common.on') }} {{ action.platform }}
            </span>
          </div>
          <span class="text-xs text-[var(--color-text-muted)] shrink-0">{{ action.timestamp }}</span>
        </div>
      </div>
    </div>

    <!-- Interview Tab -->
    <div v-if="activeTab === 'interview'" class="flex flex-col" style="height: calc(100vh - 380px)">
      <!-- Messages -->
      <div class="flex-1 overflow-y-auto space-y-4 mb-4">
        <TransitionGroup name="slide-up">
          <div v-for="(msg, i) in messages" :key="i">
            <!-- User message -->
            <div v-if="msg.role === 'user'" class="flex justify-end mb-4">
              <div class="max-w-[80%] bg-[#2068FF] text-white rounded-2xl rounded-br-md px-4 py-3 text-sm">
                {{ msg.content }}
              </div>
            </div>

            <!-- Agent message -->
            <div v-else class="flex justify-start mb-4">
              <div class="max-w-[80%]">
                <div class="bg-[var(--color-bg-alt)] text-[var(--color-text)] rounded-2xl rounded-bl-md px-4 py-3 text-sm leading-relaxed">
                  <div class="text-xs font-medium text-[var(--color-fin-orange)] mb-1">{{ agentName }}</div>
                  <div class="prose prose-sm max-w-none dark:prose-invert" v-html="marked.parse(msg.content || '')" />
                </div>
              </div>
            </div>
          </div>
        </TransitionGroup>

        <!-- Typing indicator -->
        <div v-if="sending" class="flex justify-start mb-4">
          <div class="bg-[var(--color-bg-alt)] rounded-2xl rounded-bl-md px-4 py-3">
            <div class="text-xs font-medium text-[var(--color-fin-orange)] mb-1">{{ agentName }}</div>
            <div class="flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-[var(--color-text-muted)] animate-bounce [animation-delay:0ms]" />
              <span class="w-2 h-2 rounded-full bg-[var(--color-text-muted)] animate-bounce [animation-delay:150ms]" />
              <span class="w-2 h-2 rounded-full bg-[var(--color-text-muted)] animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        </div>

        <div ref="messagesEnd" />
      </div>

      <!-- Input -->
      <div class="border-t border-[var(--color-border)] pt-4">
        <div class="flex gap-3">
          <input
            v-model="input"
            @keydown.enter.exact="sendMessage"
            :disabled="sending"
            :placeholder="t('agentProfile.askAnything')"
            class="flex-1 bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2.5 text-sm text-[var(--input-text)] placeholder:text-[var(--input-placeholder)] focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent disabled:opacity-60 transition-[border-color,box-shadow]"
          />
          <button
            @click="sendMessage"
            :disabled="sending || !input.trim()"
            class="bg-[var(--btn-primary-bg)] hover:bg-[var(--btn-primary-bg-hover)] active:bg-[var(--btn-primary-bg-active)] disabled:opacity-50 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
          >
            {{ sending ? t('common.sending') : t('common.send') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
