<script setup>
defineProps({
  icon: { type: String, default: '📭' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  actionLabel: { type: String, default: '' },
  actionTo: { type: String, default: '' },
})

defineEmits(['action'])
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 px-4 text-center">
    <div class="w-16 h-16 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mb-4">
      <span class="text-3xl">{{ icon }}</span>
    </div>
    <h3 class="text-base font-semibold text-[#050505] mb-1">{{ title }}</h3>
    <p v-if="description" class="text-sm text-[#888] mb-6 max-w-sm">{{ description }}</p>
    <router-link
      v-if="actionLabel && actionTo"
      :to="actionTo"
      class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors no-underline"
    >
      {{ actionLabel }}
    </router-link>
    <button
      v-else-if="actionLabel"
      @click="$emit('action')"
      class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>
