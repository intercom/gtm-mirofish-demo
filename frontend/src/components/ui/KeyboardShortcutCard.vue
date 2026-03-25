<script setup>
import { useKeyboardShortcuts } from '../../composables/useKeyboardShortcuts'

const { visible, shortcuts, close } = useKeyboardShortcuts()

function onBackdropClick(e) {
  if (e.target === e.currentTarget) close()
}
</script>

<template>
  <Teleport to="body">
    <Transition name="shortcut-card">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click="onBackdropClick"
      >
        <div class="shortcut-card">
          <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-[var(--color-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                  d="M6 4h12a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2zm1 4h2v2H7V8zm4 0h2v2h-2V8zm4 0h2v2h-2V8zm-8 4h2v2H7v-2zm4 4h2v2h-2v-2zm4-4h2v2h-2v-2zm-8 4h2v2H7v-2zm8 0h2v2h-2v-2z" />
              </svg>
              <h2 class="text-base font-semibold text-[var(--color-text)]">Keyboard Shortcuts</h2>
            </div>
            <button
              class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors cursor-pointer"
              @click="close"
              aria-label="Close"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="px-6 py-5 space-y-5">
            <div v-for="group in shortcuts" :key="group.group">
              <h3 class="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-2.5">
                {{ group.group }}
              </h3>
              <ul class="space-y-2">
                <li
                  v-for="item in group.items"
                  :key="item.description"
                  class="flex items-center justify-between"
                >
                  <span class="text-sm text-[var(--color-text-secondary)]">{{ item.description }}</span>
                  <span class="flex items-center gap-1">
                    <kbd
                      v-for="key in item.keys"
                      :key="key"
                      class="kbd"
                    >{{ key }}</kbd>
                  </span>
                </li>
              </ul>
            </div>
          </div>

          <div class="px-6 py-3 border-t border-[var(--color-border)] text-center">
            <span class="text-xs text-[var(--color-text-muted)]">
              Press <kbd class="kbd kbd-sm">?</kbd> to toggle &middot; <kbd class="kbd kbd-sm">Esc</kbd> to close
            </span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.shortcut-card {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-width: 380px;
  margin: 0 1rem;
}

.kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.75rem;
  height: 1.625rem;
  padding: 0 0.5rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1;
  color: var(--color-text);
  background: var(--color-bg-alt, #f4f4f5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  box-shadow: 0 1px 0 var(--color-border);
}

.kbd-sm {
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.35rem;
  font-size: 0.625rem;
}

.shortcut-card-enter-active,
.shortcut-card-leave-active {
  transition: opacity var(--transition-fast);
}
.shortcut-card-enter-active .shortcut-card,
.shortcut-card-leave-active .shortcut-card {
  transition: transform var(--transition-fast);
}
.shortcut-card-enter-from,
.shortcut-card-leave-to {
  opacity: 0;
}
.shortcut-card-enter-from .shortcut-card {
  transform: scale(0.95);
}
.shortcut-card-leave-to .shortcut-card {
  transform: scale(0.95);
}
</style>
