<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  sections: { type: Array, default: () => [] },
  mode: { type: String, default: 'edit', validator: (v) => ['edit', 'preview'].includes(v) },
  pageSize: { type: String, default: 'letter', validator: (v) => ['letter', 'a4'].includes(v) },
})

const emit = defineEmits([
  'update:sections',
  'edit-section',
  'add-section',
])

const dragState = ref({
  active: false,
  sourceIndex: null,
  overIndex: null,
  isExternal: false,
})

const activeDropZone = ref(null)

const isEdit = computed(() => props.mode === 'edit')

const pageAspect = computed(() => (props.pageSize === 'a4' ? 1.4142 : 1.2941))

// Group sections into rows: full-width sections get their own row,
// consecutive half-width sections are paired.
const rows = computed(() => {
  const result = []
  let i = 0
  while (i < props.sections.length) {
    const section = props.sections[i]
    if (section.width === 'half' && i + 1 < props.sections.length && props.sections[i + 1].width === 'half') {
      result.push({
        type: 'two-col',
        sections: [section, props.sections[i + 1]],
        startIndex: i,
      })
      i += 2
    } else {
      result.push({
        type: 'full',
        sections: [section],
        startIndex: i,
      })
      i++
    }
  }
  return result
})

function sectionIcon(type) {
  const icons = {
    heading: 'H',
    paragraph: '\u00B6',
    callout: '!',
    'line-chart': '\u2197',
    'bar-chart': '\u2581',
    'donut-chart': '\u25CE',
    'radar-chart': '\u25C7',
    table: '\u2637',
    'kpi-row': '#',
    'metric-cards': '\u25A3',
    divider: '\u2500',
    spacer: '\u2195',
    columns: '\u2503',
  }
  return icons[type] || '\u25A1'
}

function sectionLabel(type) {
  return type.split('-').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ')
}

// --- Drag & Drop: internal reorder ---

function onDragStart(e, index) {
  dragState.value = { active: true, sourceIndex: index, overIndex: null, isExternal: false }
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(index))
}

function onDragEnd() {
  dragState.value = { active: false, sourceIndex: null, overIndex: null, isExternal: false }
  activeDropZone.value = null
}

// --- Drop zones ---

function onDropZoneDragOver(e, insertIndex) {
  e.preventDefault()
  e.dataTransfer.dropEffect = 'move'
  activeDropZone.value = insertIndex
}

function onDropZoneDragLeave(e, insertIndex) {
  if (activeDropZone.value === insertIndex) {
    activeDropZone.value = null
  }
}

function onDropZoneDrop(e, insertIndex) {
  e.preventDefault()
  activeDropZone.value = null

  const externalType = e.dataTransfer.getData('application/x-section-type')
  if (externalType) {
    emit('add-section', { type: externalType, index: insertIndex })
    onDragEnd()
    return
  }

  const sourceIndex = parseInt(e.dataTransfer.getData('text/plain'), 10)
  if (isNaN(sourceIndex) || sourceIndex === insertIndex || sourceIndex === insertIndex - 1) {
    onDragEnd()
    return
  }

  const updated = [...props.sections]
  const [moved] = updated.splice(sourceIndex, 1)
  const adjustedIndex = sourceIndex < insertIndex ? insertIndex - 1 : insertIndex
  updated.splice(adjustedIndex, 0, moved)
  emit('update:sections', updated)
  onDragEnd()
}

// --- Section actions ---

function deleteSection(index) {
  const updated = [...props.sections]
  updated.splice(index, 1)
  emit('update:sections', updated)
}

function toggleWidth(index) {
  const updated = [...props.sections]
  updated[index] = {
    ...updated[index],
    width: updated[index].width === 'half' ? 'full' : 'half',
  }
  emit('update:sections', updated)
}

// --- External drag detection ---

