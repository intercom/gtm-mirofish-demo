<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useToast } from '../composables/useToast'
import ExecutiveKpis from '../components/dashboard/ExecutiveKpis.vue'
import HealthScorecard from '../components/dashboard/HealthScorecard.vue'
import RevenuePipelineChart from '../components/dashboard/RevenuePipelineChart.vue'
import ActivityFeed from '../components/dashboard/ActivityFeed.vue'
import DealVelocity from '../components/dashboard/DealVelocity.vue'
import FunnelSummaryWidget from '../components/dashboard/FunnelSummaryWidget.vue'

const toast = useToast()
const refreshing = ref(false)
const dateRange = ref('last-30d')
const expandedSections = ref(new Set(['kpis', 'revenue', 'health', 'funnel']))

const dateRangeOptions = [
  { value: 'last-7d', label: '7d' },
  { value: 'last-30d', label: '30d' },
  { value: 'last-90d', label: '90d' },
  { value: 'ytd', label: 'YTD' },
]

function toggleSection(key) {
  if (expandedSections.value.has(key)) {
    expandedSections.value.delete(key)
  } else {
    expandedSections.value.add(key)
  }
}

function isExpanded(key) {
  return expandedSections.value.has(key)
}

// Pull-to-refresh
const pullStartY = ref(0)
const pullDistance = ref(0)
const isPulling = ref(false)
const scrollContainer = ref(null)
const PULL_THRESHOLD = 80

function onTouchStart(e) {
  if (scrollContainer.value?.scrollTop > 0) return
  pullStartY.value = e.touches[0].clientY
  isPulling.value = true
}

function onTouchMove(e) {
  if (!isPulling.value) return
  const y = e.touches[0].clientY
  const dist = y - pullStartY.value
  if (dist > 0 && scrollContainer.value?.scrollTop === 0) {
    pullDistance.value = Math.min(dist * 0.5, 120)
    if (pullDistance.value > 10) {
      e.preventDefault()
    }
  } else {
    pullDistance.value = 0
  }
}

async function onTouchEnd() {
  if (!isPulling.value) return
  isPulling.value = false
  if (pullDistance.value >= PULL_THRESHOLD) {
    await refresh()
  }
  pullDistance.value = 0
}

async function refresh() {
  refreshing.value = true
  await new Promise(r => setTimeout(r, 600))
  refreshing.value = false
  toast.info('Dashboard refreshed')
}

// Auto-refresh every 60s
let autoRefreshTimer = null
onMounted(() => {
  autoRefreshTimer = setInterval(() => {
    // Silently re-render (components with ResizeObservers will adapt)
  }, 60000)
})
onUnmounted(() => {
  clearInterval(autoRefreshTimer)
})
</script>

