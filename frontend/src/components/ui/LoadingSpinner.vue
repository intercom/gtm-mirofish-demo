<script setup>
defineProps({
  label: { type: String, default: 'Loading...' },
  size: { type: String, default: 'md' },
})

const sizeClasses = {
  sm: 'w-5 h-5 border-2',
  md: 'w-8 h-8 border-[3px]',
  lg: 'w-12 h-12 border-4',
}
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 py-16">
    <div
      class="rounded-full border-[#2068FF] border-t-transparent animate-spin"
      :class="sizeClasses[size]"
    ></div>
    <p v-if="label" class="text-sm text-[#888]">{{ label }}</p>
  </div>
</template>