function onCanvasDragOver(e) {
  if (!dragState.value.active) {
    const sectionType = e.dataTransfer.types.includes('application/x-section-type')
    if (sectionType) {
      dragState.value = { active: true, sourceIndex: null, overIndex: null, isExternal: true }
    }
  }
}

function onCanvasDragLeave(e) {
  if (dragState.value.isExternal && !e.currentTarget.contains(e.relatedTarget)) {
    onDragEnd()
  }
}

// --- Placeholder rendering for section types ---

function renderPlaceholder(section) {
  const type = section.type
  if (['heading', 'paragraph', 'callout'].includes(type)) return 'text'
  if (type.includes('chart')) return 'chart'
  if (type === 'table') return 'table'
  if (['kpi-row', 'metric-cards'].includes(type)) return 'metrics'
  if (type === 'divider') return 'divider'
  if (type === 'spacer') return 'spacer'
  return 'generic'
}
</script>

<template>
  <div
    class="report-canvas-wrapper"
    @dragover.prevent="onCanvasDragOver"
    @dragleave="onCanvasDragLeave"
  >
    <!-- Page container with aspect ratio -->
    <div
      class="report-page"
      :class="{ 'report-page--edit': isEdit }"
      :style="{ '--page-aspect': pageAspect }"
    >
      <!-- Empty state -->
      <div
        v-if="sections.length === 0"
        class="report-empty"
      >
        <!-- Top drop zone when empty -->
        <div
          v-if="isEdit"
          class="drop-zone drop-zone--empty"
          :class="{ 'drop-zone--active': activeDropZone === 0 }"
          @dragover.prevent="onDropZoneDragOver($event, 0)"
          @dragleave="onDropZoneDragLeave($event, 0)"
          @drop="onDropZoneDrop($event, 0)"
        >
          <div class="drop-zone__indicator">
            <svg class="drop-zone__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 5v14M5 12h14" stroke-linecap="round" />
            </svg>
            <span class="drop-zone__label">Drag sections here or click to add</span>
          </div>
        </div>
        <div v-else class="report-empty__preview">
          <p class="text-sm text-[var(--color-text-muted)]">No sections in this report</p>
        </div>
      </div>

      <!-- Section rows -->
      <template v-for="(row, rowIdx) in rows" :key="'row-' + rowIdx">
        <!-- Drop zone before this row -->
        <div
          v-if="isEdit"
          class="drop-zone"
          :class="{ 'drop-zone--active': activeDropZone === row.startIndex }"
          @dragover.prevent="onDropZoneDragOver($event, row.startIndex)"
          @dragleave="onDropZoneDragLeave($event, row.startIndex)"
          @drop="onDropZoneDrop($event, row.startIndex)"
        >
          <div class="drop-zone__line" />
        </div>

        <!-- Row: full-width or two-column -->
        <div
          class="report-row"
          :class="{ 'report-row--two-col': row.type === 'two-col' }"
        >
          <div
            v-for="(section, colIdx) in row.sections"
            :key="section.id"
            class="report-section"
            :class="{
              'report-section--edit': isEdit,
              'report-section--half': section.width === 'half',
              'report-section--dragging': dragState.sourceIndex === row.startIndex + colIdx,
            }"
            :draggable="isEdit"
            @dragstart="onDragStart($event, row.startIndex + colIdx)"
            @dragend="onDragEnd"
          >
            <!-- Edit mode toolbar -->
            <div v-if="isEdit" class="section-toolbar">
              <button
                class="section-toolbar__btn section-toolbar__drag"
                title="Drag to reorder"
                @mousedown.stop
              >
                <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14">
                  <circle cx="9" cy="6" r="1.5" /><circle cx="15" cy="6" r="1.5" />
                  <circle cx="9" cy="12" r="1.5" /><circle cx="15" cy="12" r="1.5" />
                  <circle cx="9" cy="18" r="1.5" /><circle cx="15" cy="18" r="1.5" />
                </svg>
              </button>

              <span class="section-toolbar__type">{{ sectionLabel(section.type) }}</span>

              <div class="section-toolbar__actions">
                <button
                  class="section-toolbar__btn"
                  title="Toggle width"
                  @click.stop="toggleWidth(row.startIndex + colIdx)"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                    <path d="M4 9h16M4 15h16M9 4v16M15 4v16" v-if="section.width === 'full'" stroke-linecap="round" />
                    <path d="M4 4h16v16H4z" v-else stroke-linecap="round" />
                  </svg>
                </button>
                <button
                  class="section-toolbar__btn"
                  title="Edit section"
                  @click.stop="$emit('edit-section', { section, index: row.startIndex + colIdx })"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" stroke-linecap="round" />
                    <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" stroke-linecap="round" />
                  </svg>
                </button>
                <button
                  class="section-toolbar__btn section-toolbar__btn--danger"
                  title="Delete section"
                  @click.stop="deleteSection(row.startIndex + colIdx)"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                    <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14" stroke-linecap="round" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Section content placeholder -->
            <div class="section-content" :class="'section-content--' + renderPlaceholder(section)">
              <!-- Text types -->
              <template v-if="renderPlaceholder(section) === 'text'">
                <div v-if="section.type === 'heading'" class="placeholder-heading">
                  <div class="placeholder-line placeholder-line--lg" style="width: 60%" />
                </div>
                <div v-else-if="section.type === 'callout'" class="placeholder-callout">
                  <div class="placeholder-callout__icon">{{ sectionIcon(section.type) }}</div>
                  <div class="placeholder-lines">
                    <div class="placeholder-line" style="width: 90%" />
                    <div class="placeholder-line" style="width: 70%" />
                  </div>
                </div>
                <div v-else class="placeholder-paragraph">
                  <div class="placeholder-line" style="width: 100%" />
                  <div class="placeholder-line" style="width: 95%" />
                  <div class="placeholder-line" style="width: 80%" />
                  <div class="placeholder-line" style="width: 60%" />
                </div>
              </template>

              <!-- Chart types -->
              <template v-else-if="renderPlaceholder(section) === 'chart'">
                <div class="placeholder-chart">
                  <div class="placeholder-chart__title">
                    <div class="placeholder-line placeholder-line--sm" style="width: 40%" />
                  </div>
                  <div class="placeholder-chart__area">
                    <svg viewBox="0 0 200 80" preserveAspectRatio="none" class="placeholder-chart__svg">
                      <template v-if="section.type === 'bar-chart'">
                        <rect x="10" y="40" width="20" height="40" rx="2" fill="var(--color-primary)" opacity="0.15" />
                        <rect x="40" y="20" width="20" height="60" rx="2" fill="var(--color-primary)" opacity="0.25" />
                        <rect x="70" y="30" width="20" height="50" rx="2" fill="var(--color-primary)" opacity="0.2" />
                        <rect x="100" y="10" width="20" height="70" rx="2" fill="var(--color-primary)" opacity="0.3" />
                        <rect x="130" y="25" width="20" height="55" rx="2" fill="var(--color-primary)" opacity="0.22" />
                        <rect x="160" y="45" width="20" height="35" rx="2" fill="var(--color-primary)" opacity="0.12" />
                      </template>
                      <template v-else-if="section.type === 'donut-chart'">
                        <circle cx="100" cy="40" r="30" fill="none" stroke="var(--color-primary)" stroke-width="12" opacity="0.2" stroke-dasharray="60 130" />
                        <circle cx="100" cy="40" r="30" fill="none" stroke="var(--color-fin-orange)" stroke-width="12" opacity="0.2" stroke-dasharray="40 150" stroke-dashoffset="-60" />
                        <circle cx="100" cy="40" r="30" fill="none" stroke="var(--color-accent)" stroke-width="12" opacity="0.2" stroke-dasharray="30 160" stroke-dashoffset="-100" />
                      </template>
                      <template v-else>
                        <polyline points="10,60 40,45 70,50 100,20 130,30 160,15 190,25" fill="none" stroke="var(--color-primary)" stroke-width="2" opacity="0.3" />
                        <polyline points="10,65 40,55 70,60 100,40 130,50 160,35 190,45" fill="none" stroke="var(--color-fin-orange)" stroke-width="2" opacity="0.2" />
                      </template>
                    </svg>
                  </div>
                </div>
              </template>

              <!-- Table type -->
              <template v-else-if="renderPlaceholder(section) === 'table'">
                <div class="placeholder-table">
                  <div class="placeholder-table__header">
                    <div class="placeholder-line placeholder-line--sm" style="width: 15%" />
                    <div class="placeholder-line placeholder-line--sm" style="width: 20%" />
                    <div class="placeholder-line placeholder-line--sm" style="width: 12%" />
                    <div class="placeholder-line placeholder-line--sm" style="width: 18%" />
                  </div>
                  <div v-for="r in 3" :key="r" class="placeholder-table__row">
                    <div class="placeholder-line placeholder-line--sm" style="width: 15%" />
                    <div class="placeholder-line placeholder-line--sm" style="width: 20%" />
                    <div class="placeholder-line placeholder-line--sm" style="width: 12%" />
                    <div class="placeholder-line placeholder-line--sm" style="width: 18%" />
                  </div>
                </div>
              </template>

              <!-- Metrics types -->
              <template v-else-if="renderPlaceholder(section) === 'metrics'">
                <div class="placeholder-metrics">
                  <div v-for="m in (section.type === 'kpi-row' ? 3 : 4)" :key="m" class="placeholder-metric-card">
                    <div class="placeholder-line placeholder-line--sm" style="width: 60%" />
                    <div class="placeholder-line placeholder-line--lg" style="width: 40%" />
                  </div>
                </div>
              </template>

              <!-- Divider -->
              <template v-else-if="renderPlaceholder(section) === 'divider'">
                <hr class="placeholder-divider" />
              </template>

              <!-- Spacer -->
              <template v-else-if="renderPlaceholder(section) === 'spacer'">
                <div class="placeholder-spacer" />
              </template>

              <!-- Generic fallback -->
              <template v-else>
                <div class="placeholder-generic">
                  <span class="placeholder-generic__icon">{{ sectionIcon(section.type) }}</span>
                  <span class="placeholder-generic__label">{{ sectionLabel(section.type) }}</span>
                </div>
              </template>

              <!-- Real data overlay when section has data -->
              <div v-if="section.data?.html" class="section-content__rendered" v-html="section.data.html" />
            </div>
          </div>
        </div>
      </template>

      <!-- Final drop zone (after last section) -->
      <div
        v-if="isEdit && sections.length > 0"
        class="drop-zone drop-zone--last"
        :class="{ 'drop-zone--active': activeDropZone === sections.length }"
        @dragover.prevent="onDropZoneDragOver($event, sections.length)"
        @dragleave="onDropZoneDragLeave($event, sections.length)"
        @drop="onDropZoneDrop($event, sections.length)"
      >
        <div class="drop-zone__line" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.report-canvas-wrapper {
  display: flex;
  justify-content: center;
  padding: 1.5rem;
}

