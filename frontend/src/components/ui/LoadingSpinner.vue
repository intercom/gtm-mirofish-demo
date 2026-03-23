<script setup>
defineProps({
  size: { type: String, default: 'md' },
  label: { type: String, default: 'Loading...' },
})

const sizeClasses = {
  sm: 'w-5 h-5 border-2',
  md: 'w-8 h-8 border-[3px]',
  lg: 'w-12 h-12 border-4',
}
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 py-12" role="status">
    <div
      class="rounded-full border-[#2068FF] border-t-transparent animate-spin"
      :class="sizeClasses[size]"
    ></div>
    <p v-if="label" class="text-sm text-[#888]">{{ label }}</p>
    <span class="sr-only">{{ label }}</span>
  </div>
</template>
