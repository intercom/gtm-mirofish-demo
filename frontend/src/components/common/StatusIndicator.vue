<script setup>
defineProps({
  status: {
    type: String,
    default: 'idle',
    validator: (v) => ['running', 'complete', 'error', 'idle'].includes(v),
  },
})
</script>

<template>
  <span class="inline-flex items-center gap-2 text-xs" role="status">
    <span
      class="w-2 h-2 rounded-full shrink-0"
      aria-hidden="true"
      :class="{
        'bg-[var(--color-success)] animate-pulse': status === 'running',
        'bg-[var(--color-primary)]': status === 'complete',
        'bg-[var(--color-error)]': status === 'error',
        'bg-[var(--color-text-muted)]': status === 'idle',
      }"
    />
    <slot>
      <span class="text-[var(--color-text-secondary)] capitalize">{{ status }}</span>
    </slot>
  </span>
</template>
