<script setup>
import { useToast } from '../../composables/useToast'

const { toasts, removeToast } = useToast()

const iconMap = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
}

const colorMap = {
  success: 'bg-[#090] text-white',
  error: 'bg-red-600 text-white',
  info: 'bg-[#2068FF] text-white',
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none">
      <TransitionGroup
        enter-active-class="transition-all duration-300 ease-out"
        leave-active-class="transition-all duration-200 ease-in"
        enter-from-class="translate-x-full opacity-0"
        enter-to-class="translate-x-0 opacity-100"
        leave-from-class="translate-x-0 opacity-100"
        leave-to-class="translate-x-full opacity-0"
      >
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="pointer-events-auto flex items-center gap-2.5 px-4 py-3 rounded-lg shadow-lg text-sm font-medium min-w-[280px] max-w-[420px]"
          :class="colorMap[toast.type]"
        >
          <span class="text-base font-bold shrink-0">{{ iconMap[toast.type] }}</span>
          <span class="flex-1">{{ toast.message }}</span>
          <button
            @click="removeToast(toast.id)"
            class="shrink-0 opacity-70 hover:opacity-100 text-base leading-none cursor-pointer"
          >
            &times;
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
