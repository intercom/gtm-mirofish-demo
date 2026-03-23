<script setup>
defineProps({
  status: {
    type: String,
    default: 'idle',
    validator: (v) => ['running', 'complete', 'error', 'idle'].includes(v),
  },
})
</script>

<template>
  <span class="inline-flex items-center gap-2 text-xs">
    <span
      class="w-2 h-2 rounded-full shrink-0"
      :class="{
        'bg-green-500 animate-pulse': status === 'running',
        'bg-[#2068FF]': status === 'complete',
        'bg-red-500': status === 'error',
        'bg-[#888]': status === 'idle',
      }"
    />
    <slot>
      <span class="text-[#555] capitalize">{{ status }}</span>
    </slot>
  </span>
</template>
