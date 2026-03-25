import { ref, onUnmounted } from 'vue'

const isOnline = ref(navigator.onLine)
let listenerCount = 0

function handleOnline() {
  isOnline.value = true
}

function handleOffline() {
  isOnline.value = false
}

function startListening() {
  if (listenerCount === 0) {
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
  }
  listenerCount++
}

function stopListening() {
  listenerCount--
  if (listenerCount === 0) {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  }
}

export function useOnlineStatus() {
  startListening()
  onUnmounted(stopListening)
  return { isOnline }
}
