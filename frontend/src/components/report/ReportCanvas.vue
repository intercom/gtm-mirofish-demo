<script setup>
import { computed } from 'vue'
import { useListReorder } from '../../composables/useDragAndDrop'

const props = defineProps({
  sections: { type: Array, required: true },
})

const emit = defineEmits(['reorder'])

const chapters = computed(() =>
  props.sections.map((s) => {
    const titleMatch = s.content.match(/^##\s+(.+)/m)
    const plainText = s.content
      .replace(/^#+\s+.+/gm, '')
      .replace(/[*_~`]/g, '')
      .trim()
    return {
      title: titleMatch ? titleMatch[1] : `Section ${s.section_index}`,
      preview: plainText.slice(0, 120) + (plainText.length > 120 ? '…' : ''),
    }
  })
)

const { dragIndex, dropIndicatorIndex, onDragStart, onDragOver, onDrop, onDragEnd } =
  useListReorder({
    onReorder: (from, to) => emit('reorder', from, to),
  })
</script>

<template>
  <div
    class="report-canvas"
    @dragover.prevent
    @drop="onDrop($event)"
  >
    <p class="text-xs text-[var(--color-text-muted)] mb-3">
      Drag sections to reorder your report
    </p>

    <div class="flex flex-col gap-1.5">
      <template v-for="(chapter, i) in chapters" :key="'sec-' + i">
        <!-- Drop indicator line (before this card) -->
        <div v-if="dropIndicatorIndex === i" class="drop-indicator">
          <div class="drop-indicator-line" />
        </div>

        <!-- Section card -->
        <div
          class="section-card"
          :class="{ 'is-dragging': dragIndex === i }"
          draggable="true"
          @dragstart="onDragStart($event, i)"
          @dragover="onDragOver($event, i)"
          @dragend="onDragEnd"
        >
          <!-- Drag handle (6-dot grip) -->
          <div class="drag-handle" @mousedown.stop>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <circle cx="5" cy="3" r="1.5" />
              <circle cx="11" cy="3" r="1.5" />
              <circle cx="5" cy="8" r="1.5" />
              <circle cx="11" cy="8" r="1.5" />
              <circle cx="5" cy="13" r="1.5" />
              <circle cx="11" cy="13" r="1.5" />
            </svg>
          </div>

          <!-- Section number badge -->
          <span class="section-number">{{ i + 1 }}</span>

          <!-- Title + preview -->
          <div class="section-meta">
            <span class="section-title">{{ chapter.title }}</span>
            <span class="section-preview">{{ chapter.preview }}</span>
          </div>
        </div>
      </template>

      <!-- Drop indicator at end of list -->
      <div v-if="dropIndicatorIndex === chapters.length" class="drop-indicator">
        <div class="drop-indicator-line" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  cursor: default;
  transition: opacity 0.2s, box-shadow 0.2s, transform 0.2s;
  user-select: none;
}

.section-card:hover {
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.section-card.is-dragging {
  opacity: 0.35;
  transform: scale(0.98);
}

.drag-handle {
  flex-shrink: 0;
  color: var(--color-text-muted);
  cursor: grab;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: color 0.15s, background 0.15s;
}

.drag-handle:hover {
  color: var(--color-text-secondary);
  background: var(--color-tint);
}

.drag-handle:active {
  cursor: grabbing;
}

.section-number {
  flex-shrink: 0;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 9999px;
  background: rgba(32, 104, 255, 0.08);
  color: #2068FF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
}

.section-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.section-preview {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 0.125rem;
}

.drop-indicator {
  padding: 0.125rem 0;
}

.drop-indicator-line {
  height: 2px;
  background: #2068FF;
  border-radius: 1px;
  position: relative;
}

.drop-indicator-line::before,
.drop-indicator-line::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 6px;
  height: 6px;
  background: #2068FF;
  border-radius: 50%;
  transform: translateY(-50%);
}

.drop-indicator-line::before { left: -3px; }
.drop-indicator-line::after { right: -3px; }
</style>
