<script setup>
defineProps({
  open: Boolean,
  title: String,
})

const emit = defineEmits(['done', 'cancel'])

function onBackdropClick(e) {
  if (e.target === e.currentTarget) {
    emit('cancel')
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="editor-popover">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] bg-black/40"
        @click="onBackdropClick"
      >
        <div class="bg-[var(--color-surface)] rounded-xl shadow-2xl w-full max-w-xl mx-4 max-h-[75vh] flex flex-col border border-[var(--color-border)]">
          <!-- Header -->
          <div class="flex items-center justify-between px-5 py-3.5 border-b border-[var(--color-border)] shrink-0">
            <h3 class="text-sm font-semibold text-[var(--color-text)]">{{ title }}</h3>
            <button
              class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors cursor-pointer"
              @click="emit('cancel')"
              aria-label="Close"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Content (scrollable) -->
          <div class="p-5 overflow-y-auto flex-1">
            <slot />
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-end gap-2 px-5 py-3.5 border-t border-[var(--color-border)] shrink-0">
            <button
              class="px-4 py-1.5 text-sm font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-black/5 rounded-lg transition-colors cursor-pointer"
              @click="emit('cancel')"
            >
              Cancel
            </button>
            <button
              class="px-4 py-1.5 text-sm font-medium bg-[#2068FF] hover:bg-[#1a5ae0] text-white rounded-lg transition-colors cursor-pointer"
              @click="emit('done')"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.editor-popover-enter-active,
.editor-popover-leave-active {
  transition: opacity 0.15s ease;
}
.editor-popover-enter-active > div,
.editor-popover-leave-active > div {
  transition: transform 0.15s ease;
}
.editor-popover-enter-from,
.editor-popover-leave-to {
  opacity: 0;
}
.editor-popover-enter-from > div {
  transform: translateY(-8px) scale(0.98);
}
.editor-popover-leave-to > div {
  transform: translateY(4px) scale(0.98);
}
</style>
