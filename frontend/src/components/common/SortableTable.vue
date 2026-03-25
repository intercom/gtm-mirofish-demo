<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  columns: {
    type: Array,
    required: true,
  },
  rows: {
    type: Array,
    required: true,
  },
  rowKey: {
    type: String,
    default: 'id',
  },
  draggable: {
    type: Boolean,
    default: false,
  },
  striped: {
    type: Boolean,
    default: false,
  },
  emptyText: {
    type: String,
    default: 'No data',
  },
})

const emit = defineEmits(['sort', 'reorder'])

const sortColumn = ref(null)
const sortDirection = ref('asc')
const dragFromIndex = ref(null)
const dragOverIndex = ref(null)

const sortedRows = computed(() => {
  const data = [...props.rows]
  if (!sortColumn.value) return data

  const key = sortColumn.value
  const dir = sortDirection.value === 'asc' ? 1 : -1

  return data.sort((a, b) => {
    const aVal = a[key]
    const bVal = b[key]
    if (aVal == null && bVal == null) return 0
    if (aVal == null) return 1
    if (bVal == null) return -1
    if (typeof aVal === 'number' && typeof bVal === 'number') return (aVal - bVal) * dir
    return String(aVal).localeCompare(String(bVal)) * dir
  })
})

function toggleSort(col) {
  if (!col.sortable) return
  if (sortColumn.value === col.key) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = col.key
    sortDirection.value = 'asc'
  }
  emit('sort', { column: sortColumn.value, direction: sortDirection.value })
}

function onDragStart(e, index) {
  dragFromIndex.value = index
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(index))
}

function onDragEnd() {
  dragFromIndex.value = null
  dragOverIndex.value = null
}

function onDragOver(e, index) {
  e.preventDefault()
  e.dataTransfer.dropEffect = 'move'
  dragOverIndex.value = index
}

function onDragLeave(e, index) {
  if (dragOverIndex.value === index) dragOverIndex.value = null
}

function onDrop(e, toIndex) {
  e.preventDefault()
  const fromIndex = dragFromIndex.value
  if (fromIndex == null || fromIndex === toIndex) {
    dragFromIndex.value = null
    dragOverIndex.value = null
    return
  }

  sortColumn.value = null
  sortDirection.value = 'asc'

  const reordered = [...props.rows]
  const [moved] = reordered.splice(fromIndex, 1)
  reordered.splice(toIndex, 0, moved)
  emit('reorder', reordered)

  dragFromIndex.value = null
  dragOverIndex.value = null
}

const totalCols = computed(() => props.columns.length + (props.draggable ? 1 : 0))
</script>

<template>
  <div class="overflow-x-auto rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-[var(--color-border)]">
          <th v-if="draggable" class="w-10 px-2 py-3 bg-[var(--color-tint)]" />
          <th
            v-for="col in columns"
            :key="col.key"
            :style="col.width ? { width: col.width } : {}"
            :class="[
              'px-4 py-3 text-xs font-semibold tracking-wide uppercase bg-[var(--color-tint)]',
              'text-[var(--color-text-muted)]',
              col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
              col.sortable && 'cursor-pointer select-none hover:text-[var(--color-text)] transition-colors',
            ]"
            @click="toggleSort(col)"
          >
            <span class="inline-flex items-center gap-1">
              <slot :name="`header-${col.key}`" :column="col">
                {{ col.label }}
              </slot>
              <svg
                v-if="col.sortable && sortColumn === col.key"
                class="w-3.5 h-3.5 transition-transform"
                :class="sortDirection === 'desc' && 'rotate-180'"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 15.75l7.5-7.5 7.5 7.5" />
              </svg>
              <svg
                v-else-if="col.sortable"
                class="w-3.5 h-3.5 opacity-30"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 15L12 18.75 15.75 15m-7.5-6L12 5.25 15.75 9" />
              </svg>
            </span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="sortedRows.length === 0">
          <td
            :colspan="totalCols"
            class="px-4 py-12 text-center text-sm text-[var(--color-text-muted)]"
          >
            {{ emptyText }}
          </td>
        </tr>
        <tr
          v-for="(row, index) in sortedRows"
          :key="row[rowKey] ?? index"
          :draggable="draggable"
          :class="[
            'border-b border-[var(--color-border)] last:border-b-0',
            'transition-[background-color,opacity] duration-150',
            striped && index % 2 === 1 && 'bg-[var(--color-tint)]',
            dragFromIndex === index && 'opacity-40',
            dragOverIndex === index && dragFromIndex !== index && 'bg-[var(--color-primary-light)]',
          ]"
          @dragstart="draggable && onDragStart($event, index)"
          @dragend="draggable && onDragEnd()"
          @dragover="draggable && onDragOver($event, index)"
          @dragleave="draggable && onDragLeave($event, index)"
          @drop="draggable && onDrop($event, index)"
        >
          <td
            v-if="draggable"
            class="w-10 px-2 py-3 text-center text-[var(--color-text-muted)] cursor-grab active:cursor-grabbing"
          >
            <svg class="w-4 h-4 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 9h16.5m-16.5 6.75h16.5" />
            </svg>
          </td>
          <td
            v-for="col in columns"
            :key="col.key"
            :class="[
              'px-4 py-3 text-[var(--color-text)]',
              col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
            ]"
          >
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]" :index="index">
              {{ row[col.key] ?? '—' }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
