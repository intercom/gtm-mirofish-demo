<script setup>
import { ref, computed, nextTick } from 'vue'
import { GridLayout, GridItem } from 'grid-layout-plus'
import { getWidgetDef } from './WidgetRegistry.js'

const props = defineProps({
  layout: { type: Array, required: true },
  editing: { type: Boolean, default: false },
})

const emit = defineEmits(['update:layout', 'remove-widget', 'select-widget'])

const isDragOver = ref(false)
const activeItemId = ref(null)

const colNum = 12
const rowHeight = 80

const gridLayout = computed({
  get: () => props.layout,
  set: (val) => emit('update:layout', val),
})

function onLayoutUpdated(newLayout) {
  emit('update:layout', newLayout)
}

// --- Drop from WidgetPicker ---

function onDragOver(e) {
  if (!props.editing) return
  e.preventDefault()
  e.dataTransfer.dropEffect = 'copy'
  isDragOver.value = true
}

function onDragLeave() {
  isDragOver.value = false
}

function onDrop(e) {
  isDragOver.value = false
  if (!props.editing) return

  const widgetType = e.dataTransfer.getData('application/widget-type')
  if (!widgetType) return
  e.preventDefault()

  const def = getWidgetDef(widgetType)
  if (!def) return

  // Find lowest open Y position
  const maxY = props.layout.reduce((max, item) => Math.max(max, item.y + item.h), 0)

  const newItem = {
    i: `widget-${Date.now()}`,
    x: 0,
    y: maxY,
    w: def.defaultSize.w,
    h: def.defaultSize.h,
    type: widgetType,
    config: { ...def.defaultConfig },
  }

  emit('update:layout', [...props.layout, newItem])
  nextTick(() => {
    activeItemId.value = newItem.i
  })
}

function removeWidget(id) {
  emit('remove-widget', id)
}

function selectWidget(id) {
  activeItemId.value = id
  emit('select-widget', id)
}

function widgetLabel(item) {
  const def = getWidgetDef(item.type)
  return def ? def.label : item.type
}
</script>

<template>
  <div
    class="dashboard-grid"
    :class="{ editing, 'drag-over': isDragOver }"
    @dragover="onDragOver"
    @dragleave.self="onDragLeave"
    @drop="onDrop"
  >
    <GridLayout
      v-model:layout="gridLayout"
      :col-num="colNum"
      :row-height="rowHeight"
      :is-draggable="editing"
      :is-resizable="editing"
      :vertical-compact="true"
      :use-css-transforms="true"
      :margin="[16, 16]"
      @layout-updated="onLayoutUpdated"
    >
      <GridItem
        v-for="item in layout"
        :key="item.i"
        :i="item.i"
        :x="item.x"
        :y="item.y"
        :w="item.w"
        :h="item.h"
        :is-draggable="editing"
        :is-resizable="editing"
        drag-allow-from=".widget-drag-handle"
        drag-ignore-from=".widget-content"
        class="grid-item"
        :class="{ active: activeItemId === item.i }"
        @click="selectWidget(item.i)"
      >
        <div class="widget-wrapper">
          <div v-if="editing" class="widget-drag-handle" title="Drag to reposition">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M8 6h.01M8 12h.01M8 18h.01M16 6h.01M16 12h.01M16 18h.01" />
            </svg>
            <span class="handle-label">{{ widgetLabel(item) }}</span>
          </div>
          <div class="widget-content">
            <div class="widget-placeholder">
              <span class="widget-type-badge">{{ widgetLabel(item) }}</span>
            </div>
          </div>
          <button
            v-if="editing"
            class="widget-remove"
            @click.stop="removeWidget(item.i)"
            title="Remove widget"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
      </GridItem>
    </GridLayout>

    <!-- Empty state / drop zone hint -->
    <div v-if="layout.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
        </svg>
      </div>
      <p class="empty-title">{{ editing ? 'Drag widgets here' : 'No widgets yet' }}</p>
      <p class="empty-desc">
        {{ editing ? 'Open the widget picker and drag items onto this grid' : 'Switch to edit mode to add widgets' }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.dashboard-grid {
  position: relative;
  min-height: 400px;
  border-radius: var(--radius-lg);
  transition: var(--transition-fast);
}

.dashboard-grid.editing {
  background-image:
    linear-gradient(to right, var(--color-border) 1px, transparent 1px),
    linear-gradient(to bottom, var(--color-border) 1px, transparent 1px);
  background-size: calc(100% / 12) 80px;
  background-position: -1px -1px;
  background-color: var(--color-bg);
  border: 2px dashed var(--color-border);
}

.dashboard-grid.drag-over {
  border-color: var(--color-primary);
  background-color: var(--color-primary-lighter);
}

.grid-item {
  touch-action: none;
}

.widget-wrapper {
  position: relative;
  height: 100%;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: var(--transition-fast);
}

.grid-item.active .widget-wrapper {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

.editing .widget-wrapper:hover {
  box-shadow: var(--shadow-md);
}

.widget-drag-handle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  cursor: grab;
  user-select: none;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
}

.widget-drag-handle:active {
  cursor: grabbing;
  background: var(--color-primary-light);
}

.handle-label {
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
}

.widget-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-3);
}

.widget-placeholder {
  text-align: center;
}

.widget-type-badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.widget-remove {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  color: var(--color-text-muted);
  cursor: pointer;
  opacity: 0;
  transition: var(--transition-fast);
}

.widget-wrapper:hover .widget-remove {
  opacity: 1;
}

.widget-remove:hover {
  background: var(--color-error-light);
  border-color: var(--color-error);
  color: var(--color-error);
}

.empty-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.empty-icon {
  color: var(--color-text-muted);
  opacity: 0.3;
  margin-bottom: var(--space-4);
}

.empty-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.empty-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}
</style>
