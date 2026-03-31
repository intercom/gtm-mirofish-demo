import { describe, it, expect, vi } from 'vitest'
import { useListReorder as useDragAndDrop } from '../useDragAndDrop.js'

function makeDragEvent(overrides = {}) {
  return {
    preventDefault: vi.fn(),
    dataTransfer: { effectAllowed: '', dropEffect: '', setData: vi.fn() },
    currentTarget: {
      getBoundingClientRect: () => ({ top: 0, height: 100 }),
    },
    clientY: 50,
    ...overrides,
  }
}

describe('useDragAndDrop', () => {
  it('sets dragIndex on dragStart', () => {
    const { dragIndex, onDragStart } = useDragAndDrop()
    const e = makeDragEvent()

    onDragStart(e, 2)

    expect(dragIndex.value).toBe(2)
    expect(e.dataTransfer.effectAllowed).toBe('move')
    expect(e.dataTransfer.setData).toHaveBeenCalledWith('text/plain', '2')
  })

  it('computes dropIndicatorIndex from cursor position (top half)', () => {
    const { dragIndex, dropIndicatorIndex, onDragStart, onDragOver } = useDragAndDrop()

    onDragStart(makeDragEvent(), 0)

    // Cursor in top half of item at index 2 → indicator at index 2
    const e = makeDragEvent({
      clientY: 20,
      currentTarget: { getBoundingClientRect: () => ({ top: 0, height: 100 }) },
    })
    onDragOver(e, 2)

    expect(dropIndicatorIndex.value).toBe(2)
    expect(e.preventDefault).toHaveBeenCalled()
  })

  it('computes dropIndicatorIndex from cursor position (bottom half)', () => {
    const { onDragStart, dropIndicatorIndex, onDragOver } = useDragAndDrop()

    onDragStart(makeDragEvent(), 0)

    // Cursor in bottom half of item at index 2 → indicator at index 3
    const e = makeDragEvent({
      clientY: 80,
      currentTarget: { getBoundingClientRect: () => ({ top: 0, height: 100 }) },
    })
    onDragOver(e, 2)

    expect(dropIndicatorIndex.value).toBe(3)
  })

  it('hides indicator when hovering own position', () => {
    const { onDragStart, dropIndicatorIndex, onDragOver } = useDragAndDrop()

    onDragStart(makeDragEvent(), 1)

    // Top half of index 1 → insertAt=1, which equals dragIndex → null
    const e = makeDragEvent({
      clientY: 20,
      currentTarget: { getBoundingClientRect: () => ({ top: 0, height: 100 }) },
    })
    onDragOver(e, 1)

    expect(dropIndicatorIndex.value).toBe(null)
  })

  it('hides indicator when hovering position directly after own', () => {
    const { onDragStart, dropIndicatorIndex, onDragOver } = useDragAndDrop()

    onDragStart(makeDragEvent(), 1)

    // Bottom half of index 1 → insertAt=2, which equals dragIndex+1 → null
    const e = makeDragEvent({
      clientY: 80,
      currentTarget: { getBoundingClientRect: () => ({ top: 0, height: 100 }) },
    })
    onDragOver(e, 1)

    expect(dropIndicatorIndex.value).toBe(null)
  })

  it('calls onReorder with adjusted indices on drop', () => {
    const onReorder = vi.fn()
    const { onDragStart, onDragOver, onDrop } = useDragAndDrop({ onReorder })

    // Drag item 0 to after item 2
    onDragStart(makeDragEvent(), 0)
    onDragOver(makeDragEvent({
      clientY: 80,
      currentTarget: { getBoundingClientRect: () => ({ top: 0, height: 100 }) },
    }), 2)
    onDrop(makeDragEvent())

    // dropIndicatorIndex was 3, adjusted by -1 for removal = 2
    expect(onReorder).toHaveBeenCalledWith(0, 2)
  })

  it('does not call onReorder when dropped at same position', () => {
    const onReorder = vi.fn()
    const { dragIndex, dropIndicatorIndex, onDrop } = useDragAndDrop({ onReorder })

    // Manually set invalid state (both null)
    onDrop(makeDragEvent())

    expect(onReorder).not.toHaveBeenCalled()
  })

  it('clears state on dragEnd', () => {
    const { dragIndex, dropIndicatorIndex, onDragStart, onDragOver, onDragEnd } = useDragAndDrop()

    onDragStart(makeDragEvent(), 1)
    onDragOver(makeDragEvent({
      clientY: 80,
      currentTarget: { getBoundingClientRect: () => ({ top: 0, height: 100 }) },
    }), 3)

    expect(dragIndex.value).toBe(1)
    expect(dropIndicatorIndex.value).toBe(4)

    onDragEnd()

    expect(dragIndex.value).toBe(null)
    expect(dropIndicatorIndex.value).toBe(null)
  })

  it('adjusts target index correctly when dragging backward', () => {
    const onReorder = vi.fn()
    const { onDragStart, onDragOver, onDrop } = useDragAndDrop({ onReorder })

    // Drag item 3 to before item 1
    onDragStart(makeDragEvent(), 3)
    onDragOver(makeDragEvent({
      clientY: 20,
      currentTarget: { getBoundingClientRect: () => ({ top: 0, height: 100 }) },
    }), 1)
    onDrop(makeDragEvent())

    // dropIndicatorIndex=1, from=3 (3 > 1 so no adjustment) → reorder(3, 1)
    expect(onReorder).toHaveBeenCalledWith(3, 1)
  })
})
