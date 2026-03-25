import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref([])
  let nextId = 0

  const unreadCount = computed(() =>
    notifications.value.filter(n => !n.read).length
  )

  function add({ title, message = '', type = 'info' }) {
    const id = nextId++
    notifications.value.unshift({ id, title, message, type, read: false, timestamp: Date.now() })
    return id
  }

  function markRead(id) {
    const n = notifications.value.find(item => item.id === id)
    if (n) n.read = true
  }

  function markAllRead() {
    notifications.value.forEach(n => { n.read = true })
  }

  function remove(id) {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  function clear() {
    notifications.value = []
  }

  return { notifications, unreadCount, add, markRead, markAllRead, remove, clear }
})
