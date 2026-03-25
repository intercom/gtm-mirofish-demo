<script setup>
import { ref, computed } from 'vue'
import { getWidgetsByCategory } from './WidgetRegistry.js'

defineProps({
  open: Boolean,
})

const emit = defineEmits(['close', 'add-widget'])

const search = ref('')

const filteredCategories = computed(() => {
  const q = search.value.toLowerCase().trim()
  if (!q) return getWidgetsByCategory()
  return getWidgetsByCategory()
    .map((cat) => ({
      ...cat,
      widgets: cat.widgets.filter(
        (w) =>
          w.label.toLowerCase().includes(q) ||
          w.description.toLowerCase().includes(q) ||
          w.type.includes(q),
      ),
    }))
    .filter((cat) => cat.widgets.length > 0)
})

const hasResults = computed(() => filteredCategories.value.some((c) => c.widgets.length > 0))

function onDragStart(e, widgetDef) {
  e.dataTransfer.effectAllowed = 'copy'
  e.dataTransfer.setData('application/widget-type', widgetDef.type)

  // Create a compact drag ghost
  const ghost = document.createElement('div')
  ghost.textContent = widgetDef.label
  ghost.style.cssText =
    'position:absolute;top:-9999px;padding:8px 16px;background:#2068FF;color:#fff;border-radius:8px;font-size:14px;font-weight:600;white-space:nowrap;'
  document.body.appendChild(ghost)
  e.dataTransfer.setDragImage(ghost, 0, 0)
  requestAnimationFrame(() => ghost.remove())
}

function addWidget(widgetDef) {
  emit('add-widget', {
    type: widgetDef.type,
    config: { ...widgetDef.defaultConfig },
    size: { ...widgetDef.defaultSize },
  })
}

const ICON_PATHS = {
  'chart-line': 'M3 17l4-4 4 4 8-8M14 5h5v5',
  'chart-bar': 'M4 20V10m5 10V4m5 16v-7m5 7V9',
  'chart-donut': 'M12 2a10 10 0 110 20 10 10 0 010-20zm0 5a5 5 0 100 10 5 5 0 000-10z',
  metric: 'M9 19V6l12-3v13M9 19a3 3 0 11-6 0 3 3 0 016 0zm12-3a3 3 0 11-6 0 3 3 0 016 0z',
  table: 'M3 10h18M3 14h18M3 6h18M3 18h18M10 6v12M16 6v12',
  funnel: 'M3 4h18l-6 7v6l-6 3V11L3 4z',
  text: 'M4 6h16M4 10h12M4 14h14M4 18h10',
  activity: 'M22 12h-4l-3 9L9 3l-3 9H2',
}
</script>

<template>
  <Teleport to="body">
    <Transition name="picker">
      <div v-if="open" class="picker-overlay" @click.self="emit('close')">
        <aside class="picker-panel">
          <header class="picker-header">
            <h2 class="picker-title">Add Widget</h2>
            <button class="picker-close" @click="emit('close')" aria-label="Close picker">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </header>

          <div class="picker-search">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
            </svg>
            <input
              v-model="search"
              type="text"
              placeholder="Search widgets..."
              class="search-input"
            />
            <button v-if="search" class="search-clear" @click="search = ''">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="picker-body">
            <template v-if="hasResults">
              <div v-for="cat in filteredCategories" :key="cat.id" class="picker-category">
                <h3 class="category-label">{{ cat.label }}</h3>
                <div class="widget-grid">
                  <div
                    v-for="w in cat.widgets"
                    :key="w.type"
                    class="widget-card"
                    draggable="true"
                    @dragstart="onDragStart($event, w)"
                    @click="addWidget(w)"
                    :title="`Drag to add ${w.label} or click`"
                  >
                    <div class="widget-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path :d="ICON_PATHS[w.icon]" />
                      </svg>
                    </div>
                    <span class="widget-label">{{ w.label }}</span>
                    <span class="widget-desc">{{ w.description }}</span>
                    <div class="drag-hint">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M8 6h.01M8 12h.01M8 18h.01M16 6h.01M16 12h.01M16 18h.01" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </template>
            <div v-else class="picker-empty">
              <p>No widgets match "{{ search }}"</p>
              <button class="clear-btn" @click="search = ''">Clear search</button>
            </div>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.picker-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  justify-content: flex-end;
}

.picker-panel {
  width: 360px;
  max-width: 100vw;
  height: 100%;
  background: var(--color-surface);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.picker-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.picker-close {
  padding: var(--space-1);
  border-radius: var(--radius);
  color: var(--color-text-muted);
  cursor: pointer;
  background: none;
  border: none;
  transition: var(--transition-fast);
}

.picker-close:hover {
  background: var(--color-tint);
  color: var(--color-text);
}

.picker-search {
  position: relative;
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.search-icon {
  position: absolute;
  left: calc(var(--space-5) + 10px);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: var(--space-2) var(--space-4) var(--space-2) calc(var(--space-8) + 4px);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: var(--text-sm);
  background: var(--color-bg);
  color: var(--color-text);
  outline: none;
  transition: var(--transition-fast);
}

.search-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

.search-clear {
  position: absolute;
  right: calc(var(--space-5) + 10px);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted);
  cursor: pointer;
  background: none;
  border: none;
  padding: 2px;
}

.picker-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-5);
}

.picker-category {
  margin-bottom: var(--space-5);
}

.category-label {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
  letter-spacing: var(--letter-spacing-wide);
  color: var(--color-text-muted);
  margin-bottom: var(--space-3);
}

.widget-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}

.widget-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: grab;
  user-select: none;
  transition: var(--transition-fast);
}

.widget-card:hover {
  border-color: var(--color-primary-border);
  background: var(--color-primary-lighter);
  box-shadow: var(--shadow);
}

.widget-card:active {
  cursor: grabbing;
  transform: scale(0.97);
}

.widget-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
  background: var(--color-primary-light);
  color: var(--color-primary);
  margin-bottom: var(--space-1);
  transition: var(--transition-fast);
}

.widget-card:hover .widget-icon {
  background: var(--color-primary);
  color: #fff;
}

.widget-label {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  text-align: center;
}

.widget-desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: center;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.drag-hint {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  color: var(--color-text-muted);
  opacity: 0;
  transition: var(--transition-fast);
}

.widget-card:hover .drag-hint {
  opacity: 0.6;
}

.picker-empty {
  text-align: center;
  padding: var(--space-8) 0;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.clear-btn {
  margin-top: var(--space-3);
  padding: var(--space-2) var(--space-4);
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  color: var(--color-primary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: var(--transition-fast);
}

.clear-btn:hover {
  background: var(--color-primary-light);
}

/* Slide-over transitions */
.picker-enter-active,
.picker-leave-active {
  transition: opacity 0.25s ease;
}
.picker-enter-active .picker-panel,
.picker-leave-active .picker-panel {
  transition: transform 0.25s ease;
}
.picker-enter-from,
.picker-leave-to {
  opacity: 0;
}
.picker-enter-from .picker-panel,
.picker-leave-to .picker-panel {
  transform: translateX(100%);
}
</style>
