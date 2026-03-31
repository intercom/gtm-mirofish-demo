<script setup>
import { ref } from 'vue'

defineProps({
  simAName: { type: String, default: 'Simulation A' },
  simBName: { type: String, default: 'Simulation B' },
})

defineEmits(['swap'])

const showSidebar = ref(false)
</script>

<template>
  <div class="flex gap-6">
    <!-- Main content -->
    <div class="flex-1 min-w-0 space-y-6">
      <!-- Header with sim labels -->
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[rgba(32,104,255,0.08)] border border-[#2068FF]/20">
          <span class="w-2.5 h-2.5 rounded-full bg-[#2068FF]" />
          <span class="text-sm font-medium text-[#2068FF]">{{ simAName }}</span>
        </div>
        <button
          @click="$emit('swap')"
          class="p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[#2068FF] hover:bg-[rgba(32,104,255,0.08)] transition-colors"
          title="Swap simulations"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
          </svg>
        </button>
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[rgba(255,86,0,0.08)] border border-[#ff5600]/20">
          <span class="w-2.5 h-2.5 rounded-full bg-[#ff5600]" />
          <span class="text-sm font-medium text-[#ff5600]">{{ simBName }}</span>
        </div>
        <div class="flex-1" />
        <button
          @click="showSidebar = !showSidebar"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF] transition-colors"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
          </svg>
          A/B Test
        </button>
      </div>

      <slot />
    </div>

    <!-- Sidebar (A/B scenario builder) -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 translate-x-4"
      enter-to-class="opacity-100 translate-x-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-x-0"
      leave-to-class="opacity-0 translate-x-4"
    >
      <div v-if="showSidebar" class="w-full sm:w-80 shrink-0">
        <slot name="sidebar" />
      </div>
    </Transition>
  </div>
</template>
