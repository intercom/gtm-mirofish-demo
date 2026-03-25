import { ref } from 'vue'

const draggedItem = ref(null)
const dragSource = ref(null)

export function useDragAndDrop() {
  const dragOverTarget = ref(null)

  function onDragStart(item, source, event) {
    draggedItem.value = item
    dragSource.value = source
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', '')
    event.target.classList.add('dragging')
  }

  function onDragEnd(event) {
    event.target.classList.remove('dragging')
    draggedItem.value = null
    dragSource.value = null
    dragOverTarget.value = null
  }

  function onDragOver(targetId, event) {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
    dragOverTarget.value = targetId
  }

  function onDragLeave(targetId) {
    if (dragOverTarget.value === targetId) {
      dragOverTarget.value = null
    }
  }

  function onDrop(targetId, handler, event) {
    event.preventDefault()
    dragOverTarget.value = null
    if (draggedItem.value != null) {
      handler(draggedItem.value, dragSource.value, targetId)
    }
  }

  return {
    draggedItem,
    dragSource,
    dragOverTarget,
    onDragStart,
    onDragEnd,
    onDragOver,
    onDragLeave,
    onDrop,
  }
}
