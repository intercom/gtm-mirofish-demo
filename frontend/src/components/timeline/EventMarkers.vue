<script setup>
import { computed } from 'vue'

const props = defineProps({
  events: { type: Array, default: () => [] },
  totalRounds: { type: Number, default: 0 },
})

const visibleEvents = computed(() => {
  if (!props.totalRounds) return []
  return props.events.filter(e => e.round > 0 && e.round <= props.totalRounds)
})

function markerClass(type) {
  switch (type) {
    case 'spike': return 'bg-[var(--color-fin-orange)]'
    case 'milestone': return 'bg-emerald-500'
    default: return 'bg-[var(--color-primary)]'
  }
}
</script>

<template>
  <div v-if="visibleEvents.length" class="relative h-2.5 mb-0.5">
    <div
      v-for="(event, idx) in visibleEvents"
      :key="`${event.round}-${event.type}-${idx}`"
      class="absolute top-0.5 -translate-x-1/2 group"
      :style="{ left: `${(event.round / totalRounds) * 100}%` }"
    >
      <div class="w-1.5 h-1.5 rounded-full" :class="markerClass(event.type)" />
      <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 text-[10px] text-white bg-[#050505] rounded whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-10">
        {{ event.label }}
      </div>
    </div>
  </div>
</template>
