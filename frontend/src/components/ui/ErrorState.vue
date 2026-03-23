<script setup>
defineProps({
  message: { type: String, default: 'Something went wrong.' },
  retryLabel: { type: String, default: 'Try Again' },
})

defineEmits(['retry'])
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-4 py-16 text-center">
    <div class="w-14 h-14 rounded-full bg-[#dc2626]/10 flex items-center justify-center">
      <span class="text-2xl text-[#dc2626]">!</span>
    </div>
    <div>
      <p class="text-sm font-medium text-[#050505]">{{ message }}</p>
    </div>
    <button
      @click="$emit('retry')"
      class="px-5 py-2 text-sm font-medium text-white bg-[#2068FF] hover:bg-[#1a5ae0] rounded-lg transition-colors"
    >
      {{ retryLabel }}
    </button>
  </div>
</template>
