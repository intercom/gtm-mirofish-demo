<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'

const CATEGORIES = [
  { key: 'all', label: 'All' },
  { key: 'deal', label: 'Deals' },
  { key: 'lead', label: 'Leads' },
  { key: 'risk', label: 'Risk' },
  { key: 'milestone', label: 'Milestones' },
]

const CATEGORY_META = {
  deal: { icon: '💰', badge: 'Deal', badgeClass: 'badge-success' },
  lead: { icon: '🎯', badge: 'Lead', badgeClass: 'badge-primary' },
  risk: { icon: '⚠️', badge: 'Risk', badgeClass: 'badge-error' },
  milestone: { icon: '🏆', badge: 'Milestone', badgeClass: 'badge-orange' },
}

function generateEvents() {
  const now = Date.now()
  const raw = [
    { type: 'deal', message: 'Acme Corp closed for $120K', hoursAgo: 2 },
    { type: 'lead', message: 'Lead scored 85+ from Campaign X', hoursAgo: 5 },
    { type: 'risk', message: 'Renewal at risk: BigCo health score dropped to 35', hoursAgo: 8 },
    { type: 'milestone', message: 'Q4 pipeline target 80% achieved', hoursAgo: 14 },
    { type: 'deal', message: 'TechStart Inc. advanced to Negotiation — $85K', hoursAgo: 22 },
    { type: 'lead', message: '12 new MQLs from webinar "AI in GTM"', hoursAgo: 28 },
    { type: 'risk', message: 'Churn signal: DataFlow usage down 40% this month', hoursAgo: 36 },
    { type: 'deal', message: 'CloudBase signed 2-year expansion — $210K', hoursAgo: 44 },
    { type: 'milestone', message: 'Sales team hit 100 qualified meetings this quarter', hoursAgo: 52 },
    { type: 'lead', message: 'VP Engineering at Stripe requested demo', hoursAgo: 60 },
    { type: 'risk', message: 'NovaTech support tickets spiked 3x — escalation needed', hoursAgo: 68 },
    { type: 'deal', message: 'Pinnacle Group contract renewed — $95K ARR', hoursAgo: 76 },
    { type: 'lead', message: 'Inbound lead from G2 review: "Best in class"', hoursAgo: 84 },
    { type: 'milestone', message: 'NRR crossed 115% for the first time', hoursAgo: 92 },
    { type: 'deal', message: 'SkyBridge moved to Closed Won — $67K', hoursAgo: 100 },
    { type: 'risk', message: 'Champion left at MegaCorp — renewal at risk', hoursAgo: 110 },
    { type: 'lead', message: 'SDR booked 8 meetings from LinkedIn outreach', hoursAgo: 120 },
    { type: 'deal', message: 'Greenfield upsold to Enterprise tier — +$45K', hoursAgo: 132 },
    { type: 'milestone', message: 'Win rate improved to 32% (up from 28%)', hoursAgo: 148 },
    { type: 'risk', message: 'HealthScore alert: 3 accounts dropped below 40', hoursAgo: 160 },
  ]

  return raw.map((e, i) => ({
    id: i + 1,
    type: e.type,
    message: e.message,
    timestamp: new Date(now - e.hoursAgo * 3600000),
    ...CATEGORY_META[e.type],
  }))
}

const activeFilter = ref('all')
const feedRef = ref(null)
const events = ref(generateEvents())

const filteredEvents = computed(() => {
  if (activeFilter.value === 'all') return events.value
  return events.value.filter((e) => e.type === activeFilter.value)
})

function formatTime(date) {
  const diff = Date.now() - date.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function setFilter(key) {
  activeFilter.value = key
  nextTick(() => {
    if (feedRef.value) feedRef.value.scrollTop = 0
  })
}

onMounted(() => {
  if (feedRef.value) feedRef.value.scrollTop = 0
})
</script>

<template>
  <div class="activity-feed flex flex-col h-full">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Activity Feed</h3>
      <span class="text-xs text-[var(--color-text-muted)]">{{ filteredEvents.length }} events</span>
    </div>

    <!-- Filter chips -->
    <div class="flex gap-1.5 mb-3 flex-wrap">
      <button
        v-for="cat in CATEGORIES"
        :key="cat.key"
        @click="setFilter(cat.key)"
        class="px-2.5 py-1 text-xs rounded-full transition-colors border"
        :class="
          activeFilter === cat.key
            ? 'bg-[var(--color-primary)] text-white border-transparent'
            : 'bg-[var(--color-primary-lighter)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:bg-[var(--color-primary-light)]'
        "
      >
        {{ cat.label }}
      </button>
    </div>

    <!-- Events list -->
    <div ref="feedRef" class="flex-1 overflow-y-auto min-h-0 -mx-1 px-1">
      <TransitionGroup name="feed-item" tag="div" class="flex flex-col gap-1">
        <div
          v-for="event in filteredEvents"
          :key="event.id"
          class="flex items-start gap-2.5 p-2.5 rounded-lg hover:bg-[var(--color-tint)] transition-colors"
        >
          <span class="text-base leading-none mt-0.5 shrink-0">{{ event.icon }}</span>
          <div class="flex-1 min-w-0">
            <p class="text-xs text-[var(--color-text)] leading-relaxed">{{ event.message }}</p>
            <div class="flex items-center gap-2 mt-1">
              <span
                class="inline-block px-1.5 py-px text-[10px] font-medium rounded-full"
                :class="event.badgeClass"
              >
                {{ event.badge }}
              </span>
              <span class="text-[10px] text-[var(--color-text-muted)]">{{ formatTime(event.timestamp) }}</span>
            </div>
          </div>
        </div>
      </TransitionGroup>

      <div
        v-if="filteredEvents.length === 0"
        class="flex flex-col items-center justify-center py-8 text-center"
      >
        <span class="text-2xl mb-2">📭</span>
        <p class="text-xs text-[var(--color-text-muted)]">No events in this category</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.badge-success {
  background: var(--badge-success-bg-soft);
  color: var(--badge-success-text-soft, var(--color-success));
}
.badge-primary {
  background: var(--badge-secondary-bg);
  color: var(--badge-secondary-text, var(--color-primary));
}
.badge-error {
  background: var(--badge-error-bg-soft);
  color: var(--badge-error-text-soft, var(--color-error));
}
.badge-orange {
  background: var(--badge-orange-bg-soft);
  color: var(--badge-orange-text-soft, var(--color-fin-orange));
}

/* TransitionGroup: new events slide in from top */
.feed-item-enter-active {
  transition: all 0.3s ease;
}
.feed-item-leave-active {
  transition: all 0.2s ease;
}
.feed-item-enter-from {
  opacity: 0;
  transform: translateY(-12px);
}
.feed-item-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
.feed-item-move {
  transition: transform 0.3s ease;
}
</style>
