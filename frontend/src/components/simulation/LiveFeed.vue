<script setup>
import { ref, computed, inject, watch, nextTick } from 'vue'

const polling = inject('polling')

const feedContainer = ref(null)
const autoScroll = ref(true)

const actions = computed(() => polling.recentActions.value || [])

function actionIcon(actionType) {
  const t = (actionType || '').toUpperCase()
  if (t.includes('POST') || t.includes('CREATE')) return '\uD83D\uDCDD'
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

function platformBadge(platform) {
  return platform === 'twitter'
    ? { label: 'Twitter', class: 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]' }
    : { label: 'Reddit', class: 'bg-[var(--color-fin-orange-tint)] text-[var(--color-fin-orange)]' }
}

function truncate(str, len = 160) {
  if (!str || str.length <= len) return str || ''
  return str.slice(0, len) + '\u2026'
}

function onFeedScroll() {
  const el = feedContainer.value
  if (!el) return
  autoScroll.value = (el.scrollHeight - el.scrollTop - el.clientHeight) < 50
}

watch(() => actions.value.length, () => {
  if (autoScroll.value && feedContainer.value) {
    nextTick(() => {
      feedContainer.value.scrollTop = feedContainer.value.scrollHeight
    })
  }
})
</script>

<template>
  <div class="flex flex-col h-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
    <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)]">
      <div class="flex items-center gap-2">
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Live Feed</h3>
        <span
          v-if="polling.simStatus.value === 'running'"
          class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-red-500/10 text-red-500"
        >
          <span class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          Live
        </span>
      </div>
      <span class="text-xs text-[var(--color-text-muted)]">{{ actions.length }} messages</span>
    </div>

    <div
      v-if="actions.length"
      ref="feedContainer"
      class="flex-1 overflow-y-auto px-4 py-2"
      @scroll="onFeedScroll"
    >
      <div
        v-for="(action, idx) in actions.slice(0, 100)"
        :key="idx"
        class="flex items-start gap-2.5 py-2.5 border-b border-[var(--color-border)] last:border-0"
      >
        <span class="text-base mt-0.5 shrink-0">{{ actionIcon(action.action_type) }}</span>
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-sm font-medium text-[var(--color-text)]">
              {{ action.agent_name || `Agent #${action.agent_id}` }}
            </span>
            <span class="text-xs px-1.5 py-0.5 rounded-full" :class="platformBadge(action.platform).class">
              {{ platformBadge(action.platform).label }}
            </span>
            <span class="text-xs text-[var(--color-text-muted)]">R{{ action.round_num }}</span>
          </div>
          <p class="text-xs text-[var(--color-text-secondary)] mt-0.5">
            {{ actionLabel(action.action_type) }}
            <span v-if="action.action_args?.content" class="text-[var(--color-text-muted)]">
              &mdash; {{ truncate(action.action_args.content) }}
            </span>
          </p>
        </div>
      </div>
    </div>

    <div v-else class="flex-1 flex flex-col items-center justify-center text-[var(--color-text-muted)] px-4">
      <p class="text-3xl mb-2">&#x1F4E1;</p>
      <p class="text-sm">Waiting for agent messages...</p>
      <p class="text-xs mt-1">Real-time posts, replies, and reactions will stream here</p>
    </div>
  </div>
</template>
