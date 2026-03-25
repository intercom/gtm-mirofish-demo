import { ref } from 'vue'

const STORAGE_KEY = 'mirofish_dashboard_order'

const customOrder = ref(loadFromStorage())

function loadFromStorage() {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

export function useDashboardLayout() {
  function saveOrder(ids) {
    customOrder.value = ids
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids))
  }

  function clearOrder() {
    customOrder.value = []
    localStorage.removeItem(STORAGE_KEY)
  }

  function applyOrder(items) {
    if (!customOrder.value.length) return items
    const map = new Map(items.map(i => [i.id, i]))
    const ordered = []
    for (const id of customOrder.value) {
      const item = map.get(id)
      if (item) {
        ordered.push(item)
        map.delete(id)
      }
    }
    for (const item of map.values()) {
      ordered.push(item)
    }
    return ordered
  }

  return { customOrder, saveOrder, clearOrder, applyOrder }
}
