<script setup>
import { computed } from 'vue'
import { usePresenceStore } from '../../stores/presence'

const store = usePresenceStore()

const recentEvents = computed(() =>
  [...store.events].reverse().slice(0, 15),
)

function timeAgo(ts) {
  const diff = Math.floor(Date.now() / 1000 - ts)
  if (diff < 5) return 'just now'
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  return `${Math.floor(diff / 3600)}h ago`
}

const EVENT_ICONS = {
  join: '→',
  leave: '←',
  navigate: '⬡',
  status_change: '◆',
}
</script>

<template>
  <div class="presence-panel rounded-xl border border-white/10 bg-[#050505]/80 backdrop-blur-sm overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-white/10">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <span class="text-sm font-medium text-white">Team Activity</span>
      </div>
      <span class="text-xs text-white/40 tabular-nums">{{ store.totalOnline }} online</span>
    </div>

    <!-- Online users -->
    <div class="px-4 py-3 space-y-2 border-b border-white/5">
      <div
        v-for="user in store.users"
        :key="user.id"
        class="flex items-center gap-2.5 group"
      >
        <div
          class="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-semibold text-white shrink-0 ring-1 ring-white/10"
          :style="{ backgroundColor: user.color }"
        >
          {{ user.initials }}
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-1.5">
            <span class="text-xs font-medium text-white truncate">{{ user.name }}</span>
            <span
              v-if="user.is_typing"
              class="text-[10px] text-emerald-400 animate-pulse"
            >typing...</span>
          </div>
          <div class="text-[10px] text-white/30 truncate">
            {{ user.activity }} · {{ user.current_page }}
          </div>
        </div>
        <span
          class="w-1.5 h-1.5 rounded-full shrink-0"
          :class="{
            'bg-emerald-500': user.status === 'active',
            'bg-blue-400': user.status === 'viewing',
            'bg-amber-400': user.status === 'editing',
            'bg-white/20': user.status === 'idle',
          }"
        />
      </div>
    </div>

    <!-- Activity feed -->
    <div class="px-4 py-3 space-y-1.5 max-h-48 overflow-y-auto">
      <div class="text-[10px] text-white/25 uppercase tracking-wider mb-2">Recent Activity</div>
      <div
        v-for="(event, i) in recentEvents"
        :key="i"
        class="flex items-start gap-2 text-[11px]"
      >
        <span class="text-white/20 shrink-0 mt-px">{{ EVENT_ICONS[event.type] || '·' }}</span>
        <span class="text-white/50 flex-1">{{ event.details }}</span>
        <span class="text-white/20 tabular-nums shrink-0">{{ timeAgo(event.timestamp) }}</span>
      </div>
      <div v-if="!recentEvents.length" class="text-[11px] text-white/20 italic">
        No activity yet
      </div>
    </div>
  </div>
</template>

<style scoped>
.presence-panel {
  width: 100%;
  max-width: 280px;
}
</style>
