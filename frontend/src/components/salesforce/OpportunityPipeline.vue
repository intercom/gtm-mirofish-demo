<script setup>
import { computed } from 'vue'

const props = defineProps({
  opportunities: {
    type: Array,
    default: () => [],
  },
})

const STAGES = [
  { key: 'Prospecting', color: '#2068FF', bgTint: 'rgba(32, 104, 255, 0.08)' },
  { key: 'Discovery', color: '#1a5ae0', bgTint: 'rgba(26, 90, 224, 0.08)' },
  { key: 'Proposal', color: '#1550cc', bgTint: 'rgba(21, 80, 204, 0.08)' },
  { key: 'Negotiation', color: '#009900', bgTint: 'rgba(0, 153, 0, 0.08)' },
  { key: 'Closed Won', color: '#009900', bgTint: 'rgba(0, 153, 0, 0.08)' },
  { key: 'Closed Lost', color: '#ef4444', bgTint: 'rgba(239, 68, 68, 0.08)' },
]

const DEMO_OPPORTUNITIES = [
  { id: 1, name: 'Acme Corp — Expert Upgrade', account: 'Acme Corp', stage: 'Prospecting', amount: 84000, close_date: '2026-05-15', probability: 20 },
  { id: 2, name: 'Globex Platform Deal', account: 'Globex Inc', stage: 'Prospecting', amount: 126000, close_date: '2026-06-01', probability: 15 },
  { id: 3, name: 'Soylent — Advanced Seats', account: 'Soylent Green', stage: 'Discovery', amount: 47500, close_date: '2026-04-22', probability: 35 },
  { id: 4, name: 'Initech Support Bundle', account: 'Initech', stage: 'Discovery', amount: 63000, close_date: '2026-05-10', probability: 40 },
  { id: 5, name: 'Wayne Enterprises Fin AI', account: 'Wayne Enterprises', stage: 'Discovery', amount: 210000, close_date: '2026-04-30', probability: 30 },
  { id: 6, name: 'Stark Industries Renewal', account: 'Stark Industries', stage: 'Proposal', amount: 175000, close_date: '2026-04-18', probability: 60 },
  { id: 7, name: 'Umbrella Corp Migration', account: 'Umbrella Corp', stage: 'Proposal', amount: 92000, close_date: '2026-04-25', probability: 55 },
  { id: 8, name: 'Wonka — Enterprise Expansion', account: 'Wonka Industries', stage: 'Negotiation', amount: 340000, close_date: '2026-04-10', probability: 75 },
  { id: 9, name: 'Cyberdyne — Expert 500-seat', account: 'Cyberdyne Systems', stage: 'Negotiation', amount: 278000, close_date: '2026-04-12', probability: 80 },
  { id: 10, name: 'Oscorp Annual Contract', account: 'Oscorp', stage: 'Negotiation', amount: 156000, close_date: '2026-04-08', probability: 70 },
  { id: 11, name: 'Tyrell Corp — Full Suite', account: 'Tyrell Corporation', stage: 'Closed Won', amount: 420000, close_date: '2026-03-20', probability: 100 },
  { id: 12, name: 'Nakatomi Advanced Rollout', account: 'Nakatomi Trading', stage: 'Closed Won', amount: 89000, close_date: '2026-03-15', probability: 100 },
  { id: 13, name: 'Massive Dynamic — Proactive', account: 'Massive Dynamic', stage: 'Closed Won', amount: 195000, close_date: '2026-03-22', probability: 100 },
  { id: 14, name: 'Weyland-Yutani Evaluation', account: 'Weyland-Yutani', stage: 'Closed Lost', amount: 310000, close_date: '2026-03-28', probability: 0 },
  { id: 15, name: 'LexCorp Pilot Program', account: 'LexCorp', stage: 'Closed Lost', amount: 55000, close_date: '2026-03-25', probability: 0 },
]

const data = computed(() =>
  props.opportunities.length > 0 ? props.opportunities : DEMO_OPPORTUNITIES,
)

const columns = computed(() =>
  STAGES.map((stage) => {
    const items = data.value.filter((o) => o.stage === stage.key)
    const total = items.reduce((sum, o) => sum + (o.amount || 0), 0)
    return { ...stage, items, count: items.length, total }
  }),
)

function formatCurrency(value) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value.toLocaleString()}`
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="pipeline-board">
    <div
      v-for="col in columns"
      :key="col.key"
      class="pipeline-column"
    >
      <div class="column-header" :style="{ borderTopColor: col.color }">
        <div class="column-title-row">
          <span class="column-title">{{ col.key }}</span>
          <span class="column-count">{{ col.count }}</span>
        </div>
        <span class="column-total">{{ formatCurrency(col.total) }}</span>
      </div>

      <div class="column-body">
        <div
          v-for="opp in col.items"
          :key="opp.id"
          class="opp-card"
        >
          <div class="opp-name">{{ opp.name }}</div>
          <div class="opp-account">{{ opp.account }}</div>
          <div class="opp-meta">
            <span class="opp-amount">{{ formatCurrency(opp.amount) }}</span>
            <span class="opp-date">{{ formatDate(opp.close_date) }}</span>
          </div>
          <div class="opp-probability">
            <div class="prob-bar-bg">
              <div
                class="prob-bar-fill"
                :style="{ width: opp.probability + '%', backgroundColor: col.color }"
              />
            </div>
            <span class="prob-label">{{ opp.probability }}%</span>
          </div>
        </div>

        <div v-if="col.items.length === 0" class="empty-col">
          No opportunities
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pipeline-board {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: var(--space-3);
  min-height: 400px;
}

@media (max-width: 1200px) {
  .pipeline-board {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 640px) {
  .pipeline-board {
    grid-template-columns: 1fr;
  }
}

.pipeline-column {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.column-header {
  border-top: 3px solid;
  background: var(--card-bg);
  border-radius: var(--radius) var(--radius) 0 0;
  padding: var(--space-3) var(--space-3) var(--space-2);
  border-left: 1px solid var(--color-border);
  border-right: 1px solid var(--color-border);
}

.column-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.column-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.column-count {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: var(--radius-full);
  background: var(--color-tint);
  font-size: 0.6875rem;
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
}

.column-total {
  display: block;
  margin-top: 2px;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-weight: var(--font-medium);
}

.column-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-2);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-top: none;
  border-radius: 0 0 var(--radius) var(--radius);
  min-height: 120px;
}

.opp-card {
  background: var(--card-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: var(--space-3);
  cursor: default;
  transition: box-shadow var(--transition-fast), border-color var(--transition-fast);
}

.opp-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-strong);
}

.opp-name {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  line-height: var(--leading-tight);
  margin-bottom: 2px;
}

.opp-account {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-bottom: var(--space-2);
}

.opp-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
}

.opp-amount {
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
  color: var(--color-text);
}

.opp-date {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.opp-probability {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.prob-bar-bg {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: var(--color-tint);
  overflow: hidden;
}

.prob-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width var(--transition-base);
}

.prob-label {
  flex-shrink: 0;
  font-size: 0.6875rem;
  color: var(--color-text-muted);
  font-weight: var(--font-medium);
  min-width: 28px;
  text-align: right;
}

.empty-col {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  padding: var(--space-4);
}
</style>
