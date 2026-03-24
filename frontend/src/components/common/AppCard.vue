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
    :class="[
      'bg-[--color-surface] border border-[--color-border] rounded-lg',
      padding && 'p-6',
    ]"
  >
    <div v-if="$slots.header" class="mb-4">
      <slot name="header" />
    </div>
    <slot />
  </div>
</template>
