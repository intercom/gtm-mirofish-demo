<script setup>
defineProps({
  status: {
    type: String,
    required: true,
    validator: (v) => ['running', 'complete', 'error'].includes(v),
  },
  label: String,
})

const statusConfig = {
  running: { color: 'bg-green-500', animate: true, defaultLabel: 'Running' },
  complete: { color: 'bg-[--color-primary]', animate: false, defaultLabel: 'Complete' },
  error: { color: 'bg-red-500', animate: false, defaultLabel: 'Error' },
}
</script>

<template>
  <span class="inline-flex items-center gap-1.5 text-xs text-[--color-text-secondary]">
    <span class="relative flex h-2 w-2">
      <span
        v-if="statusConfig[status].animate"
        :class="[statusConfig[status].color, 'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75']"
      />
      <span :class="[statusConfig[status].color, 'relative inline-flex rounded-full h-2 w-2']" />
    </span>
    {{ label ?? statusConfig[status].defaultLabel }}
  </span>
</template>
