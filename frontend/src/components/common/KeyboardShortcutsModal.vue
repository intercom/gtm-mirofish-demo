<script setup>
import AppModal from './AppModal.vue'
import { useKeyboardShortcuts } from '../../composables/useKeyboardShortcuts'

const { showHelp, shortcuts } = useKeyboardShortcuts()
</script>

<template>
  <AppModal :open="showHelp" title="Keyboard Shortcuts" @close="showHelp = false">
    <div class="space-y-5">
      <div v-for="group in shortcuts" :key="group.group">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-[--color-text-muted] mb-2">
          {{ group.group }}
        </h3>
        <ul class="space-y-1.5">
          <li
            v-for="item in group.items"
            :key="item.description"
            class="flex items-center justify-between py-1.5 px-2 rounded-md hover:bg-[--color-surface-hover]"
          >
            <span class="text-sm text-[--color-text]">{{ item.description }}</span>
            <span class="flex items-center gap-1">
              <kbd
                v-for="(key, i) in item.keys"
                :key="i"
                class="kbd"
              >{{ key }}</kbd>
              <span
                v-if="item.keys.length > 1"
                class="hidden"
              />
            </span>
          </li>
        </ul>
      </div>
    </div>

    <template #footer>
      <p class="text-xs text-[--color-text-muted] text-center">
        Press <kbd class="kbd">?</kbd> anywhere to toggle this dialog
      </p>
    </template>
  </AppModal>
</template>

<style scoped>
.kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.375rem;
  font-family: inherit;
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1;
  color: var(--color-text);
  background: var(--color-surface-hover, #f3f4f6);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: 0 1px 0 var(--color-border);
}
</style>