<template>
  <div class="mobile-dashboard">
    <!-- Pull-to-refresh indicator -->
    <div
      class="pull-indicator"
      :style="{ height: pullDistance + 'px', opacity: pullDistance / PULL_THRESHOLD }"
    >
      <div class="pull-spinner" :class="{ 'pull-spinner--active': pullDistance >= PULL_THRESHOLD }">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
        </svg>
      </div>
    </div>

    <!-- Sticky header -->
    <header class="mobile-header">
      <div class="mobile-header__top">
        <h1 class="mobile-header__title">Dashboard</h1>
        <button
          @click="refresh"
          class="mobile-header__refresh"
          :class="{ 'mobile-header__refresh--active': refreshing }"
          :disabled="refreshing"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
          </svg>
        </button>
      </div>
      <div class="mobile-header__filters">
        <button
          v-for="opt in dateRangeOptions"
          :key="opt.value"
          @click="dateRange = opt.value"
          class="date-chip"
          :class="{ 'date-chip--active': dateRange === opt.value }"
        >
          {{ opt.label }}
        </button>
      </div>
    </header>

    <!-- Scrollable content -->
    <div
      ref="scrollContainer"
      class="mobile-content"
      @touchstart.passive="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
    >
      <!-- Loading overlay -->
      <div v-if="refreshing" class="refresh-overlay">
        <div class="refresh-spinner" />
      </div>

      <!-- KPI Strip — horizontal scroll -->
      <section class="mobile-section">
        <ExecutiveKpis />
      </section>

      <!-- Revenue & Pipeline -->
      <section class="mobile-section">
        <button class="section-toggle" @click="toggleSection('revenue')">
          <span class="section-toggle__label">Revenue & Pipeline</span>
          <svg
            class="section-toggle__chevron"
            :class="{ 'section-toggle__chevron--open': isExpanded('revenue') }"
            width="16" height="16" viewBox="0 0 16 16" fill="currentColor"
          >
            <path d="M4.646 5.646a.5.5 0 01.708 0L8 8.293l2.646-2.647a.5.5 0 01.708.708l-3 3a.5.5 0 01-.708 0l-3-3a.5.5 0 010-.708z" />
          </svg>
        </button>
        <Transition name="section-expand">
          <div v-if="isExpanded('revenue')" class="section-body">
            <RevenuePipelineChart />
          </div>
        </Transition>
      </section>

      <!-- Health Scorecard -->
      <section class="mobile-section">
        <button class="section-toggle" @click="toggleSection('health')">
          <span class="section-toggle__label">GTM Health</span>
          <svg
            class="section-toggle__chevron"
            :class="{ 'section-toggle__chevron--open': isExpanded('health') }"
            width="16" height="16" viewBox="0 0 16 16" fill="currentColor"
          >
            <path d="M4.646 5.646a.5.5 0 01.708 0L8 8.293l2.646-2.647a.5.5 0 01.708.708l-3 3a.5.5 0 01-.708 0l-3-3a.5.5 0 010-.708z" />
          </svg>
        </button>
        <Transition name="section-expand">
          <div v-if="isExpanded('health')" class="section-body">
            <HealthScorecard />
          </div>
        </Transition>
      </section>

      <!-- Pipeline Funnel -->
      <section class="mobile-section">
        <button class="section-toggle" @click="toggleSection('funnel')">
          <span class="section-toggle__label">Pipeline Funnel</span>
          <svg
            class="section-toggle__chevron"
            :class="{ 'section-toggle__chevron--open': isExpanded('funnel') }"
            width="16" height="16" viewBox="0 0 16 16" fill="currentColor"
          >
            <path d="M4.646 5.646a.5.5 0 01.708 0L8 8.293l2.646-2.647a.5.5 0 01.708.708l-3 3a.5.5 0 01-.708 0l-3-3a.5.5 0 010-.708z" />
          </svg>
        </button>
        <Transition name="section-expand">
          <div v-if="isExpanded('funnel')" class="section-body">
            <FunnelSummaryWidget />
          </div>
        </Transition>
      </section>

      <!-- Deal Velocity -->
      <section class="mobile-section">
        <button class="section-toggle" @click="toggleSection('velocity')">
          <span class="section-toggle__label">Deal Velocity</span>
          <svg
            class="section-toggle__chevron"
            :class="{ 'section-toggle__chevron--open': isExpanded('velocity') }"
            width="16" height="16" viewBox="0 0 16 16" fill="currentColor"
          >
            <path d="M4.646 5.646a.5.5 0 01.708 0L8 8.293l2.646-2.647a.5.5 0 01.708.708l-3 3a.5.5 0 01-.708 0l-3-3a.5.5 0 010-.708z" />
          </svg>
        </button>
        <Transition name="section-expand">
          <div v-if="isExpanded('velocity')" class="section-body">
            <DealVelocity />
          </div>
        </Transition>
      </section>

      <!-- Activity Feed -->
      <section class="mobile-section mobile-section--feed">
        <button class="section-toggle" @click="toggleSection('activity')">
          <span class="section-toggle__label">Activity Feed</span>
          <svg
            class="section-toggle__chevron"
            :class="{ 'section-toggle__chevron--open': isExpanded('activity') }"
            width="16" height="16" viewBox="0 0 16 16" fill="currentColor"
          >
            <path d="M4.646 5.646a.5.5 0 01.708 0L8 8.293l2.646-2.647a.5.5 0 01.708.708l-3 3a.5.5 0 01-.708 0l-3-3a.5.5 0 010-.708z" />
          </svg>
        </button>
        <Transition name="section-expand">
          <div v-if="isExpanded('activity')" class="section-body section-body--feed">
            <ActivityFeed />
          </div>
        </Transition>
      </section>

      <!-- Bottom spacer for MobileNav -->
      <div class="mobile-bottom-spacer" />
    </div>
  </div>
