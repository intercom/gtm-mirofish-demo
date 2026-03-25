import { ref, shallowRef, watch, unref, onUnmounted } from 'vue'

// Shared drag payload — lets useDropTarget validate types during dragover
// (dataTransfer data isn't readable in dragover on some browsers)
const activeDrag = shallowRef(null)

// Watch a template ref or plain element, bind setup logic, auto-cleanup
function bindElement(elRef, setupFn) {
  let cleanup = null
  const stop = watch(
    () => unref(elRef),
    (el) => {
      if (cleanup) { cleanup(); cleanup = null }
      if (el) cleanup = setupFn(el)
    },
    { immediate: true, flush: 'post' },
  )
  onUnmounted(() => {
    stop()
    if (cleanup) cleanup()
  })
}

/**
 * Make an element a drag source.
 * @param {Ref<HTMLElement>|HTMLElement} elRef - Template ref or element
 * @param {Ref|*} data - Data payload to transfer
 * @param {{ type?: string }} options
 */
export function useDragSource(elRef, data, options = {}) {
  const isDragging = ref(false)
  const type = options.type || 'default'

  bindElement(elRef, (el) => {
    el.draggable = true
    let clone = null

    function startDrag() {
      isDragging.value = true
      el.style.opacity = '0.4'
      activeDrag.value = { type, data: unref(data) }
    }

    function endDrag() {
      isDragging.value = false
      el.style.opacity = ''
      activeDrag.value = null
    }

    // --- HTML5 Drag & Drop ---
    function onDragStart(e) {
      startDrag()
      e.dataTransfer.setData('application/json', JSON.stringify(activeDrag.value))
      e.dataTransfer.effectAllowed = 'move'
    }

    function onDragEnd() { endDrag() }

    // --- Touch fallback ---
    let offsetX = 0, offsetY = 0

    function onTouchStart(e) {
      if (e.touches.length !== 1) return
      const touch = e.touches[0]
      const rect = el.getBoundingClientRect()
      offsetX = touch.clientX - rect.left
      offsetY = touch.clientY - rect.top
      startDrag()

      clone = el.cloneNode(true)
      Object.assign(clone.style, {
        position: 'fixed', pointerEvents: 'none', zIndex: '9999',
        opacity: '0.8', width: rect.width + 'px',
        left: rect.left + 'px', top: rect.top + 'px',
      })
      document.body.appendChild(clone)
      e.preventDefault()
    }

    function onTouchMove(e) {
      if (!clone) return
      const touch = e.touches[0]
      clone.style.left = (touch.clientX - offsetX) + 'px'
      clone.style.top = (touch.clientY - offsetY) + 'px'

      clone.style.display = 'none'
      const target = document.elementFromPoint(touch.clientX, touch.clientY)
      clone.style.display = ''
      if (target) target.dispatchEvent(new CustomEvent('touchdragover', { bubbles: true }))
      e.preventDefault()
    }

    function onTouchEnd(e) {
      if (!clone) return
      const touch = e.changedTouches[0]
      clone.style.display = 'none'
      const target = document.elementFromPoint(touch.clientX, touch.clientY)
      clone.remove()
      clone = null
      if (target) {
        target.dispatchEvent(new CustomEvent('touchdrop', { bubbles: true, detail: activeDrag.value }))
      }
      endDrag()
    }

    el.addEventListener('dragstart', onDragStart)
    el.addEventListener('dragend', onDragEnd)
    el.addEventListener('touchstart', onTouchStart, { passive: false })
    el.addEventListener('touchmove', onTouchMove, { passive: false })
    el.addEventListener('touchend', onTouchEnd)

    return () => {
      el.removeEventListener('dragstart', onDragStart)
      el.removeEventListener('dragend', onDragEnd)
      el.removeEventListener('touchstart', onTouchStart)
      el.removeEventListener('touchmove', onTouchMove)
      el.removeEventListener('touchend', onTouchEnd)
      el.draggable = false
      if (clone) { clone.remove(); clone = null }
      if (isDragging.value) endDrag()
    }
  })

  return { isDragging }
}

/**
 * Make an element a drop target.
 * @param {Ref<HTMLElement>|HTMLElement} elRef - Template ref or element
 * @param {(data: *, event: Event) => void} onDrop - Drop handler
 * @param {{ acceptTypes?: string[] }} options
 */
