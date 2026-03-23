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
    class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)]"
    style="box-shadow: var(--card-shadow)"
    :class="{ 'p-6': padding }"
  >
    <slot />
  </div>
</template>
