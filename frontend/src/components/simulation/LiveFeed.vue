<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  actions: { type: Array, default: () => [] },
  connectionStatus: { type: String, default: 'polling' },
  maxVisible: { type: Number, default: 100 },
  showThinking: { type: Boolean, default: false },
  hasAgentFilter: { type: Boolean, default: false },
  isAgentTransparent: { type: Function, default: () => false },
  llmModel: { type: String, default: '' },
  llmProvider: { type: String, default: '' },
})

const emit = defineEmits(['select-agent', 'toggle-thinking', 'toggle-agent', 'clear-agent-filter'])

const feedContainer = ref(null)
const autoScroll = ref(true)
const filterPlatform = ref('all')
const filterType = ref('all')
const searchQuery = ref('')
const isPaused = ref(false)

const platformOptions = [
  { key: 'all', label: 'All' },
  { key: 'twitter', label: 'Twitter' },
  { key: 'reddit', label: 'Reddit' },
]

const typeOptions = [
  { key: 'all', label: 'All Types' },
  { key: 'post', label: 'Posts' },
  { key: 'reply', label: 'Replies' },
  { key: 'like', label: 'Likes' },
  { key: 'repost', label: 'Reposts' },
]

const filteredActions = computed(() => {
  let result = props.actions

  if (filterPlatform.value !== 'all') {
    result = result.filter(a => a.platform === filterPlatform.value)
  }

  if (filterType.value !== 'all') {
    result = result.filter(a => matchesType(a.action_type, filterType.value))
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(a =>
      (a.agent_name || '').toLowerCase().includes(q) ||
      (a.action_args?.content || '').toLowerCase().includes(q)
    )
  }

  return result
})

const visibleActions = computed(() => {
  const list = filteredActions.value
  if (isPaused.value) return list.slice(-props.maxVisible)
  return list.slice(-props.maxVisible)
})

const feedStats = computed(() => {
  const all = props.actions
  return {
    total: all.length,
    twitter: all.filter(a => a.platform === 'twitter').length,
    reddit: all.filter(a => a.platform === 'reddit').length,
    filtered: filteredActions.value.length,
  }
})

function matchesType(actionType, filter) {
  const t = (actionType || '').toUpperCase()
  switch (filter) {
    case 'post': return t.includes('POST') || t.includes('THREAD')
    case 'reply': return t.includes('REPLY') || t.includes('COMMENT')
    case 'like': return t.includes('LIKE') || t.includes('UPVOTE')
    case 'repost': return t.includes('REPOST') || t.includes('RETWEET') || t.includes('SHARE')
    default: return true
  }
}

function actionIcon(actionType) {
  const t = (actionType || '').toUpperCase()
  if (t.includes('POST') || t.includes('CREATE') || t.includes('THREAD')) return '\uD83D\uDCDD'
  if (t.includes('REPLY') || t.includes('COMMENT')) return '\uD83D\uDCAC'
  if (t.includes('LIKE') || t.includes('UPVOTE')) return '\u2764\uFE0F'
  if (t.includes('REPOST') || t.includes('RETWEET') || t.includes('SHARE')) return '\uD83D\uDD01'
  return '\u26A1'
}

function actionLabel(actionType) {
  const t = (actionType || '').toUpperCase()
  if (t.includes('CREATE_POST') || t.includes('CREATE_THREAD')) return 'Posted'
  if (t.includes('REPLY') || t.includes('COMMENT')) return 'Replied'
  if (t.includes('LIKE') || t.includes('UPVOTE')) return 'Liked'
  if (t.includes('REPOST') || t.includes('RETWEET')) return 'Reposted'
  if (t.includes('SHARE')) return 'Shared'
  return actionType?.replace(/_/g, ' ').toLowerCase() || 'Action'
}