/* --- Page --- */

.report-page {
  width: 100%;
  max-width: 816px; /* US Letter width at 96dpi */
  min-height: calc(816px * var(--page-aspect));
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: 3rem 2.5rem;
  position: relative;
}

.report-page--edit {
  padding-top: 1.5rem;
}

/* --- Empty state --- */

.report-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.report-empty__preview {
  text-align: center;
  padding: 4rem;
}

/* --- Rows --- */

.report-row {
  display: flex;
  gap: 1rem;
}

.report-row--two-col > .report-section {
  flex: 1;
  min-width: 0;
}

/* --- Sections --- */

.report-section {
  position: relative;
  border-radius: var(--radius);
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
}

.report-section--edit {
  border: 1px dashed transparent;
  padding: 0.25rem;
  cursor: grab;
}

.report-section--edit:hover {
  border-color: var(--color-primary-border);
  background: var(--color-primary-lighter);
}

.report-section--dragging {
  opacity: 0.4;
}

/* --- Section toolbar --- */

.section-toolbar {
  display: none;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.5rem;
  margin-bottom: 0.25rem;
  border-radius: var(--radius-sm);
  background: var(--color-tint);
  font-size: 0.6875rem;
  color: var(--color-text-muted);
}

.report-section--edit:hover .section-toolbar {
  display: flex;
}

