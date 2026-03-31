<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useDemoMode } from '../../composables/useDemoMode'

const { isDemoMode } = useDemoMode()
const showTooltip = ref(false)
const wrapper = ref(null)

function toggleTooltip() {
  showTooltip.value = !showTooltip.value
}

function onDocumentClick(e) {
  if (wrapper.value && !wrapper.value.contains(e.target)) {
    showTooltip.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))
</script>

<template>
  <span v-if="isDemoMode" ref="wrapper" class="demo-badge-wrapper" @click.stop="toggleTooltip">
    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[var(--badge-warning-bg-soft)] text-[var(--badge-warning-text-soft)] border border-[var(--color-warning-border)] cursor-pointer hover:opacity-80 transition-colors select-none">
      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      Demo Data
    </span>
    <Transition name="tooltip">
      <span
        v-if="showTooltip"
        class="absolute z-40 bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 rounded-lg bg-gray-900 text-white text-xs leading-relaxed whitespace-nowrap shadow-lg"
      >
        This data is simulated. Configure API keys for real data.
        <span class="absolute top-full left-1/2 -translate-x-1/2 -mt-px border-4 border-transparent border-t-gray-900" />
      </span>
    </Transition>
  </span>
</template>

<style scoped>
.demo-badge-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 150ms ease, transform 150ms ease;
}
.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translate(-50%, 4px);
}
</style>
