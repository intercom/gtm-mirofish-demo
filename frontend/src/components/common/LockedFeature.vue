<script setup>
import { computed } from 'vue'

const props = defineProps({
  requiredRole: {
    type: String,
    default: 'editor',
    validator: (v) => ['editor', 'admin'].includes(v),
  },
  locked: {
    type: Boolean,
    default: false,
  },
})

const tooltipText = computed(() => `Requires ${props.requiredRole.charAt(0).toUpperCase() + props.requiredRole.slice(1)} role`)
</script>

<template>
  <span class="inline-flex items-center gap-1.5 relative group">
    <slot />
    <span
      v-if="locked"
      class="inline-flex items-center text-[var(--color-text-muted)]"
      :title="tooltipText"
    >
      <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
      <span
        class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 text-[10px] font-medium text-white bg-[var(--color-navy)] rounded whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity"
      >{{ tooltipText }}</span>
    </span>
  </span>
</template>