.section-toolbar__type {
  font-weight: 500;
  color: var(--color-text-secondary);
  flex: 1;
}

.section-toolbar__actions {
  display: flex;
  gap: 0.125rem;
}

.section-toolbar__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.section-toolbar__btn:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.section-toolbar__btn--danger:hover {
  background: var(--color-error-light);
  color: var(--color-error);
}

.section-toolbar__drag {
  cursor: grab;
}

/* --- Drop zones --- */

.drop-zone {
  position: relative;
  height: 8px;
  margin: 0.25rem 0;
  transition: height 0.15s ease;
}

.drop-zone--empty {
  height: auto;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  transition: border-color 0.2s, background 0.2s;
}

.drop-zone--empty.drop-zone--active {
  border-color: var(--color-primary);
  background: var(--color-primary-lighter);
}

.drop-zone__indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  color: var(--color-text-muted);
}

.drop-zone__icon {
  width: 32px;
  height: 32px;
  opacity: 0.4;
}

.drop-zone__label {
  font-size: 0.8125rem;
}

.drop-zone__line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: transparent;
  border-radius: 1px;
  transform: translateY(-50%);
  transition: background 0.15s;
}

.drop-zone--active {
  height: 16px;
}

.drop-zone--active .drop-zone__line {
  background: var(--color-primary);
}

