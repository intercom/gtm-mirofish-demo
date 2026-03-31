<script setup>
import { useId, watch, nextTick, ref } from 'vue'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: String,
})

const emit = defineEmits(['close'])
const titleId = `modal-title-${useId()}`
const dialogRef = ref(null)

function onOverlayClick(e) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    nextTick(() => {
      dialogRef.value?.focus()
    })
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal-overlay">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-[2px]"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="title ? titleId : undefined"
        @click="onOverlayClick"
        @keydown.escape="emit('close')"
      >
        <Transition name="modal-content" appear>
          <div
            v-if="open"
            ref="dialogRef"
            tabindex="-1"
            class="bg-[var(--color-surface)] rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col focus:outline-none"
          >
            <div v-if="title || $slots.header" class="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
              <slot name="header">
                <h2 :id="titleId" class="text-lg font-semibold text-[var(--color-text)]">{{ title }}</h2>
              </slot>
              <button
                @click="emit('close')"
                class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] p-1 -mr-1 cursor-pointer"
                style="transition: var(--transition-fast)"
                aria-label="Close"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path d="M15 5L5 15M5 5l10 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
                </svg>
              </button>
            </div>

            <div class="px-6 py-4 overflow-y-auto">
              <slot />
            </div>

            <div v-if="$slots.footer" class="px-6 py-4 border-t border-[var(--color-border)]">
              <slot name="footer" />
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
