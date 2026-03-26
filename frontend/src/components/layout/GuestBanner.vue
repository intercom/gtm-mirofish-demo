<script setup>
import { ref } from 'vue'

const dismissed = ref(false)
</script>

<template>
  <div
    v-if="!dismissed"
    class="bg-[var(--color-fin-orange-tint)] border-b border-[var(--color-fin-orange)]/20 px-4 py-2 flex items-center justify-center gap-2 text-sm"
  >
    <svg class="w-4 h-4 text-[var(--color-fin-orange)] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
    <span class="text-[var(--color-text-secondary)]">
      <span class="font-semibold text-[var(--color-fin-orange)]">Guest access</span> — some features are limited
    </span>
    <button
      @click="dismissed = true"
      class="ml-2 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
      aria-label="Dismiss banner"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
</template>
