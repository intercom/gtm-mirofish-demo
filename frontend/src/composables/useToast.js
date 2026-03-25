import { ref } from 'vue'

const toasts = ref([])
let nextId = 0

export function useToast() {
  function addToast(message, type = 'info', duration = 4000) {
    const id = nextId++
    toasts.value.push({ id, message, type, duration })
    if (duration > 0) {
      setTimeout(() => removeToast(id), duration)
    }
  }

  function removeToast(id) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  function success(message, duration) {
    addToast(message, 'success', duration)
  }

  function error(message, duration) {
    addToast(message, 'error', duration)
  }

  function info(message, duration) {
    addToast(message, 'info', duration)
  }

  return { toasts, addToast, removeToast, success, error, info }
}
