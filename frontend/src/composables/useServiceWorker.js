import { ref, readonly } from 'vue'

const isSupported = ref('serviceWorker' in navigator)
const isReady = ref(false)
const hasUpdate = ref(false)
const registration = ref(null)

let registered = false

export function useServiceWorker() {
  async function register() {
    if (registered || !isSupported.value) return

    registered = true
    try {
      const reg = await navigator.serviceWorker.register('/sw.js')
      registration.value = reg

      reg.addEventListener('updatefound', () => {
        const newWorker = reg.installing
        if (!newWorker) return
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'activated' && navigator.serviceWorker.controller) {
            hasUpdate.value = true
          }
        })
      })

      if (reg.active) isReady.value = true
      navigator.serviceWorker.ready.then(() => {
        isReady.value = true
      })
    } catch (err) {
      console.warn('Service worker registration failed:', err)
    }
  }

  function update() {
    registration.value?.update()
  }

  function applyUpdate() {
    window.location.reload()
  }

  return {
    isSupported: readonly(isSupported),
    isReady: readonly(isReady),
    hasUpdate: readonly(hasUpdate),
    register,
    update,
    applyUpdate,
  }
}
