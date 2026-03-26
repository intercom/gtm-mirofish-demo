<script setup>
import { useId } from 'vue'

defineProps({
  open: Boolean,
  title: String,
})

const emit = defineEmits(['close'])
const titleId = `app-modal-title-${useId()}`

function onBackdropClick(e) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-overlay">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-[2px]"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="title ? titleId : undefined"
        @click="onBackdropClick"
        @keydown.escape="emit('close')"
      >
        <Transition name="modal-content" appear>
          <div
            v-if="open"
            class="bg-[--color-surface] rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[85vh] overflow-y-auto"
          >
            <div v-if="title || $slots.header" class="flex items-center justify-between px-6 py-4 border-b border-[--color-border]">
              <slot name="header">
                <h2 :id="titleId" class="text-lg font-semibold text-[--color-text]">{{ title }}</h2>
              </slot>
              <button
                class="text-[--color-text-muted] hover:text-[--color-text] transition-colors cursor-pointer"
                @click="emit('close')"
                aria-label="Close"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div class="p-6">
              <slot />
            </div>
            <div v-if="$slots.footer" class="px-6 py-4 border-t border-[--color-border]">
              <slot name="footer" />
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
