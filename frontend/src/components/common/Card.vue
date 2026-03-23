<script setup>
defineProps({
  padding: {
    type: Boolean,
    default: true,
  },
})
</script>

<template>
  <div
    class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg"
    :class="{ 'p-6': padding }"
  >
    <slot />
  </div>
</template>
