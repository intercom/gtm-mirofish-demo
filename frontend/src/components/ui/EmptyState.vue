<script setup>
defineProps({
  icon: { type: String, default: '📭' },
  title: { type: String, default: 'Nothing here yet' },
  description: { type: String, default: '' },
  actionLabel: { type: String, default: '' },
  actionTo: { type: String, default: '' },
})

defineEmits(['action'])
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 py-16 text-center">
    <span class="text-5xl">{{ icon }}</span>
    <h3 class="text-base font-semibold text-[#050505]">{{ title }}</h3>
    <p v-if="description" class="text-sm text-[#888] max-w-sm">{{ description }}</p>
    <router-link
      v-if="actionTo"
      :to="actionTo"
      class="mt-2 px-5 py-2 text-sm font-medium text-white bg-[#2068FF] hover:bg-[#1a5ae0] rounded-lg transition-colors no-underline"
    >
      {{ actionLabel }}
    </router-link>
    <button
      v-else-if="actionLabel"
      @click="$emit('action')"
      class="mt-2 px-5 py-2 text-sm font-medium text-white bg-[#2068FF] hover:bg-[#1a5ae0] rounded-lg transition-colors"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>
