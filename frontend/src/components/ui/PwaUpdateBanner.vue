<script setup>
import { useServiceWorker } from '../../composables/useServiceWorker'

const { needRefresh, offlineReady, update, dismiss } = useServiceWorker()
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      enter-from-class="translate-y-full opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-full opacity-0"
    >
      <div
        v-if="needRefresh || offlineReady"
        class="fixed bottom-4 left-1/2 -translate-x-1/2 z-[9999] flex items-center gap-3 px-5 py-3 rounded-lg shadow-lg text-sm font-medium bg-[#050505] text-white max-w-[480px]"
      >
        <span class="flex-1">
          <template v-if="needRefresh">A new version is available.</template>
          <template v-else>App ready for offline use.</template>
        </span>
        <button
          v-if="needRefresh"
          @click="update"
          class="shrink-0 px-3 py-1 rounded-md bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-xs font-semibold cursor-pointer transition-colors"
        >
          Update
        </button>
        <button
          @click="dismiss"
          class="shrink-0 opacity-60 hover:opacity-100 text-base leading-none cursor-pointer"
        >
          &times;
        </button>
      </div>
    </Transition>
  </Teleport>
</template>
