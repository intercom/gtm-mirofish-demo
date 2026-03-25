<script setup>
import { useRoute } from 'vue-router'
import { useSimulationStore } from '../../stores/simulation'

const route = useRoute()
const simulationStore = useSimulationStore()

const navItems = [
  { to: '/', label: 'Home', icon: 'home', exact: true },
  { to: '/simulations', label: 'Simulations', icon: 'simulations', exact: false },
  { to: '/settings', label: 'Settings', icon: 'settings', exact: false },
]

function isActive(item) {
  if (item.exact) return route.path === item.to
  return route.path.startsWith(item.to)
}
</script>

<template>
  <nav class="mobile-nav md:hidden" aria-label="Mobile navigation">
    <router-link
      v-for="item in navItems"
      :key="item.to"
      :to="item.to"
      class="mobile-nav__item"
      :class="{ 'mobile-nav__item--active': isActive(item) }"
    >
      <!-- Home icon -->
      <svg v-if="item.icon === 'home'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>

      <!-- Simulations icon -->
      <svg v-else-if="item.icon === 'simulations'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>

      <!-- Settings icon -->
      <svg v-else-if="item.icon === 'settings'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
      </svg>

      <span class="mobile-nav__label">{{ item.label }}</span>

      <span
        v-if="item.icon === 'simulations' && simulationStore.isActive"
        class="mobile-nav__dot"
      ></span>
    </router-link>
  </nav>
</template>

<style scoped>
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  align-items: stretch;
  justify-content: space-around;
  background: var(--color-navy);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

.mobile-nav__item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 2px;
  padding: 8px 0 6px;
  color: rgba(255, 255, 255, 0.45);
  text-decoration: none;
  transition: color var(--transition-fast);
  -webkit-tap-highlight-color: transparent;
}

.mobile-nav__item--active {
  color: var(--color-primary);
}

.mobile-nav__label {
  font-size: 0.625rem;
  font-weight: var(--font-medium);
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

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
