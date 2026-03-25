<script setup>
defineProps({
  width: { type: String, default: '100%' },
  height: { type: String, default: '12px' },
  rounded: { type: String, default: 'md' },
})
</script>

<template>
  <div
    class="skeleton-shimmer"
    :class="`rounded-${rounded}`"
    :style="{ width, height }"
  />
</template>

<style scoped>
.skeleton-shimmer {
  background: linear-gradient(
    90deg,
    var(--skeleton-base, var(--color-tint)) 25%,
    var(--skeleton-highlight, var(--color-border)) 50%,
    var(--skeleton-base, var(--color-tint)) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
