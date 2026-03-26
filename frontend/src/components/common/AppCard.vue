<script setup>
defineProps({
  padding: {
    type: Boolean,
    default: true,
  },
  interactive: {
    type: Boolean,
    default: false,
  },
})
</script>

<template>
  <div
    :class="[
      'bg-[--color-surface] border border-[--color-border] rounded-lg hover-lift',
      padding && 'p-6',
      interactive && 'card-interactive hover:border-[var(--color-primary-border)]',
    ]"
  >
    <div v-if="$slots.header" class="mb-4">
      <slot name="header" />
    </div>
    <slot />
  </div>
</template>