function actionColor(actionType) {
  const t = (actionType || '').toUpperCase()
  if (t.includes('POST') || t.includes('CREATE') || t.includes('THREAD')) return 'bg-[rgba(32,104,255,0.08)] border-[rgba(32,104,255,0.15)]'
  if (t.includes('REPLY') || t.includes('COMMENT')) return 'bg-[rgba(0,153,0,0.06)] border-[rgba(0,153,0,0.12)]'
  if (t.includes('LIKE') || t.includes('UPVOTE')) return 'bg-[rgba(239,68,68,0.05)] border-[rgba(239,68,68,0.1)]'
  if (t.includes('REPOST') || t.includes('RETWEET') || t.includes('SHARE')) return 'bg-[rgba(255,86,0,0.06)] border-[rgba(255,86,0,0.12)]'
  return 'bg-[var(--color-tint)] border-[var(--color-border)]'
}

function platformBadge(platform) {
  return platform === 'twitter'
    ? { label: 'X', cls: 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]' }
    : { label: 'Reddit', cls: 'bg-[var(--color-fin-orange-tint)] text-[var(--color-fin-orange)]' }
}

function agentShortName(fullName) {
  if (!fullName) return 'Agent'
  const parts = fullName.split(',')
  return parts[0].trim()
}

function agentRole(fullName) {
  if (!fullName) return ''
  const parts = fullName.split(',')
  return parts.length > 1 ? parts.slice(1).join(',').trim() : ''
}

function truncate(str, len = 140) {
  if (!str || str.length <= len) return str || ''
  return str.slice(0, len) + '\u2026'
}

function connectionLabel(status) {
  switch (status) {
    case 'connected': return 'Live'
    case 'connecting': return 'Connecting'
    case 'error': return 'Reconnecting'
    case 'done': return 'Complete'
    default: return 'Polling'
  }
}

function connectionDotClass(status) {
  switch (status) {
    case 'connected': return 'bg-[var(--color-success)]'
    case 'connecting': return 'bg-yellow-400'
    case 'error': return 'bg-[var(--color-error)]'
    case 'done': return 'bg-[var(--color-text-muted)]'
    default: return 'bg-[var(--color-primary)]'
  }
}

function onFeedScroll() {
  const el = feedContainer.value
  if (!el) return
  autoScroll.value = (el.scrollHeight - el.scrollTop - el.clientHeight) < 60
}

function scrollToBottom() {
  autoScroll.value = true
  isPaused.value = false
  if (feedContainer.value) {
    feedContainer.value.scrollTop = feedContainer.value.scrollHeight
  }
}

