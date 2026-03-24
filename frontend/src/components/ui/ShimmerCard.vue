<script setup>
const props = defineProps({
  lines: { type: Number, default: 3 },
  height: { type: String, default: 'auto' },
  rounded: { type: String, default: 'lg' },
})

const lineWidths = ['75%', '100%', '60%', '85%', '45%', '90%', '70%', '55%']

function getLineWidth(index) {
  return lineWidths[index % lineWidths.length]
}
</script>

<template>
  <div
    class="bg-[var(--color-surface)] border border-[var(--color-border)] p-4 overflow-hidden"
    :class="`rounded-${rounded}`"
    :style="{ height }"
  >
    <div
      v-for="i in lines"
      :key="i"
      class="shimmer-line rounded"
      :class="i > 1 ? 'mt-3' : ''"
      :style="{ width: getLineWidth(i - 1) }"
    />
  </div>
</template>

<style scoped>
.shimmer-line {
  height: 12px;
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.04) 25%,
    rgba(0, 0, 0, 0.08) 50%,
    rgba(0, 0, 0, 0.04) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
