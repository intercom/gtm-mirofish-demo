<script setup>
import { computed } from 'vue'
import { formatShortcut } from '../../composables/useKeyboardShortcuts'

const props = defineProps({
  /** Shortcut string using "mod+key" notation, e.g. "mod+k", "shift+?" */
  shortcut: {
    type: String,
    required: true,
  },
  /** Visual variant: 'light' for dark backgrounds, 'dark' for light backgrounds */
  variant: {
    type: String,
    default: 'dark',
    validator: (v) => ['dark', 'light'].includes(v),
  },
})

const keys = computed(() => formatShortcut(props.shortcut))
</script>

<template>
  <span class="shortcut-badge" :class="`shortcut-badge--${variant}`" aria-hidden="true">
    <kbd v-for="(key, i) in keys" :key="i" class="shortcut-badge__key">{{ key }}</kbd>
  </span>
</template>

<style scoped>
.shortcut-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  pointer-events: none;
}

/* Hide on touch devices */
@media (hover: none) {
  .shortcut-badge {
    display: none;
  }
}

.shortcut-badge__key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.25rem;
  font-family: var(--font-mono);
  font-size: 0.625rem;
  font-weight: 500;
  line-height: 1;
  border-radius: var(--radius-sm);
}

/* Dark variant: for use on light backgrounds */
.shortcut-badge--dark .shortcut-badge__key {
  background: rgba(0, 0, 0, 0.06);
  color: var(--color-text-muted);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

/* Light variant: for use on dark backgrounds (e.g. nav bar) */
.shortcut-badge--light .shortcut-badge__key {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
