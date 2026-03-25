<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTimelineScrubberInject } from '../../composables/useTimelineScrubber'

const props = defineProps({
  padLeft: { type: Number, default: 40 },
  padRight: { type: Number, default: 16 },
})

const emit = defineEmits(['seek'])

const scrubber = useTimelineScrubberInject()
const containerRef = ref(null)
const containerWidth = ref(0)
let resizeObserver = null

const crosshairLeft = computed(() => {
  if (!scrubber || !scrubber.hasData.value || containerWidth.value === 0) return null
  if (scrubber.totalRounds.value === 0) return null
  const chartWidth = containerWidth.value - props.padLeft - props.padRight
  if (chartWidth <= 0) return null
  const x = props.padLeft + scrubber.position.value * chartWidth
  return `${x}px`
})

function handleClick(e) {
  if (!scrubber || !containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const chartWidth = rect.width - props.padLeft - props.padRight
  if (chartWidth <= 0) return
  const pos = Math.max(0, Math.min(1, (x - props.padLeft) / chartWidth))
  scrubber.seekToPosition(pos)
  emit('seek', Math.round(pos * scrubber.totalRounds.value))
}

onMounted(() => {
  if (containerRef.value) {
    containerWidth.value = containerRef.value.clientWidth
    resizeObserver = new ResizeObserver(entries => {
      containerWidth.value = entries[0].contentRect.width
    })
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})
</script>

<template>
  <div ref="containerRef" class="relative cursor-crosshair" @click="handleClick">
    <slot />
    <div
      v-if="crosshairLeft"
      class="absolute top-0 bottom-0 w-px bg-[var(--color-primary)] opacity-40 pointer-events-none transition-[left] duration-75"
      :style="{ left: crosshairLeft }"
    />
  </div>
</template>
