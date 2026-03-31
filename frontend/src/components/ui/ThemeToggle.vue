<script setup>
import { useTheme } from '../../composables/useTheme'

const { preference, isDark, setTheme } = useTheme()

const modes = ['light', 'dark', 'system']

function cycle() {
  const idx = modes.indexOf(preference.value)
  setTheme(modes[(idx + 1) % modes.length])
}
</script>

<template>
  <button
    @click="cycle"
    class="theme-toggle"
    :title="`Theme: ${preference} — click to cycle`"
    :aria-label="`Current theme: ${preference}. Click to switch.`"
  >
    <!-- Sun (light mode) -->
    <svg v-if="preference === 'light'" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
      <circle cx="8" cy="8" r="3" />
      <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.41 1.41M11.54 11.54l1.41 1.41M3.05 12.95l1.41-1.41M11.54 4.46l1.41-1.41" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none" />
    </svg>
    <!-- Moon (dark mode) -->
    <svg v-else-if="preference === 'dark'" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
      <path d="M13.36 10.06A6 6 0 015.94 2.64 7 7 0 1013.36 10.06z" />
    </svg>
    <!-- Monitor (system mode) -->
    <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="1.5" y="2" width="13" height="9" rx="1.5" />
      <path d="M5.5 14h5M8 11v3" />
    </svg>
  </button>
</template>

<style scoped>
.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  color: rgba(255, 255, 255, 0.5);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color var(--transition-fast), background-color var(--transition-fast);
}
.theme-toggle:hover {
  color: white;
  background-color: rgba(255, 255, 255, 0.08);
}
</style>
