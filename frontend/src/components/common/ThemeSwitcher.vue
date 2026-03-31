<script setup>
import { useTheme } from '../../composables/useTheme'

defineProps({
  compact: Boolean,
})

const { preference, setTheme } = useTheme()

const options = [
  { id: 'system', label: 'System', ariaLabel: 'Use system theme' },
  { id: 'light', label: 'Light', ariaLabel: 'Use light theme' },
  { id: 'dark', label: 'Dark', ariaLabel: 'Use dark theme' },
]
</script>

<template>
  <div class="theme-switcher" :class="{ 'theme-switcher--compact': compact }" role="radiogroup" aria-label="Theme">
    <button
      v-for="opt in options"
      :key="opt.id"
      :aria-label="opt.ariaLabel"
      :aria-checked="preference === opt.id"
      role="radio"
      class="theme-switcher__btn"
      :class="{ 'theme-switcher__btn--active': preference === opt.id }"
      @click="setTheme(opt.id)"
    >
      <!-- System / Monitor icon -->
      <svg v-if="opt.id === 'system'" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <rect x="1.5" y="2.5" width="13" height="9" rx="1.5" stroke="currentColor" stroke-width="1.5" />
        <path d="M5.5 14h5M8 11.5V14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      </svg>
      <!-- Sun icon -->
      <svg v-else-if="opt.id === 'light'" width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <circle cx="8" cy="8" r="3" stroke="currentColor" stroke-width="1.5" />
        <path d="M8 1.5v1M8 13.5v1M1.5 8h1M13.5 8h1M3.4 3.4l.7.7M11.9 11.9l.7.7M12.6 3.4l-.7.7M4.1 11.9l-.7.7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
      </svg>
      <!-- Moon icon -->
      <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M13.5 9.5a5.5 5.5 0 0 1-7-7A5.5 5.5 0 1 0 13.5 9.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
      <span v-if="!compact" class="theme-switcher__label">{{ opt.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.theme-switcher {
  display: inline-flex;
  gap: 0.25rem;
  padding: 0.125rem;
  border-radius: var(--radius-md);
  background: var(--color-border);
}

.theme-switcher__btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
  background: transparent;
  cursor: pointer;
  transition: color var(--transition-fast), background-color var(--transition-fast), border-color var(--transition-fast);
}

.theme-switcher__btn:hover {
  color: var(--color-text);
}

.theme-switcher__btn--active {
  background: var(--color-surface);
  color: var(--color-text);
  border-color: var(--color-border);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* Compact mode for navbar */
.theme-switcher--compact {
  background: rgba(255, 255, 255, 0.08);
}

.theme-switcher--compact .theme-switcher__btn {
  padding: 0.3rem;
  color: rgba(255, 255, 255, 0.5);
}

.theme-switcher--compact .theme-switcher__btn:hover {
  color: rgba(255, 255, 255, 0.85);
}

.theme-switcher--compact .theme-switcher__btn--active {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border-color: transparent;
}
</style>
