<script setup>
import Modal from '../common/Modal.vue'

defineProps({
  open: Boolean,
  shortcuts: Array,
  modLabel: { type: String, default: '⌘' },
})

defineEmits(['close'])
</script>

<template>
  <Modal :open="open" title="Keyboard Shortcuts" @close="$emit('close')">
    <div class="space-y-1">
      <div
        v-for="s in shortcuts"
        :key="s.label"
        class="flex items-center justify-between py-2"
      >
        <span class="text-sm text-[var(--color-text-secondary)]">{{ s.label }}</span>
        <div class="flex items-center gap-1">
          <kbd v-if="s.mod" class="kbd">{{ modLabel }}</kbd>
          <span v-if="s.mod" class="text-xs text-[var(--color-text-muted)]">+</span>
          <kbd class="kbd">{{ s.display || s.key }}</kbd>
        </div>
      </div>
    </div>
    <div class="border-t border-[var(--color-border)] mt-4 pt-3">
      <div class="flex items-center justify-between py-2">
        <span class="text-sm text-[var(--color-text-muted)]">Toggle this help</span>
        <kbd class="kbd">?</kbd>
      </div>
    </div>
  </Modal>
</template>

<style scoped>
.kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  background: var(--color-tint);
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  color: var(--color-text-secondary);
  box-shadow: 0 1px 0 var(--color-border);
}
</style>