export function useDropTarget(elRef, onDrop, options = {}) {
  const isOver = ref(false)
  const acceptTypes = options.acceptTypes || null

  function accepts(payload) {
    return !acceptTypes || acceptTypes.includes(payload?.type)
  }

  bindElement(elRef, (el) => {
    let touchTimer = null

    function highlight() {
      isOver.value = true
      el.style.outline = '2px dashed #2068FF'
      el.style.outlineOffset = '-2px'
    }

    function unhighlight() {
      isOver.value = false
      el.style.outline = ''
      el.style.outlineOffset = ''
    }

    function onDragOver(e) {
      if (activeDrag.value && !accepts(activeDrag.value)) return
      e.preventDefault()
      e.dataTransfer.dropEffect = 'move'
      highlight()
    }

    function onDragLeave(e) {
      if (el.contains(e.relatedTarget)) return
      unhighlight()
    }

    function onDropHandler(e) {
      e.preventDefault()
      unhighlight()
      try {
        const payload = JSON.parse(e.dataTransfer.getData('application/json'))
        if (accepts(payload)) onDrop(payload.data, e)
      } catch { /* invalid payload */ }
    }

    function onTouchDragOver() {
      if (activeDrag.value && !accepts(activeDrag.value)) return
      highlight()
      clearTimeout(touchTimer)
      touchTimer = setTimeout(unhighlight, 150)
    }

    function onTouchDropHandler(e) {
      clearTimeout(touchTimer)
      unhighlight()
      const payload = e.detail
      if (payload && accepts(payload)) onDrop(payload.data, e)
    }

    el.addEventListener('dragover', onDragOver)
    el.addEventListener('dragleave', onDragLeave)
    el.addEventListener('drop', onDropHandler)
    el.addEventListener('touchdragover', onTouchDragOver)
    el.addEventListener('touchdrop', onTouchDropHandler)

    return () => {
      el.removeEventListener('dragover', onDragOver)
      el.removeEventListener('dragleave', onDragLeave)
      el.removeEventListener('drop', onDropHandler)
      el.removeEventListener('touchdragover', onTouchDragOver)
      el.removeEventListener('touchdrop', onTouchDropHandler)
      clearTimeout(touchTimer)
      unhighlight()
    }
  })

  return { isOver }
}

/**
 * Sortable list with drag reordering.
 * @param {Ref<Array>} list - Reactive array (used by consumer in v-for)
 * @param {(fromIndex: number, toIndex: number) => void} onReorder - Reorder callback
 */
export function useSortable(list, onReorder) {
  const dragIndex = ref(-1)
  const overIndex = ref(-1)
  let touchState = null

  function findSortableIndex(el) {
    while (el) {
      if (el.dataset?.sortableIndex != null) return parseInt(el.dataset.sortableIndex, 10)
      el = el.parentElement
    }
    return -1
  }

  function onTouchMove(e) {
    if (!touchState) return
    const touch = e.touches[0]
    const { clone, offsetX, offsetY } = touchState
    clone.style.left = (touch.clientX - offsetX) + 'px'
    clone.style.top = (touch.clientY - offsetY) + 'px'

    clone.style.display = 'none'
    const target = document.elementFromPoint(touch.clientX, touch.clientY)
    clone.style.display = ''
    overIndex.value = findSortableIndex(target)
    e.preventDefault()
  }

  function onTouchEnd() {
    if (!touchState) return
    touchState.clone.remove()
    touchState.sourceEl.style.opacity = ''
    touchState = null

    const from = dragIndex.value
    const to = overIndex.value
    dragIndex.value = -1
    overIndex.value = -1
    if (from !== -1 && to !== -1 && from !== to) onReorder(from, to)

    document.removeEventListener('touchmove', onTouchMove)
    document.removeEventListener('touchend', onTouchEnd)
  }

  function getItemProps(index) {
    return {
      draggable: true,
      'data-sortable-index': index,
      onDragstart(e) {
        dragIndex.value = index
        e.dataTransfer.effectAllowed = 'move'
        e.dataTransfer.setData('text/plain', String(index))
        e.currentTarget.style.opacity = '0.4'
      },
      onDragover(e) {
        e.preventDefault()
        e.dataTransfer.dropEffect = 'move'
        overIndex.value = index
      },
      onDragleave() {
        if (overIndex.value === index) overIndex.value = -1
      },
      onDrop(e) {
        e.preventDefault()
        const from = dragIndex.value
        overIndex.value = -1
        dragIndex.value = -1
        if (from !== -1 && from !== index) onReorder(from, index)
      },
      onDragend(e) {
        e.currentTarget.style.opacity = ''
        dragIndex.value = -1
        overIndex.value = -1
      },
      onTouchstart(e) {
        if (e.touches.length !== 1) return
        e.preventDefault()
        const el = e.currentTarget
        const touch = e.touches[0]
        const rect = el.getBoundingClientRect()

        dragIndex.value = index
        el.style.opacity = '0.4'

        const clone = el.cloneNode(true)
        Object.assign(clone.style, {
          position: 'fixed', pointerEvents: 'none', zIndex: '9999',
          opacity: '0.8', width: rect.width + 'px',
          left: rect.left + 'px', top: rect.top + 'px',
        })
        document.body.appendChild(clone)

        touchState = {
          clone, sourceEl: el,
          offsetX: touch.clientX - rect.left,
          offsetY: touch.clientY - rect.top,
        }
        document.addEventListener('touchmove', onTouchMove, { passive: false })
        document.addEventListener('touchend', onTouchEnd)
      },
    }
  }

  onUnmounted(() => {
    if (touchState) {
      touchState.clone.remove()
      document.removeEventListener('touchmove', onTouchMove)
      document.removeEventListener('touchend', onTouchEnd)
      touchState = null
    }
  })

  return { dragIndex, overIndex, getItemProps }
}
