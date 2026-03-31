import { ref, computed } from 'vue'

const DISMISS_KEY = 'mirofish-pwa-dismiss'
const DISMISS_EXPIRY_DAYS = 7

const deferredPrompt = ref(null)
const canInstall = ref(false)
const isInstalled = ref(false)

let initialized = false

function isIos() {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream
}

function isInStandaloneMode() {
  return window.matchMedia('(display-mode: standalone)').matches ||
    navigator.standalone === true
}

function getDismissedAt() {
  const raw = localStorage.getItem(DISMISS_KEY)
  if (!raw) return null
  const ts = Number(raw)
  if (Number.isNaN(ts)) {
    // Legacy boolean value — treat as expired
    localStorage.removeItem(DISMISS_KEY)
    return null
  }
  return ts
}

function isDismissExpired() {
  const dismissedAt = getDismissedAt()
  if (!dismissedAt) return true
  const expiryMs = DISMISS_EXPIRY_DAYS * 24 * 60 * 60 * 1000
  return Date.now() - dismissedAt > expiryMs
}

export function usePwaInstall() {
  const wasDismissed = ref(false)
  const isIosDevice = ref(false)

  if (!initialized) {
    initialized = true

    isInstalled.value = isInStandaloneMode()
    isIosDevice.value = isIos()
    wasDismissed.value = !isDismissExpired()

    // Chrome/Edge/Android — standard install prompt
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
  } else {
    isIosDevice.value = isIos()
    wasDismissed.value = !isDismissExpired()
  }

  const showPrompt = computed(() =>
    !isInstalled.value &&
    !wasDismissed.value &&
    (canInstall.value || isIosDevice.value),
  )

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
    localStorage.setItem(DISMISS_KEY, String(Date.now()))
  }

  return { canInstall, isInstalled, isIosDevice, wasDismissed, showPrompt, promptInstall, dismiss }
}
