import { useRegisterSW } from 'virtual:pwa-register/vue'

const UPDATE_CHECK_INTERVAL = 60 * 60 * 1000 // 1 hour

let needRefresh
let offlineReady
let updateServiceWorker
let initialized = false

export function useServiceWorker() {
  if (!initialized) {
    initialized = true
    const sw = useRegisterSW({
      onRegisteredSW(swUrl, registration) {
        if (!registration) return
        setInterval(() => {
          registration.update()
        }, UPDATE_CHECK_INTERVAL)
      },
    })
    needRefresh = sw.needRefresh
    offlineReady = sw.offlineReady
    updateServiceWorker = sw.updateServiceWorker
  }

  function update() {
    updateServiceWorker()
  }

  function dismiss() {
    needRefresh.value = false
    offlineReady.value = false
  }

  return { needRefresh, offlineReady, update, dismiss }
}
