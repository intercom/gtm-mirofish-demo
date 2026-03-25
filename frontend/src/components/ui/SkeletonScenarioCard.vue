<script setup>
import SkeletonBlock from './SkeletonBlock.vue'

defineProps({
  dark: { type: Boolean, default: false },
})
</script>

<template>
  <div
    class="rounded-lg p-5 border"
    :class="dark
      ? 'border-white/10 bg-white/5'
      : 'border-[var(--color-border)] bg-[var(--color-surface)]'"
    :style="dark ? { '--skeleton-base': 'rgba(255,255,255,0.05)', '--skeleton-highlight': 'rgba(255,255,255,0.12)' } : {}"
  >
    <div class="flex items-start gap-3">
      <SkeletonBlock width="32px" height="32px" rounded="lg" />
      <div class="flex-1 space-y-2">
        <SkeletonBlock height="16px" width="70%" />
        <SkeletonBlock height="12px" width="100%" />
        <SkeletonBlock height="12px" width="50%" />
      </div>
    </div>
  </div>
</template>
