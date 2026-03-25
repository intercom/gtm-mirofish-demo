<script setup>
import { useId } from 'vue'

defineProps({
  modelValue: { type: Boolean, required: true },
  title: { type: String, required: true },
  message: { type: String, required: true },
  confirmLabel: { type: String, default: 'Confirm' },
  cancelLabel: { type: String, default: 'Cancel' },
  destructive: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])
const titleId = `confirm-title-${useId()}`
const descId = `confirm-desc-${useId()}`

function close() {
  emit('update:modelValue', false)
  emit('cancel')
}

function confirm() {
  emit('update:modelValue', false)
  emit('confirm')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="confirm-overlay">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        role="alertdialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        :aria-describedby="descId"
        @click.self="close"
        @keydown.escape="close"
      >
        <Transition name="confirm-modal" appear>
          <div
            v-if="modelValue"
            class="bg-[var(--color-surface)] rounded-xl shadow-xl w-full max-w-md mx-4"
          >
            <div class="px-6 pt-6 pb-2">
              <h3 :id="titleId" class="text-lg font-semibold text-[var(--color-text)]">{{ title }}</h3>
            </div>
            <div class="px-6 pb-6">
              <p :id="descId" class="text-sm text-[var(--color-text-secondary)]">{{ message }}</p>
            </div>
            <div class="flex items-center justify-end gap-3 px-6 pb-6">
              <button
                class="px-4 py-2 text-sm font-medium rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)] transition-colors cursor-pointer"
                @click="close"
              >
                {{ cancelLabel }}
              </button>
              <button
                class="px-4 py-2 text-sm font-medium rounded-lg text-white transition-colors cursor-pointer"
                :class="destructive ? 'bg-red-600 hover:bg-red-700' : 'bg-[#2068FF] hover:bg-[#1a5ae0]'"
                @click="confirm"
              >
                {{ confirmLabel }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.confirm-overlay-enter-active,
.confirm-overlay-leave-active {
  transition: opacity 0.2s ease;
}
.confirm-overlay-enter-from,
.confirm-overlay-leave-to {
  opacity: 0;
}

.confirm-modal-enter-active {
  transition: all 0.2s ease-out;
}
.confirm-modal-leave-active {
  transition: all 0.15s ease-in;
}
.confirm-modal-enter-from {
  opacity: 0;
  transform: scale(0.95);
}
.confirm-modal-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
