<script setup>
defineProps({
  config: { type: Object, default: () => ({}) },
  data: { type: [Object, Array, null], default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null },
  onConfigChange: { type: Function, default: null },
})
</script>

<template>
  <div class="flex items-center justify-center h-full min-h-[120px] p-4">
    <div v-if="loading" class="text-sm text-[--color-text-secondary]">Loading table...</div>
    <div v-else-if="error" class="text-sm text-red-500">{{ error }}</div>
    <div v-else class="text-sm text-[--color-text-secondary]">Table — {{ config.title || 'No data' }}</div>
  </div>
</template>
