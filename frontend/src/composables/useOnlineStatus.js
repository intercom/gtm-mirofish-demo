import { ref, onMounted, onUnmounted } from 'vue'

const isOnline = ref(navigator.onLine)

function handleOnline() { isOnline.value = true }
function handleOffline() { isOnline.value = false }

let listenerCount = 0

export function useOnlineStatus() {
  onMounted(() => {
    if (listenerCount === 0) {
      window.addEventListener('online', handleOnline)
      window.addEventListener('offline', handleOffline)
    }
    listenerCount++
    isOnline.value = navigator.onLine
  })

  onUnmounted(() => {
    listenerCount--
    if (listenerCount === 0) {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  })

  return { isOnline }
}
