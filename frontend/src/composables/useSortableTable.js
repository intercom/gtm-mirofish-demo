import { ref, computed, toValue } from 'vue'

export function useSortableTable(rowsRef, options = {}) {
  const sortColumn = ref(options.defaultSort?.column ?? null)
  const sortDirection = ref(options.defaultSort?.direction ?? 'asc')
  const dragFromIndex = ref(null)
  const dragOverIndex = ref(null)

  const sortedRows = computed(() => {
    const data = [...toValue(rowsRef)]
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

  function toggleSort(column) {
    if (sortColumn.value === column) {
      sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortColumn.value = column
      sortDirection.value = 'asc'
    }
  }

  function clearSort() {
    sortColumn.value = null
    sortDirection.value = 'asc'
  }

  function reorder(fromIndex, toIndex) {
    if (fromIndex === toIndex) return null
    const data = [...toValue(rowsRef)]
    const [moved] = data.splice(fromIndex, 1)
    data.splice(toIndex, 0, moved)
    clearSort()
    return data
  }

  return {
    sortColumn,
    sortDirection,
    sortedRows,
    dragFromIndex,
    dragOverIndex,
    toggleSort,
    clearSort,
    reorder,
  }
}
