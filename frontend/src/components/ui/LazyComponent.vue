<script setup>
import { ref } from 'vue'
import { useLazyLoad } from '../../composables/useLazyLoad'

const props = defineProps({
  rootMargin: { type: String, default: '200px' },
  threshold: { type: Number, default: 0 },
  minHeight: { type: String, default: '100px' },
})

const sentinelRef = ref(null)
const { isVisible } = useLazyLoad(sentinelRef, {
  rootMargin: props.rootMargin,
  threshold: props.threshold,
})
</script>

<template>
  <div ref="sentinelRef" :style="{ minHeight: isVisible ? undefined : minHeight }">
    <slot v-if="isVisible" />
    <slot v-else name="placeholder">
      <div class="flex items-center justify-center" :style="{ minHeight }">
        <div class="w-6 h-6 rounded-full border-2 border-black/10 border-t-[#2068FF] animate-spin" />
      </div>
    </slot>
  </div>
</template>
