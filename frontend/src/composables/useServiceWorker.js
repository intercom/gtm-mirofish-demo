import { useRegisterSW } from 'virtual:pwa-register/vue'

const UPDATE_CHECK_INTERVAL = 60 * 60 * 1000 // 1 hour

export function useServiceWorker() {
  const {
    needRefresh,
    offlineReady,
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW(swUrl, registration) {
      if (!registration) return
      setInterval(() => {
        registration.update()
      }, UPDATE_CHECK_INTERVAL)
    },
  })

  function update() {
    updateServiceWorker()
  }

  function dismiss() {
    needRefresh.value = false
    offlineReady.value = false
  }

  return { needRefresh, offlineReady, update, dismiss }
}
