import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])
  let nextId = 0

  function add({ message, type = 'info', duration = 4000 }) {
    const id = nextId++
    toasts.value.push({ id, message, type })
    if (duration > 0) {
      setTimeout(() => remove(id), duration)
    }
    return id
  }

  function remove(id) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  function success(message) {
    return add({ message, type: 'success' })
  }

  function error(message) {
    return add({ message, type: 'error', duration: 6000 })
  }

  function info(message) {
    return add({ message, type: 'info' })
  }

  return { toasts, add, remove, success, error, info }
})
