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
    class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)]"
    style="box-shadow: var(--card-shadow)"
    :class="[
      padding && 'p-6',
      interactive && 'card-interactive hover:border-[var(--color-primary-border)]',
    ]"
  >
    <slot />
  </div>
</template>
