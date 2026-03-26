<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTutorialStore } from '../../stores/tutorial'
import { keyboardShortcuts } from '../../data/help-content'

const route = useRoute()
const tutorial = useTutorialStore()

const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform)

// Dragging state
const cardRef = ref(null)
const position = ref({ x: null, y: null })
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

// Context-aware: pick relevant shortcut groups for current page
const contextGroups = computed(() => {
  const groups = [{ name: 'Global', shortcuts: keyboardShortcuts.global }]
  const name = route.name

  if (name === 'workspace') {
    groups.push({ name: 'Workspace', shortcuts: keyboardShortcuts.workspace })
    groups.push({ name: 'Simulation', shortcuts: keyboardShortcuts.simulation })
  } else {
    groups.push({ name: 'Navigation', shortcuts: keyboardShortcuts.navigation })
  }

  return groups
})

function formatKeys(shortcut) {
  const keys = isMac ? shortcut.mac : shortcut.keys
  return keys
}

// Dragging
function onMouseDown(e) {
  if (e.target.closest('button')) return
  isDragging.value = true
  const card = cardRef.value
  if (!card) return
  const rect = card.getBoundingClientRect()
  dragOffset.value = { x: e.clientX - rect.left, y: e.clientY - rect.top }
  e.preventDefault()
}

function onMouseMove(e) {
  if (!isDragging.value) return
  position.value = {
    x: e.clientX - dragOffset.value.x,
    y: e.clientY - dragOffset.value.y,
  }
}

function onMouseUp() {
  isDragging.value = false
}

const cardStyle = computed(() => {
  if (position.value.x !== null) {
    return {
      top: `${position.value.y}px`,
      left: `${position.value.x}px`,
      right: 'auto',
      bottom: 'auto',
    }
  }
  return {}
})

// Keyboard shortcut: Ctrl/Cmd + /
function onKeyDown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key === '/') {
    e.preventDefault()
    tutorial.toggleShortcutRef()
  }
  if (e.key === 'Escape' && tutorial.isShortcutRefOpen && !tutorial.isShortcutRefPinned) {
    tutorial.closeShortcutRef()
  }
}

onMounted(() => document.addEventListener('keydown', onKeyDown))
onUnmounted(() => {
  document.removeEventListener('keydown', onKeyDown)
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
})

// Attach move/up listeners when dragging starts
function startDrag(e) {
  onMouseDown(e)
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', function handler() {
    onMouseUp()
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', handler)
  })
}
</script>

<template>
  <Teleport to="body">
    <Transition name="shortcut-ref">
      <div
        v-if="tutorial.isShortcutRefOpen"
        ref="cardRef"
        class="shortcut-card"
        :class="{ 'shortcut-card--dragging': isDragging }"
        :style="cardStyle"
        @mousedown="startDrag"
      >
        <!-- Header -->
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-bold text-[var(--color-text)]">Keyboard Shortcuts</span>
          <div class="flex items-center gap-1">
            <!-- Pin button -->
            <button
              class="shortcut-btn"
              :class="{ 'shortcut-btn--active': tutorial.isShortcutRefPinned }"
              @click="tutorial.pinShortcutRef()"
              :title="tutorial.isShortcutRefPinned ? 'Unpin' : 'Pin'"
              aria-label="Pin shortcut reference"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <line x1="12" y1="17" x2="12" y2="22" />
                <path d="M5 17h14v-1.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V6h1a2 2 0 0 0 0-4H8a2 2 0 0 0 0 4h1v4.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24Z" />
              </svg>
            </button>
            <!-- Close button -->
            <button
              class="shortcut-btn"
              @click="tutorial.closeShortcutRef()"
              aria-label="Close shortcut reference"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Shortcut groups -->
        <div class="space-y-3">
          <div v-for="group in contextGroups" :key="group.name">
            <div class="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">
              {{ group.name }}
            </div>
            <div class="space-y-1">
              <div
                v-for="shortcut in group.shortcuts"
                :key="shortcut.label"
                class="flex items-center justify-between"
              >
                <span class="text-xs text-[var(--color-text-muted)]">{{ shortcut.label }}</span>
                <span class="flex items-center gap-0.5">
                  <kbd
                    v-for="(key, ki) in formatKeys(shortcut)"
                    :key="ki"
                    class="shortcut-key"
                  >{{ key }}</kbd>
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer hint -->
        <div class="mt-3 pt-2 border-t border-[var(--color-border)] text-center">
          <span class="text-[10px] text-[var(--color-text-muted)]">
            Press <kbd class="shortcut-key">{{ isMac ? 'Cmd' : 'Ctrl' }}</kbd><kbd class="shortcut-key">/</kbd> to toggle
          </span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.shortcut-card {
  position: fixed;
  top: 72px;
  right: 16px;
  width: 280px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
  z-index: 9000;
  cursor: grab;
  user-select: none;
}
.shortcut-card--dragging {
  cursor: grabbing;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
}

.shortcut-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color 0.15s, background-color 0.15s;
}
.shortcut-btn:hover {
  color: var(--color-text);
  background: var(--color-border);
}
.shortcut-btn--active {
  color: #2068FF;
  background: rgba(32, 104, 255, 0.08);
}

.shortcut-key {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  font-family: inherit;
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-bg, #f9fafb);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 4px;
}

.shortcut-ref-enter-active,
.shortcut-ref-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.shortcut-ref-enter-from,
.shortcut-ref-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
