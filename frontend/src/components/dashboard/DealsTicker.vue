<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { dealsApi } from '@/api/deals'

const deals = ref([])
const loading = ref(true)
const error = ref(null)
const selectedDeal = ref(null)
const paused = ref(false)

async function fetchDeals() {
  try {
    const { data } = await dealsApi.recent(10)
    deals.value = data.deals || []
  } catch (e) {
    error.value = e.message || 'Failed to load deals'
  } finally {
    loading.value = false
  }
}

function statusColor(status) {
  if (status === 'won') return 'won'
  if (status === 'lost') return 'lost'
  return 'advanced'
}

function formatAmount(amount) {
  if (amount >= 1_000_000) return `$${(amount / 1_000_000).toFixed(1)}M`
  if (amount >= 1_000) return `$${(amount / 1_000).toFixed(0)}K`
  return `$${amount}`
}

function stageLabel(deal) {
  if (deal.status === 'won') return 'Won'
  if (deal.status === 'lost') return 'Lost'
  return `${deal.previous_stage} → ${deal.stage}`
}

function selectDeal(deal) {
  selectedDeal.value = selectedDeal.value?.id === deal.id ? null : deal
}

function dismissDetail() {
  selectedDeal.value = null
}

const tickerItems = computed(() => {
  if (!deals.value.length) return []
  return [...deals.value, ...deals.value]
})

let refreshInterval = null

onMounted(() => {
  fetchDeals()
  refreshInterval = setInterval(fetchDeals, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<template>
  <div class="deals-ticker" v-if="!loading || deals.length">
    <!-- Ticker bar -->
    <div
      class="ticker-track"
      :class="{ 'ticker-paused': paused || selectedDeal }"
      @mouseenter="paused = true"
      @mouseleave="paused = false"
    >
      <div class="ticker-content" v-if="deals.length">
        <button
          v-for="(deal, i) in tickerItems"
          :key="`${deal.id}-${i}`"
          class="ticker-item"
          :class="statusColor(deal.status)"
          @click="selectDeal(deal)"
        >
          <span class="ticker-dot" />
          <span class="ticker-company">{{ deal.company }}</span>
          <span class="ticker-stage">{{ stageLabel(deal) }}</span>
          <span class="ticker-amount">{{ formatAmount(deal.amount) }}</span>
        </button>
      </div>
    </div>

    <!-- Deal detail popover -->
    <Transition name="detail-fade">
      <div v-if="selectedDeal" class="deal-detail" @click.self="dismissDetail">
        <div class="deal-detail-card">
          <div class="deal-detail-header">
            <span class="deal-detail-company">{{ selectedDeal.company }}</span>
            <button class="deal-detail-close" @click="dismissDetail">&times;</button>
          </div>
          <div class="deal-detail-body">
            <div class="deal-detail-row">
              <span class="deal-detail-label">Stage</span>
              <span class="deal-detail-value" :class="statusColor(selectedDeal.status)">
                {{ stageLabel(selectedDeal) }}
              </span>
            </div>
            <div class="deal-detail-row">
              <span class="deal-detail-label">Amount</span>
              <span class="deal-detail-value">{{ formatAmount(selectedDeal.amount) }}</span>
            </div>
            <div class="deal-detail-row">
              <span class="deal-detail-label">When</span>
              <span class="deal-detail-value">{{ selectedDeal.minutes_ago }}m ago</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.deals-ticker {
  position: relative;
  width: 100%;
  overflow: hidden;
  background: var(--color-primary-lighter, rgba(32, 104, 255, 0.04));
  border-bottom: 1px solid var(--card-border, rgba(0, 0, 0, 0.06));
}

.ticker-track {
  overflow: hidden;
  white-space: nowrap;
}

.ticker-content {
  display: inline-flex;
  animation: ticker-scroll 30s linear infinite;
}

.ticker-paused .ticker-content {
  animation-play-state: paused;
}

@keyframes ticker-scroll {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-50%);
  }
}

.ticker-item {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  cursor: pointer;
  white-space: nowrap;
  font-size: 0.75rem;
  font-family: inherit;
  color: var(--color-text-secondary, #6b7280);
  transition: background 0.15s;
  border-right: 1px solid var(--card-border, rgba(0, 0, 0, 0.06));
}

.ticker-item:hover {
  background: var(--color-primary-light, rgba(32, 104, 255, 0.08));
}

.ticker-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.ticker-item.won .ticker-dot {
  background: var(--color-success, #009900);
}

.ticker-item.lost .ticker-dot {
  background: var(--color-error, #ef4444);
}

.ticker-item.advanced .ticker-dot {
  background: var(--color-primary, #2068FF);
}

.ticker-company {
  font-weight: 600;
  color: var(--color-text-primary, #1a1a1a);
}

.ticker-stage {
  color: var(--color-text-secondary, #6b7280);
}

.ticker-item.won .ticker-stage {
  color: var(--color-success, #009900);
}

.ticker-item.lost .ticker-stage {
  color: var(--color-error, #ef4444);
}

.ticker-item.advanced .ticker-stage {
  color: var(--color-primary, #2068FF);
}

.ticker-amount {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--color-text-primary, #1a1a1a);
}

/* Deal detail popover */
.deal-detail {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 50;
  padding: 0.5rem;
  display: flex;
  justify-content: center;
}

.deal-detail-card {
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.06));
  border-radius: var(--card-radius, 0.75rem);
  box-shadow: var(--shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.1));
  padding: 0.75rem 1rem;
  min-width: 240px;
  max-width: 320px;
}

.deal-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.deal-detail-company {
  font-weight: 700;
  font-size: 0.875rem;
  color: var(--color-text-primary, #1a1a1a);
}

.deal-detail-close {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 1.125rem;
  color: var(--color-text-secondary, #6b7280);
  padding: 0;
  line-height: 1;
}

.deal-detail-close:hover {
  color: var(--color-text-primary, #1a1a1a);
}

.deal-detail-body {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.deal-detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
}

.deal-detail-label {
  color: var(--color-text-secondary, #6b7280);
}

.deal-detail-value {
  font-weight: 600;
  color: var(--color-text-primary, #1a1a1a);
}

.deal-detail-value.won {
  color: var(--color-success, #009900);
}

.deal-detail-value.lost {
  color: var(--color-error, #ef4444);
}

.deal-detail-value.advanced {
  color: var(--color-primary, #2068FF);
}

/* Transition */
.detail-fade-enter-active,
.detail-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.detail-fade-enter-from,
.detail-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Dark mode */
:root.dark .deals-ticker,
.dark .deals-ticker {
  background: rgba(32, 104, 255, 0.06);
  border-bottom-color: rgba(255, 255, 255, 0.08);
}

:root.dark .ticker-item,
.dark .ticker-item {
  border-right-color: rgba(255, 255, 255, 0.06);
}

:root.dark .ticker-item:hover,
.dark .ticker-item:hover {
  background: rgba(32, 104, 255, 0.12);
}
</style>
