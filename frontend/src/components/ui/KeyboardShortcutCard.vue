<script setup>
import { computed } from 'vue'
import { useKeyboardShortcuts } from '../../composables/useKeyboardShortcuts'

const { visible, shortcuts, close, isMac } = useKeyboardShortcuts()

const leftColumn = computed(() => shortcuts.slice(0, Math.ceil(shortcuts.length / 2)))
const rightColumn = computed(() => shortcuts.slice(Math.ceil(shortcuts.length / 2)))

function onBackdropClick(e) {
  if (e.target === e.currentTarget) close()
}
</script>

<template>
  <Teleport to="body">
    <Transition name="shortcut-card">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-[2px]"
        @click="onBackdropClick"
      >
        <div class="shortcut-card">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
            <div class="flex items-center gap-2.5">
              <div class="shortcut-icon-wrap">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M6 4h12a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2zm1 4h2v2H7V8zm4 0h2v2h-2V8zm4 0h2v2h-2V8zm-8 4h2v2H7v-2zm4 4h2v2h-2v-2zm4-4h2v2h-2v-2z" />
                </svg>
              </div>
              <div>
                <h2 class="text-sm font-semibold text-[var(--color-text)]">Keyboard Shortcuts</h2>
                <p class="text-xs text-[var(--color-text-muted)]">Quick reference for all shortcuts</p>
              </div>
            </div>
            <button
              class="w-7 h-7 flex items-center justify-center rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-border)] transition-colors cursor-pointer"
              @click="close"
              aria-label="Close"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Two-column shortcut grid -->
          <div class="shortcut-grid">
            <div class="shortcut-column">
              <div v-for="group in leftColumn" :key="group.group" class="shortcut-group">
                <h3 class="shortcut-group-title">{{ group.group }}</h3>
                <ul class="space-y-1">
                  <li
                    v-for="item in group.items"
                    :key="item.description"
                    class="shortcut-row"
                  >
                    <span class="shortcut-label">{{ item.description }}</span>
                    <span class="flex items-center gap-0.5">
                      <kbd
                        v-for="(key, ki) in item.keys"
                        :key="ki"
                        class="kbd"
                      >{{ key }}</kbd>
                    </span>
                  </li>
                </ul>
              </div>
            </div>
            <div class="shortcut-divider" />
            <div class="shortcut-column">
              <div v-for="group in rightColumn" :key="group.group" class="shortcut-group">
                <h3 class="shortcut-group-title">{{ group.group }}</h3>
                <ul class="space-y-1">
                  <li
                    v-for="item in group.items"
                    :key="item.description"
                    class="shortcut-row"
                  >
                    <span class="shortcut-label">{{ item.description }}</span>
                    <span class="flex items-center gap-0.5">
                      <kbd
                        v-for="(key, ki) in item.keys"
                        :key="ki"
                        class="kbd"
                      >{{ key }}</kbd>
                    </span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-3 border-t border-[var(--color-border)] flex items-center justify-between">
            <span class="text-xs text-[var(--color-text-muted)]">
              {{ isMac ? 'macOS' : 'Windows / Linux' }}
            </span>
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
  border-radius: var(--radius-xl, 1rem);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-width: 680px;
  margin: 0 1rem;
  overflow: hidden;
}

.shortcut-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  background: #2068FF;
  flex-shrink: 0;
}

.shortcut-grid {
  display: flex;
  padding: 1.25rem 1.5rem;
  gap: 0;
}

.shortcut-column {
  flex: 1;
  min-width: 0;
}

.shortcut-divider {
  width: 1px;
  background: var(--color-border);
  margin: 0 1.25rem;
  flex-shrink: 0;
}

.shortcut-group {
  margin-bottom: 1rem;
}
.shortcut-group:last-child {
  margin-bottom: 0;
}

.shortcut-group-title {
  font-size: 0.625rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  margin-bottom: 0.5rem;
  padding-bottom: 0.25rem;
}

.shortcut-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.25rem 0;
  gap: 0.75rem;
}

.shortcut-label {
  font-size: 0.8125rem;
  color: var(--color-text-secondary, var(--color-text));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.375rem;
  padding: 0 0.375rem;
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 0.6875rem;
  font-weight: 500;
  line-height: 1;
  color: var(--color-text);
  background: var(--color-bg-alt, #f4f4f5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm, 0.25rem);
  box-shadow: 0 1px 0 var(--color-border);
  white-space: nowrap;
}

.kbd-sm {
  min-width: 1.125rem;
  height: 1.125rem;
  padding: 0 0.25rem;
  font-size: 0.625rem;
}

/* Responsive: stack on narrow screens */
@media (max-width: 560px) {
  .shortcut-card {
    max-width: 400px;
  }
  .shortcut-grid {
    flex-direction: column;
    gap: 0;
  }
  .shortcut-divider {
    width: 100%;
    height: 1px;
    margin: 0.75rem 0;
  }
}

/* Transitions */
.shortcut-card-enter-active,
.shortcut-card-leave-active {
  transition: opacity 150ms ease;
}
.shortcut-card-enter-active .shortcut-card,
.shortcut-card-leave-active .shortcut-card {
  transition: transform 150ms ease;
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
