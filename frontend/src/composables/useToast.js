import { ref } from 'vue'

const toasts = ref([])
let nextId = 0
const MAX_TOASTS = 5

const DEFAULTS = {
  success: { duration: 4000 },
  error: { duration: 6000 },
  info: { duration: 4000 },
  warning: { duration: 5000 },
}

export function useToast() {
  function addToast(message, type = 'info', duration) {
    const id = nextId++
    const resolvedDuration = duration ?? DEFAULTS[type]?.duration ?? 4000

    const toast = {
      id,
      message,
      type,
      duration: resolvedDuration,
      createdAt: Date.now(),
      action: null,
    }

    toasts.value.push(toast)

    // Cap at MAX_TOASTS — remove oldest first
    while (toasts.value.length > MAX_TOASTS) {
      toasts.value.shift()
    }

    if (resolvedDuration > 0) {
      setTimeout(() => removeToast(id), resolvedDuration)
    }

    return id
  }

  function removeToast(id) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  function clearAll() {
    toasts.value = []
  }

  function success(message, options = {}) {
    const id = addToast(message, 'success', options.duration)
    if (options.action) {
      const t = toasts.value.find((t) => t.id === id)
      if (t) t.action = options.action
    }
    return id
  }

  function error(message, options = {}) {
    const id = addToast(message, 'error', options.duration)
    if (options.action) {
      const t = toasts.value.find((t) => t.id === id)
      if (t) t.action = options.action
    }
    return id
  }

  function info(message, options = {}) {
    const id = addToast(message, 'info', options.duration)
    if (options.action) {
      const t = toasts.value.find((t) => t.id === id)
      if (t) t.action = options.action
    }
    return id
  }

  function warning(message, options = {}) {
    const id = addToast(message, 'warning', options.duration)
    if (options.action) {
      const t = toasts.value.find((t) => t.id === id)
      if (t) t.action = options.action
    }
    return id
  }

  return { toasts, addToast, removeToast, clearAll, success, error, info, warning }
}
