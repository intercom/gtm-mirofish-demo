<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { GridLayout, GridItem } from 'grid-layout-plus'
import { getWidgetDef } from './WidgetRegistry.js'

const props = defineProps({
  layout: {
    type: Array,
    required: true,
  },
  editMode: {
    type: Boolean,
    default: false,
  },
  rowHeight: {
    type: Number,
    default: 80,
  },
  colNum: {
    type: Number,
    default: 12,
  },
})

const emit = defineEmits(['update:layout', 'remove-widget', 'select-widget'])

const isDragging = ref(false)
const isResizing = ref(false)
const isDragOver = ref(false)
const activeItemId = ref(null)

const internalLayout = computed({
  get: () => props.layout,
  set: (val) => emit('update:layout', val),
})

function onLayoutUpdated(newLayout) {
  emit('update:layout', newLayout)
}

function onMoveStart(i) {
  isDragging.value = true
  activeItemId.value = i
}

function onMoveEnd() {
  isDragging.value = false
  activeItemId.value = null
}

function onResizeStart(i) {
  isResizing.value = true
  activeItemId.value = i
}

function onResizeEnd() {
  isResizing.value = false
  activeItemId.value = null
}

// --- Drop from WidgetPicker ---

function onDragOver(e) {
  if (!props.editMode) return
  e.preventDefault()
  e.dataTransfer.dropEffect = 'copy'
  isDragOver.value = true
}

function onDragLeave() {
  isDragOver.value = false
}

function onDrop(e) {
  isDragOver.value = false
  if (!props.editMode) return

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
    w: def.defaultSize.width ?? def.defaultSize.w ?? 4,
    h: def.defaultSize.height ?? def.defaultSize.h ?? 3,
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
    :class="{
      'dashboard-grid--edit': editMode,
      'dashboard-grid--dragging': isDragging,
      'dashboard-grid--resizing': isResizing,
      'dashboard-grid--drag-over': isDragOver,
    }"
    @dragover="onDragOver"
    @dragleave.self="onDragLeave"
    @drop="onDrop"
  >
    <!-- Edit mode grid background -->
    <div v-if="editMode" class="dashboard-grid__bg" />

    <GridLayout
      v-model:layout="internalLayout"
      :col-num="colNum"
      :row-height="rowHeight"
      :is-draggable="editMode"
      :is-resizable="editMode"
      :prevent-collision="true"
      :vertical-compact="true"
      :use-css-transforms="true"
      :margin="[12, 12]"
      @layout-updated="onLayoutUpdated"
    >
      <GridItem
        v-for="item in internalLayout"
        :key="item.i"
        :x="item.x"
        :y="item.y"
        :w="item.w"
        :h="item.h"
        :i="item.i"
        :min-w="2"
        :min-h="1"
        :is-draggable="editMode"
        :is-resizable="editMode"
        drag-allow-from=".widget-drag-handle"
        class="dashboard-grid__item"
        :class="{
          'dashboard-grid__item--active': activeItemId === item.i,
          'dashboard-grid__item--edit': editMode,
        }"
        @move="onMoveStart(item.i)"
        @moved="onMoveEnd"
        @resize="onResizeStart(item.i)"
        @resized="onResizeEnd"
      >
        <div class="widget-wrapper" @click="selectWidget(item.i)">
          <!-- Edit mode header: drag handle + remove button -->
          <div v-if="editMode" class="widget-header">
            <div class="widget-drag-handle" title="Drag to move">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <circle cx="5" cy="3" r="1.2" />
                <circle cx="11" cy="3" r="1.2" />
                <circle cx="5" cy="8" r="1.2" />
                <circle cx="11" cy="8" r="1.2" />
                <circle cx="5" cy="13" r="1.2" />
                <circle cx="11" cy="13" r="1.2" />
              </svg>
              <span class="widget-drag-label">{{ widgetLabel(item) }}</span>
            </div>
            <button
              class="widget-remove-btn"
              title="Remove widget"
              @click.stop="removeWidget(item.i)"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                <line x1="3" y1="3" x2="11" y2="11" />
                <line x1="11" y1="3" x2="3" y2="11" />
              </svg>
            </button>
          </div>

          <!-- Widget content slot -->
          <div class="widget-content">
            <slot :name="`widget-${item.i}`" :item="item">
              <div class="widget-placeholder">
                <span class="text-sm text-[var(--color-text-muted)]">{{ widgetLabel(item) }}</span>
              </div>
            </slot>
          </div>
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
      <p class="empty-title">{{ editMode ? 'Drag widgets here' : 'No widgets yet' }}</p>
      <p class="empty-desc">
        {{ editMode ? 'Open the widget picker and drag items onto this grid' : 'Switch to edit mode to add widgets' }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.dashboard-grid {
  position: relative;
  min-height: 200px;
}

/* Edit mode background grid lines */
.dashboard-grid__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background-image:
    repeating-linear-gradient(
      90deg,
      var(--color-primary-light) 0px,
      var(--color-primary-light) 1px,
      transparent 1px,
      transparent
    ),
    repeating-linear-gradient(
      0deg,
      var(--color-primary-light) 0px,
      var(--color-primary-light) 1px,
      transparent 1px,
      transparent
    );
  background-size: calc(100% / 12) 92px; /* colNum=12, rowHeight+margin */
  border-radius: var(--radius-lg);
  opacity: 0.6;
}