watch(() => props.actions.length, () => {
  if (autoScroll.value && !isPaused.value && feedContainer.value) {
    nextTick(() => {
      feedContainer.value.scrollTop = feedContainer.value.scrollHeight
    })
  }
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden flex flex-col">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-[var(--color-border)]">
      <div class="flex items-center justify-between mb-2.5">
        <div class="flex items-center gap-2.5">
          <h3 class="text-sm font-semibold text-[var(--color-text)]">Live Feed</h3>
          <!-- Connection status indicator -->
          <span class="flex items-center gap-1.5 text-[11px] text-[var(--color-text-muted)]">
            <span
              class="inline-block w-1.5 h-1.5 rounded-full"
              :class="[connectionDotClass(connectionStatus), connectionStatus === 'connected' ? 'animate-pulse' : '']"
            />
            {{ connectionLabel(connectionStatus) }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-[11px] text-[var(--color-text-muted)]">
            {{ feedStats.filtered }}<span v-if="feedStats.filtered !== feedStats.total"> / {{ feedStats.total }}</span> events
          </span>
          <button
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors border"
            :class="showThinking
              ? 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)] border-[var(--color-primary)]'
              : 'bg-[var(--color-tint)] text-[var(--color-text-muted)] border-transparent hover:text-[var(--color-text-secondary)]'"
            @click="emit('toggle-thinking')"
            :title="showThinking ? 'Hide agent reasoning' : 'Show agent reasoning'"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2a8 8 0 0 0-8 8c0 3.4 2.1 6.3 5 7.4V20a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1v-2.6c2.9-1.1 5-4 5-7.4a8 8 0 0 0-8-8z"/>
              <line x1="10" y1="22" x2="14" y2="22"/>
            </svg>
            {{ showThinking ? 'Thinking On' : 'Show Thinking' }}
          </button>
          <button
            v-if="!autoScroll"
            class="text-[11px] px-2 py-0.5 rounded bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] transition-colors"
            @click="scrollToBottom"
          >
            &#x2193; Latest
          </button>
        </div>
      </div>

      <!-- Filters row -->
      <div class="flex items-center gap-2 flex-wrap">
        <!-- Platform filter pills -->
        <div class="flex gap-0.5 bg-[var(--color-tint)] rounded-md p-0.5">
          <button
            v-for="opt in platformOptions"
            :key="opt.key"
            class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
            :class="filterPlatform === opt.key
              ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
              : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
            @click="filterPlatform = opt.key"
          >
            {{ opt.label }}
          </button>
        </div>

        <!-- Type filter -->
        <select
          v-model="filterType"
          class="text-[11px] bg-[var(--color-tint)] border-none rounded-md px-2 py-1.5 text-[var(--color-text-secondary)] outline-none cursor-pointer"
        >
          <option v-for="opt in typeOptions" :key="opt.key" :value="opt.key">{{ opt.label }}</option>
        </select>

        <!-- Search -->
        <div class="flex-1 min-w-[120px]">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search agents or content..."
            class="w-full text-[11px] bg-[var(--color-tint)] border-none rounded-md px-2.5 py-1.5 text-[var(--color-text)] placeholder-[var(--color-text-muted)] outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
          />
        </div>
      </div>

      <!-- LLM model badge when transparency is on -->
      <div v-if="showThinking && llmModel" class="flex items-center gap-2 mt-2.5 px-2.5 py-1.5 rounded-md bg-[rgba(32,104,255,0.05)] border border-[rgba(32,104,255,0.1)]">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
        </svg>
        <span class="text-[10px] text-[var(--color-primary)] font-medium">
          {{ llmProvider || 'LLM' }} &middot; {{ llmModel }}
        </span>
        <button
          v-if="hasAgentFilter"
          class="ml-auto text-[10px] text-[var(--color-text-muted)] hover:text-[var(--color-primary)] transition-colors"
          @click="emit('clear-agent-filter')"
        >
          Clear agent filter
        </button>
      </div>
    </div>

    <!-- Feed body -->
    <div
      ref="feedContainer"
      class="flex-1 overflow-y-auto min-h-[240px] max-h-[400px]"
      @scroll="onFeedScroll"
    >
      <!-- Empty state -->
      <div
        v-if="!visibleActions.length"
        class="flex flex-col items-center justify-center h-[240px] text-[var(--color-text-muted)]"
      >
        <div class="text-3xl mb-2">&#x1F4E1;</div>
        <p class="text-sm">Waiting for agent activity...</p>
        <p class="text-xs mt-1">Posts, replies, likes, and reposts will stream here in real-time</p>
      </div>

      <!-- Action items -->
      <TransitionGroup v-else name="feed-item" tag="div" class="divide-y divide-[var(--color-border)]">
        <div
          v-for="(action, idx) in visibleActions"
          :key="`${action.round_num}-${action.agent_id}-${idx}`"
          class="px-4 py-2.5 hover:bg-[var(--color-tint)] transition-colors group"
        >
          <div class="flex items-start gap-2.5">
            <!-- Action icon -->
            <div
              class="w-8 h-8 rounded-lg border flex items-center justify-center text-sm shrink-0 mt-0.5"
              :class="actionColor(action.action_type)"
            >
              {{ actionIcon(action.action_type) }}
            </div>

            <!-- Content -->
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1.5 flex-wrap">
                <button
                  class="text-sm font-medium text-[var(--color-text)] hover:text-[var(--color-primary)] transition-colors text-left"
                  @click.stop="emit('select-agent', action)"
                >
                  {{ agentShortName(action.agent_name) }}
                </button>
                <span class="text-xs text-[var(--color-text-muted)] font-normal">{{ actionLabel(action.action_type) }}</span>
                <span
                  class="text-[10px] px-1.5 py-0.5 rounded-full font-medium"
                  :class="platformBadge(action.platform).cls"
                >
                  {{ platformBadge(action.platform).label }}
                </span>
                <span class="text-[10px] text-[var(--color-text-muted)]" :class="showThinking ? '' : 'ml-auto'" >R{{ action.round_num }}</span>
                <!-- Per-agent transparency toggle -->
                <button
                  v-if="showThinking"
                  class="ml-auto text-[10px] px-1.5 py-0.5 rounded transition-colors shrink-0"
                  :class="isAgentTransparent(action.agent_id)
                    ? 'text-[var(--color-primary)] bg-[rgba(32,104,255,0.08)]'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
                  @click.stop="emit('toggle-agent', action.agent_id)"
                  :title="isAgentTransparent(action.agent_id) ? 'Hide thinking for this agent' : 'Show thinking for this agent'"
                >
                  &#x1F4A1;
                </button>
              </div>

              <!-- Agent role subtitle -->
              <p v-if="agentRole(action.agent_name)" class="text-[10px] text-[var(--color-text-muted)] mt-0.5 truncate">
                {{ agentRole(action.agent_name) }}
              </p>

              <!-- Content preview -->
              <p
                v-if="action.action_args?.content"
                class="text-xs text-[var(--color-text-secondary)] mt-1 leading-relaxed"
              >
                {{ showThinking && isAgentTransparent(action.agent_id) ? action.action_args.content : truncate(action.action_args.content) }}
              </p>
            </div>
          </div>

          <!-- Reasoning trace (visible when transparency is on for this agent) -->
          <Transition name="reasoning">
            <div
              v-if="showThinking && isAgentTransparent(action.agent_id) && action.reasoning"
              class="ml-10 mt-2 pl-3 border-l-2 border-[rgba(32,104,255,0.2)] space-y-1.5"
            >
              <div class="flex items-start gap-1.5">
                <span class="text-[10px] font-semibold text-[var(--color-primary)] uppercase tracking-wider shrink-0 mt-px">Thought</span>
                <p class="text-[11px] text-[var(--color-text-muted)] leading-relaxed">{{ action.reasoning.thought }}</p>
              </div>
              <div class="flex items-start gap-1.5">
                <span class="text-[10px] font-semibold text-[#8b5cf6] uppercase tracking-wider shrink-0 mt-px">Action</span>
                <p class="text-[11px] text-[var(--color-text-muted)] leading-relaxed font-mono">{{ action.reasoning.action }}</p>
              </div>
              <div class="flex items-start gap-1.5">
                <span class="text-[10px] font-semibold text-emerald-600 uppercase tracking-wider shrink-0 mt-px">Result</span>
                <p class="text-[11px] text-[var(--color-text-muted)] leading-relaxed">{{ action.reasoning.observation }}</p>
              </div>
            </div>
          </Transition>
        </div>
      </TransitionGroup>
    </div>

    <!-- Footer with pause indicator -->
    <div
      v-if="visibleActions.length && !autoScroll"
      class="px-4 py-1.5 border-t border-[var(--color-border)] bg-[rgba(32,104,255,0.04)] text-center"
    >
      <button
        class="text-[11px] text-[var(--color-primary)] hover:underline"
        @click="scrollToBottom"
      >
        &#x2193; Scroll to latest ({{ props.actions.length - visibleActions.length + (visibleActions.length - feedContainer?.scrollTop ? 0 : 0) }} new)
      </button>
    </div>
  </div>
</template>

<style scoped>
.feed-item-enter-active {
  transition: all 0.3s ease-out;
}
.feed-item-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.feed-item-leave-active {
  transition: all 0.15s ease-in;
}
.feed-item-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
.feed-item-move {
  transition: transform 0.2s ease;
}
.reasoning-enter-active {
  transition: all 0.2s ease-out;
}
.reasoning-leave-active {
  transition: all 0.15s ease-in;
}
.reasoning-enter-from, .reasoning-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-4px);
}
.reasoning-enter-to, .reasoning-leave-from {
  opacity: 1;
  max-height: 200px;
}
</style>
