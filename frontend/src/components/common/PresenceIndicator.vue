<script setup>
import { ref, computed } from 'vue'
import { usePresenceStore } from '../../stores/presence'
import { usePresence } from '../../composables/usePresence'

const store = usePresenceStore()
usePresence({ pollInterval: 4000, cursorInterval: 2000 })

const hoveredViewer = ref(null)

const STATUS_ICONS = {
  active: '●',
  viewing: '◉',
  editing: '✎',
  idle: '○',
}

const viewers = computed(() => store.users)
</script>

<template>
  <div class="hidden sm:flex items-center">
    <div
      v-for="(viewer, i) in viewers"
      :key="viewer.id"
      class="relative"
      :class="{ '-ml-1.5': i > 0 }"
      @mouseenter="hoveredViewer = viewer.id"
      @mouseleave="hoveredViewer = null"
    >
      <div
        class="presence-avatar"
        :style="{ backgroundColor: viewer.color, zIndex: viewers.length - i }"
        :class="{ 'ring-2 ring-emerald-400': viewer.status === 'editing' }"
      >
        {{ viewer.initials }}
        <span
          v-if="viewer.is_typing"
          class="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-500 rounded-full border border-[#050505] animate-pulse"
        />
      </div>

      <Transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="opacity-0 translate-y-1"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-1"
      >
        <div
          v-if="hoveredViewer === viewer.id"
          class="absolute top-full mt-2 left-1/2 -translate-x-1/2 px-3 py-2 bg-[#050505] text-white text-xs rounded-lg shadow-lg whitespace-nowrap z-50 pointer-events-none border border-white/10"
        >
          <div class="flex items-center gap-1.5 mb-1">
            <span class="font-medium">{{ viewer.name }}</span>
            <span class="text-white/30">{{ STATUS_ICONS[viewer.status] || '●' }}</span>
          </div>
          <div class="text-white/40 text-[10px]">{{ viewer.role }}</div>
          <div class="flex items-center gap-1 mt-1">
            <span class="text-white/50">{{ viewer.activity }}</span>
            <span class="text-[#2068FF]">{{ viewer.current_page }}</span>
          </div>
          <div class="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-[#050505] border-l border-t border-white/10 rotate-45" />
        </div>
      </Transition>
    </div>

    <span
      v-if="store.totalOnline > 0"
      class="w-2 h-2 rounded-full bg-emerald-500 ml-1.5 animate-pulse"
    />
    <span
      v-if="store.totalOnline > 0"
      class="text-[10px] text-white/40 ml-1 tabular-nums"
    >
      {{ store.totalOnline }}
    </span>
  </div>
</template>

<style scoped>
.presence-avatar {
  position: relative;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.625rem;
  font-weight: 600;
  color: white;
  border: 2px solid var(--color-navy);
  cursor: default;
  transition: transform 150ms ease;
}
.presence-avatar:hover {
  transform: scale(1.15);
  z-index: 10 !important;
}
</style>
