import { ref } from 'vue'

const DISMISS_KEY = 'mirofish-pwa-dismiss'

const deferredPrompt = ref(null)
const canInstall = ref(false)
const isInstalled = ref(false)
const wasDismissed = ref(false)

let initialized = false

export function usePwaInstall() {
  if (!initialized) {
    initialized = true

    isInstalled.value =
      window.matchMedia('(display-mode: standalone)').matches ||
      navigator.standalone === true

    wasDismissed.value = localStorage.getItem(DISMISS_KEY) === 'true'

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      deferredPrompt.value = e
      canInstall.value = true
    })

    window.addEventListener('appinstalled', () => {
      deferredPrompt.value = null
      canInstall.value = false
      isInstalled.value = true
    })
  }

  async function promptInstall() {
    if (!deferredPrompt.value) return false
    deferredPrompt.value.prompt()
    const { outcome } = await deferredPrompt.value.userChoice
    deferredPrompt.value = null
    canInstall.value = false
    return outcome === 'accepted'
  }

  function dismiss() {
    wasDismissed.value = true
    localStorage.setItem(DISMISS_KEY, 'true')
  }

  const showPrompt = ref(false)
  // Reactive: show when installable, not already installed, and not dismissed
  const shouldShow = () => canInstall.value && !isInstalled.value && !wasDismissed.value

  return { canInstall, isInstalled, wasDismissed, showPrompt, shouldShow, promptInstall, dismiss }
}