</template>

<style scoped>
.mobile-dashboard {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: var(--color-bg);
  position: relative;
}

/* ── Pull-to-refresh ──────────────────────────────── */
.pull-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.pull-spinner {
  color: var(--color-text-muted);
  transition: transform 0.2s ease;
}

.pull-spinner--active {
  color: var(--color-primary);
  transform: rotate(180deg);
}

/* ── Sticky header ────────────────────────────────── */
.mobile-header {
  position: sticky;
  top: 0;
  z-index: 20;
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  padding: 0.75rem 1rem 0.625rem;
  flex-shrink: 0;
}

.mobile-header__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.mobile-header__title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
}

.mobile-header__refresh {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
  -webkit-tap-highlight-color: transparent;
}

.mobile-header__refresh:active {
  transform: scale(0.92);
}

.mobile-header__refresh--active {
  color: var(--color-primary);
  border-color: rgba(32, 104, 255, 0.3);
}

.mobile-header__refresh--active svg {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ── Date range chips ─────────────────────────────── */
.mobile-header__filters {
  display: flex;
  gap: 0.375rem;
}

.date-chip {
  flex: 1;
  padding: 0.375rem 0;
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  -webkit-tap-highlight-color: transparent;
}

.date-chip:active {
  transform: scale(0.96);
}

.date-chip--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

/* ── Scrollable content ───────────────────────────── */
.mobile-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
  position: relative;
}

.refresh-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.6);
  z-index: 10;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 2rem;
}

.dark .refresh-overlay {
  background: rgba(10, 10, 26, 0.6);
}

.refresh-spinner {
  width: 24px;
  height: 24px;
  border: 2.5px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* ── Sections ─────────────────────────────────────── */
.mobile-section {
  padding: 0 0.75rem;
  margin-bottom: 0.5rem;
}

.mobile-section:first-child {
  padding-top: 0.75rem;
}

.mobile-section--feed {
  /* Give feed section a fixed max height so it doesn't take over the page */
}

/* ── Section toggle (accordion header) ────────────── */
.section-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0.625rem 0.25rem;
  background: none;
  border: none;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.section-toggle__label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.section-toggle__chevron {
  color: var(--color-text-muted);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.section-toggle__chevron--open {
  transform: rotate(180deg);
}

/* ── Section body ─────────────────────────────────── */
.section-body {
  padding-bottom: 0.25rem;
}

.section-body--feed {
  max-height: 400px;
  overflow: hidden;
}

/* ── Section expand/collapse transition ───────────── */
.section-expand-enter-active {
  transition: all 0.25s ease-out;
  overflow: hidden;
}

.section-expand-leave-active {
  transition: all 0.2s ease-in;
  overflow: hidden;
}

.section-expand-enter-from,
.section-expand-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-8px);
}

.section-expand-enter-to,
.section-expand-leave-from {
  opacity: 1;
  max-height: 800px;
}

/* ── Bottom spacer for MobileNav ──────────────────── */
.mobile-bottom-spacer {
  height: calc(1rem + env(safe-area-inset-bottom, 0px));
}

/* ── Desktop: redirect visual hint ────────────────── */
@media (min-width: 768px) {
  .mobile-header {
    padding: 1rem 1.5rem 0.75rem;
  }

  .mobile-section {
    padding: 0 1.5rem;
    max-width: 640px;
    margin-left: auto;
    margin-right: auto;
  }

  .mobile-section:first-child {
    padding-top: 1rem;
  }

  .mobile-header__filters {
    max-width: 320px;
  }
}
</style>