.dashboard-grid--drag-over {
  outline: 2px dashed var(--color-primary);
  outline-offset: -2px;
  background-color: var(--color-primary-lighter);
}

.dashboard-grid__item {
  transition: box-shadow 0.2s ease;
}

.dashboard-grid__item--edit {
  border-radius: var(--radius-lg);
  outline: 1px dashed var(--color-border);
  outline-offset: -1px;
}

.dashboard-grid__item--active {
  z-index: 10;
  outline-color: var(--color-primary);
  outline-style: solid;
  outline-width: 2px;
}

.widget-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: box-shadow var(--transition-fast);
}

.dashboard-grid--edit .widget-wrapper:hover {
  box-shadow: var(--shadow-md);
}

.widget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  background: var(--color-tint);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.widget-drag-handle {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: grab;
  color: var(--color-text-muted);
  padding: 2px 4px;
  border-radius: var(--radius-sm);
  transition: color var(--transition-fast), background var(--transition-fast);
}

.widget-drag-handle:hover {
  color: var(--color-primary);
  background: var(--color-primary-light);
}

.widget-drag-handle:active {
  cursor: grabbing;
}

.widget-drag-label {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
}

.widget-remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: color var(--transition-fast), background var(--transition-fast);
}

.widget-remove-btn:hover {
  color: var(--color-error);
  background: var(--color-error-light);
}

.widget-content {
  flex: 1;
  overflow: auto;
}

.widget-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 60px;
}

/* Dragging state: show blue guidelines */
.dashboard-grid--dragging .dashboard-grid__bg {
  opacity: 1;
  background-image:
    repeating-linear-gradient(
      90deg,
      var(--color-primary-tint) 0px,
      var(--color-primary-tint) 1px,
      transparent 1px,
      transparent
    ),
    repeating-linear-gradient(
      0deg,
      var(--color-primary-tint) 0px,
      var(--color-primary-tint) 1px,
      transparent 1px,
      transparent
    );
}

/* Resize cursor overrides */
.dashboard-grid--resizing {
  cursor: nwse-resize;
}

/* Empty state */
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

/* grid-layout-plus default styles need slight overrides */
:deep(.vue-grid-item.vue-grid-placeholder) {
  background: var(--color-primary-light) !important;
  border: 2px dashed var(--color-primary) !important;
  border-radius: var(--radius-lg);
  opacity: 0.6;
}

:deep(.vue-grid-item > .vue-resizable-handle) {
  width: 16px;
  height: 16px;
  bottom: 2px;
  right: 2px;
  background: none;
}

:deep(.vue-grid-item > .vue-resizable-handle::after) {
  content: '';
  position: absolute;
  right: 3px;
  bottom: 3px;
  width: 8px;
  height: 8px;
  border-right: 2px solid var(--color-text-muted);
  border-bottom: 2px solid var(--color-text-muted);
  border-radius: 0 0 2px 0;
  transition: border-color var(--transition-fast);
}

:deep(.vue-grid-item:hover > .vue-resizable-handle::after) {
  border-color: var(--color-primary);
}
</style>
