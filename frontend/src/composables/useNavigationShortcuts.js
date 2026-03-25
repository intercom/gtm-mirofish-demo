import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const SHORTCUT_TIMEOUT_MS = 500

const NAV_SHORTCUTS = {
  d: { path: '/simulations', label: 'Dashboard' },
  s: { path: '/simulations', label: 'Simulations' },
  t: { path: '/', label: 'Scenario Templates' },
  e: { path: '/settings', label: 'Settings' },
  h: { path: '/', label: 'Home' },
}

const isGMode = ref(false)

export function useNavigationShortcuts() {
  const router = useRouter()
  let timeoutId = null

  function isInputFocused() {
    const el = document.activeElement
    if (!el) return false
    const tag = el.tagName
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
    if (el.isContentEditable) return true
    return false
  }

  function cancelGMode() {
    isGMode.value = false
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }

  function handleKeyDown(e) {
    if (isInputFocused()) return
    if (e.metaKey || e.ctrlKey || e.altKey) return

    const key = e.key.toLowerCase()

    if (isGMode.value) {
      cancelGMode()
      const shortcut = NAV_SHORTCUTS[key]
      if (shortcut) {
        e.preventDefault()
        router.push(shortcut.path)
      }
      return
    }

    if (key === 'g') {
      isGMode.value = true
      timeoutId = setTimeout(cancelGMode, SHORTCUT_TIMEOUT_MS)
    }
  }

  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
    cancelGMode()
  })

  return { isGMode, shortcuts: NAV_SHORTCUTS }
}
