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
  <div class="flex flex-col items-center justify-center h-full min-h-[120px] p-4">
    <div v-if="loading" class="text-sm text-[--color-text-secondary]">Loading...</div>
    <div v-else-if="error" class="text-sm text-red-500">{{ error }}</div>
    <template v-else>
      <div class="text-3xl font-bold text-[--color-text]">
        {{ config.prefix }}{{ data?.value ?? '—' }}{{ config.suffix }}
      </div>
      <div class="text-sm text-[--color-text-secondary] mt-1">{{ config.label || 'KPI' }}</div>
    </template>
  </div>
</template>
