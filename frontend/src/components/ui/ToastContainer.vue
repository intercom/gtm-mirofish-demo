<script setup>
import { useToastStore } from '../../stores/toast.js'

const toast = useToastStore()

const iconMap = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
}

const colorMap = {
  success: 'bg-[#090] text-white',
  error: 'bg-[#dc2626] text-white',
  info: 'bg-[#2068FF] text-white',
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none">
      <TransitionGroup
        enter-from-class="translate-x-full opacity-0"
        enter-active-class="transition-all duration-300 ease-out"
        leave-active-class="transition-all duration-200 ease-in"
        leave-to-class="translate-x-full opacity-0"
      >
        <div
          v-for="t in toast.toasts"
          :key="t.id"
          class="pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-lg shadow-lg text-sm font-medium min-w-[280px] max-w-[420px]"
          :class="colorMap[t.type]"
        >
          <span class="text-base font-bold shrink-0">{{ iconMap[t.type] }}</span>
          <span class="flex-1">{{ t.message }}</span>
          <button
            @click="toast.remove(t.id)"
            class="shrink-0 opacity-70 hover:opacity-100 text-base leading-none cursor-pointer"
          >
            ×
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
