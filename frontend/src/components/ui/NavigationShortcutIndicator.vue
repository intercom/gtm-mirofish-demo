<script setup>
import { useNavigationShortcuts } from '../../composables/useNavigationShortcuts'

const { isGMode, shortcuts } = useNavigationShortcuts()
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-150 ease-out"
      enter-from-class="opacity-0 translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-100 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-2"
    >
      <div
        v-if="isGMode"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[9999] bg-[#050505] border border-white/15 rounded-xl shadow-2xl px-5 py-3"
      >
        <div class="text-xs text-white/50 mb-2 font-medium">Go to&hellip;</div>
        <div class="flex items-center gap-3">
          <div
            v-for="(shortcut, key) in shortcuts"
            :key="key"
            class="flex items-center gap-1.5 text-sm"
          >
            <kbd class="inline-flex items-center justify-center w-6 h-6 rounded bg-white/10 text-white font-mono text-xs font-semibold border border-white/20">
              {{ key.toUpperCase() }}
            </kbd>
            <span class="text-white/70">{{ shortcut.label }}</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