/* --- Section content --- */

.section-content {
  padding: 0.75rem;
  min-height: 40px;
  position: relative;
}

.section-content__rendered {
  position: absolute;
  inset: 0;
  padding: 0.75rem;
  background: var(--color-surface);
  border-radius: var(--radius);
}

/* --- Placeholders --- */

.placeholder-line {
  height: 10px;
  background: var(--color-tint);
  border-radius: 4px;
  margin-bottom: 6px;
}

.placeholder-line--sm {
  height: 8px;
}

.placeholder-line--lg {
  height: 16px;
}

.placeholder-heading {
  padding: 0.5rem 0;
}

.placeholder-paragraph {
  padding: 0.25rem 0;
}

.placeholder-callout {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  border-left: 3px solid var(--color-primary);
  background: var(--color-primary-lighter);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.placeholder-callout__icon {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
}

.placeholder-lines {
  flex: 1;
}

.placeholder-chart {
  padding: 0.25rem 0;
}

.placeholder-chart__title {
  margin-bottom: 0.5rem;
}

.placeholder-chart__area {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-tint);
  border-radius: var(--radius-sm);
}

.placeholder-chart__svg {
  width: 100%;
  height: 100%;
}

.placeholder-table__header {
  display: flex;
  gap: 1rem;
  padding: 0.5rem 0;
  border-bottom: 2px solid var(--color-border-strong);
  margin-bottom: 0.375rem;
}

.placeholder-table__row {
  display: flex;
  gap: 1rem;
  padding: 0.375rem 0;
  border-bottom: 1px solid var(--color-border);
}

.placeholder-metrics {
  display: flex;
  gap: 0.75rem;
}

.placeholder-metric-card {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.placeholder-divider {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 1rem 0;
}

.placeholder-spacer {
  height: 2rem;
}

.placeholder-generic {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1.5rem;
  color: var(--color-text-muted);
  font-size: 0.8125rem;
}

.placeholder-generic__icon {
  font-size: 1.25rem;
  opacity: 0.5;
}
</style>
