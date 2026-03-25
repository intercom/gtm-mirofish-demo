import { ref } from 'vue'

/**
 * Reusable composable for HTML5 drag-and-drop list reordering.
 * @param {Object} options
 * @param {Function} options.onReorder - Called with (fromIndex, toIndex) on successful drop
 */
export function useDragAndDrop({ onReorder } = {}) {
  const dragIndex = ref(null)
  const dropIndicatorIndex = ref(null)

  function onDragStart(e, index) {
    dragIndex.value = index
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(index))
  }

  function onDragOver(e, index) {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (dragIndex.value === null) return

    const rect = e.currentTarget.getBoundingClientRect()
    const midY = rect.top + rect.height / 2
    const insertAt = e.clientY < midY ? index : index + 1

    // Don't show indicator at the dragged item's current position
    if (insertAt === dragIndex.value || insertAt === dragIndex.value + 1) {
      dropIndicatorIndex.value = null
      return
    }

    dropIndicatorIndex.value = insertAt
  }

  function onDrop(e) {
    e.preventDefault()
    if (dragIndex.value === null || dropIndicatorIndex.value === null) return

    let from = dragIndex.value
    let to = dropIndicatorIndex.value
    // Adjust target since the dragged item is removed before reinserting
    if (from < to) to--

    if (from !== to) {
      onReorder?.(from, to)
    }

    dragIndex.value = null
    dropIndicatorIndex.value = null
  }

  function onDragEnd() {
    dragIndex.value = null
    dropIndicatorIndex.value = null
  }

  return {
    dragIndex,
    dropIndicatorIndex,
    onDragStart,
    onDragOver,
    onDrop,
    onDragEnd,
  }
}
