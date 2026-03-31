<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSimulationStore } from '../../stores/simulation'

const route = useRoute()
const router = useRouter()
const simulationStore = useSimulationStore()
const drawerOpen = ref(false)

const primaryTabs = [
  { to: '/', label: 'Home', icon: 'home', exact: true },
  { to: '/scenarios', label: 'Scenarios', icon: 'scenarios', exact: true },
  { to: '/simulations', label: 'Sims', icon: 'simulations', exact: false },
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard', exact: false },
]

const drawerSections = [
  {
    title: 'Explore',
    items: [
      { to: '/marketplace', label: 'Marketplace', icon: 'marketplace' },
      { to: '/knowledge-graph', label: 'Knowledge Graph', icon: 'graph' },
      { to: '/agents', label: 'Agents', icon: 'agents' },
    ],
  },
  {
    title: 'Analyze',
    items: [
      { to: '/analytics', label: 'Analytics', icon: 'analytics' },
      { to: '/visualizations', label: 'Visualizations', icon: 'visualizations' },
      { to: '/charts', label: 'Charts Gallery', icon: 'charts' },
      { to: '/comparison', label: 'Comparison', icon: 'comparison' },
    ],
  },
  {
    title: 'System',
    items: [
      { to: '/api-docs', label: 'API Docs', icon: 'api' },
      { to: '/settings', label: 'Settings', icon: 'settings' },
    ],
  },
]

function isTabActive(item) {
  if (item.exact) return route.path === item.to
  return route.path.startsWith(item.to)
}

const isMoreActive = computed(() => {
  const primaryPaths = primaryTabs.map(t => t.to)
  if (primaryPaths.some(p => p === '/' ? route.path === '/' : route.path.startsWith(p))) return false
  return route.path !== '/'
})

function navigateTo(to) {
  drawerOpen.value = false
  router.push(to)
}

watch(() => route.path, () => {
  drawerOpen.value = false
})
</script>

<template>
  <!-- Backdrop -->
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="drawerOpen"
      class="mobile-nav-backdrop md:hidden"
      @click="drawerOpen = false"
    />
  </Transition>

  <!-- Drawer -->
  <Transition
    enter-active-class="transition duration-250 ease-out"
    enter-from-class="translate-y-full"
    enter-to-class="translate-y-0"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="translate-y-0"
    leave-to-class="translate-y-full"
  >
    <div v-if="drawerOpen" class="mobile-nav-drawer md:hidden">
      <div class="mobile-nav-drawer__handle" @click="drawerOpen = false">
        <span class="mobile-nav-drawer__pill" />
      </div>

      <div class="mobile-nav-drawer__content">
        <div
          v-for="section in drawerSections"
          :key="section.title"
          class="mobile-nav-drawer__section"
        >
          <h3 class="mobile-nav-drawer__heading">{{ section.title }}</h3>
          <button
            v-for="item in section.items"
            :key="item.to"
            class="mobile-nav-drawer__item"
            :class="{ 'mobile-nav-drawer__item--active': route.path.startsWith(item.to) }"
            @click="navigateTo(item.to)"
          >
            <!-- Marketplace -->
            <svg v-if="item.icon === 'marketplace'" class="mobile-nav-drawer__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z" /><line x1="3" y1="6" x2="21" y2="6" /><path d="M16 10a4 4 0 01-8 0" />
            </svg>
            <!-- Graph -->
            <svg v-else-if="item.icon === 'graph'" class="mobile-nav-drawer__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" /><line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
            </svg>
            <!-- Agents -->
            <svg v-else-if="item.icon === 'agents'" class="mobile-nav-drawer__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" />
            </svg>
            <!-- Analytics -->
            <svg v-else-if="item.icon === 'analytics'" class="mobile-nav-drawer__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" />
            </svg>
            <!-- Visualizations -->
            <svg v-else-if="item.icon === 'visualizations'" class="mobile-nav-drawer__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21.21 15.89A10 10 0 118 2.83" /><path d="M22 12A10 10 0 0012 2v10z" />
            </svg>
            <!-- Charts -->
            <svg v-else-if="item.icon === 'charts'" class="mobile-nav-drawer__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            <!-- Comparison -->
            <svg v-else-if="item.icon === 'comparison'" class="mobile-nav-drawer__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="7" width="8" height="14" rx="1" /><rect x="14" y="3" width="8" height="18" rx="1" />
            </svg>
            <!-- API -->
            <svg v-else-if="item.icon === 'api'" class="mobile-nav-drawer__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
            </svg>
            <!-- Settings -->
            <svg v-else-if="item.icon === 'settings'" class="mobile-nav-drawer__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
            </svg>
            <span>{{ item.label }}</span>
          </button>
        </div>
      </div>
    </div>
  </Transition>

  <!-- Bottom Tab Bar -->
  <nav class="mobile-nav md:hidden" aria-label="Mobile navigation">
    <router-link
      v-for="item in primaryTabs"
      :key="item.to"
      :to="item.to"
      class="mobile-nav__tab"
      :class="{ 'mobile-nav__tab--active': isTabActive(item) }"
    >
      <!-- Home -->
      <svg v-if="item.icon === 'home'" class="mobile-nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>

      <!-- Scenarios -->
      <svg v-else-if="item.icon === 'scenarios'" class="mobile-nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z" /><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z" />
      </svg>

      <!-- Simulations -->
      <svg v-else-if="item.icon === 'simulations'" class="mobile-nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>

      <!-- Dashboard -->
      <svg v-else-if="item.icon === 'dashboard'" class="mobile-nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>

      <span class="mobile-nav__label">{{ item.label }}</span>

      <span
        v-if="item.icon === 'simulations' && simulationStore.isActive"
        class="mobile-nav__dot"
      />
    </router-link>

    <!-- More button -->
    <button
      class="mobile-nav__tab"
      :class="{ 'mobile-nav__tab--active': isMoreActive || drawerOpen }"
      @click="drawerOpen = !drawerOpen"
      aria-label="More navigation options"
      :aria-expanded="drawerOpen"
    >
      <svg class="mobile-nav__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="5" r="1.5" fill="currentColor" /><circle cx="12" cy="12" r="1.5" fill="currentColor" /><circle cx="12" cy="19" r="1.5" fill="currentColor" />
      </svg>
      <span class="mobile-nav__label">More</span>
    </button>
  </nav>
