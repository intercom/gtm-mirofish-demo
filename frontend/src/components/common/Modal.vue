<script setup>
defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: String,
})

const emit = defineEmits(['close'])

function onOverlayClick(e) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
        @click="onOverlayClick"
      >
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
          <div v-if="title || $slots.header" class="flex items-center justify-between px-6 py-4 border-b border-black/10">
            <slot name="header">
              <h2 class="text-lg font-semibold text-[#050505]">{{ title }}</h2>
            </slot>
            <button
              @click="emit('close')"
              class="text-[#888] hover:text-[#050505] transition-colors p-1 -mr-1 cursor-pointer"
              aria-label="Close"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5l10 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
              </svg>
            </button>
          </div>

          <div class="px-6 py-4 overflow-y-auto">
            <slot />
          </div>

          <div v-if="$slots.footer" class="px-6 py-4 border-t border-black/10">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 150ms ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
