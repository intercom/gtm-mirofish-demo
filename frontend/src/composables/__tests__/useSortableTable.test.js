import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useSortableTable } from '../useSortableTable.js'

const sampleRows = () => [
  { id: 1, name: 'Charlie', score: 85 },
  { id: 2, name: 'Alice', score: 92 },
  { id: 3, name: 'Bob', score: 78 },
]

describe('useSortableTable', () => {
  it('returns rows unsorted by default', () => {
    const rows = ref(sampleRows())
    const { sortedRows } = useSortableTable(rows)
    expect(sortedRows.value.map(r => r.id)).toEqual([1, 2, 3])
  })

  it('sorts strings ascending', () => {
    const rows = ref(sampleRows())
    const { sortedRows, toggleSort } = useSortableTable(rows)
    toggleSort('name')
    expect(sortedRows.value.map(r => r.name)).toEqual(['Alice', 'Bob', 'Charlie'])
  })

  it('sorts strings descending on second toggle', () => {
    const rows = ref(sampleRows())
    const { sortedRows, toggleSort } = useSortableTable(rows)
    toggleSort('name')
    toggleSort('name')
    expect(sortedRows.value.map(r => r.name)).toEqual(['Charlie', 'Bob', 'Alice'])
  })

  it('sorts numbers ascending', () => {
    const rows = ref(sampleRows())
    const { sortedRows, toggleSort } = useSortableTable(rows)
    toggleSort('score')
    expect(sortedRows.value.map(r => r.score)).toEqual([78, 85, 92])
  })

  it('sorts numbers descending', () => {
    const rows = ref(sampleRows())
    const { sortedRows, toggleSort } = useSortableTable(rows)
    toggleSort('score')
    toggleSort('score')
    expect(sortedRows.value.map(r => r.score)).toEqual([92, 85, 78])
  })

  it('switches column resets direction to asc', () => {
    const rows = ref(sampleRows())
    const { sortedRows, toggleSort, sortDirection } = useSortableTable(rows)
    toggleSort('name')
    toggleSort('name')
    expect(sortDirection.value).toBe('desc')
    toggleSort('score')
    expect(sortDirection.value).toBe('asc')
    expect(sortedRows.value.map(r => r.score)).toEqual([78, 85, 92])
  })

  it('clearSort resets to original order', () => {
    const rows = ref(sampleRows())
    const { sortedRows, toggleSort, clearSort, sortColumn } = useSortableTable(rows)
    toggleSort('name')
    clearSort()
    expect(sortColumn.value).toBeNull()
    expect(sortedRows.value.map(r => r.id)).toEqual([1, 2, 3])
  })

  it('reorder moves item and clears sort', () => {
    const rows = ref(sampleRows())
    const { toggleSort, reorder, sortColumn } = useSortableTable(rows)
    toggleSort('name')
    const result = reorder(0, 2)
    expect(result).not.toBeNull()
    expect(result.map(r => r.id)).toEqual([2, 3, 1])
    expect(sortColumn.value).toBeNull()
  })

  it('reorder returns null for same index', () => {
    const rows = ref(sampleRows())
    const { reorder } = useSortableTable(rows)
    expect(reorder(1, 1)).toBeNull()
  })

  it('handles null values in sort', () => {
    const rows = ref([
      { id: 1, name: 'Bob' },
      { id: 2, name: null },
      { id: 3, name: 'Alice' },
    ])
    const { sortedRows, toggleSort } = useSortableTable(rows)
    toggleSort('name')
    expect(sortedRows.value.map(r => r.id)).toEqual([3, 1, 2])
  })

  it('accepts defaultSort option', () => {
    const rows = ref(sampleRows())
    const { sortedRows, sortColumn, sortDirection } = useSortableTable(rows, {
      defaultSort: { column: 'score', direction: 'desc' },
    })
    expect(sortColumn.value).toBe('score')
    expect(sortDirection.value).toBe('desc')
    expect(sortedRows.value.map(r => r.score)).toEqual([92, 85, 78])
  })
})