</template>

<style scoped>
/* ── Bottom Tab Bar ──────────────────────────────────────────────────── */
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  align-items: stretch;
  background: var(--color-navy);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

.mobile-nav__tab {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 3px;
  min-height: 44px;
  padding: 10px 0 8px;
  color: rgba(255, 255, 255, 0.45);
  text-decoration: none;
  transition: color var(--transition-fast);
  -webkit-tap-highlight-color: transparent;
  background: none;
  border: none;
  cursor: pointer;
}

.mobile-nav__tab--active {
  color: var(--color-primary);
}

.mobile-nav__icon {
  width: 22px;
  height: 22px;
}

.mobile-nav__label {
  font-size: 0.625rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  line-height: 1;
}

.mobile-nav__dot {
  position: absolute;
  top: 6px;
  right: calc(50% - 16px);
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  animation: pulse 2s ease-in-out infinite;
}

/* ── Backdrop ────────────────────────────────────────────────────────── */
.mobile-nav-backdrop {
  position: fixed;
  inset: 0;
  z-index: 45;
  background: rgba(0, 0, 0, 0.5);
  -webkit-backdrop-filter: blur(2px);
  backdrop-filter: blur(2px);
}

/* ── Drawer ──────────────────────────────────────────────────────────── */
.mobile-nav-drawer {
  position: fixed;
  bottom: 56px; /* height of bottom tab bar */
  left: 0;
  right: 0;
  z-index: 48;
  background: var(--color-surface);
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.15);
  padding-bottom: env(safe-area-inset-bottom, 0px);
  max-height: 70vh;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.mobile-nav-drawer__handle {
  display: flex;
  justify-content: center;
  padding: 10px 0 4px;
  cursor: pointer;
}

.mobile-nav-drawer__pill {
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: var(--color-border-strong);
}

.mobile-nav-drawer__content {
  padding: 4px 16px 16px;
}

.mobile-nav-drawer__section {
  margin-bottom: 12px;
}

.mobile-nav-drawer__section:last-child {
  margin-bottom: 0;
}

.mobile-nav-drawer__heading {
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  padding: 8px 12px 4px;
  margin: 0;
}

.mobile-nav-drawer__item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px;
  border-radius: var(--radius-lg);
  border: none;
  background: none;
  color: var(--color-text);
  font-size: 0.9375rem;
  font-weight: 450;
  cursor: pointer;
  transition: background-color var(--transition-fast);
  -webkit-tap-highlight-color: transparent;
  text-align: left;
}

.mobile-nav-drawer__item:active {
  background: var(--color-tint);
}

.mobile-nav-drawer__item--active {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

.mobile-nav-drawer__icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

/* ── Animations ──────────────────────────────────────────────────────── */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
