import { ref, onMounted, onUnmounted } from 'vue'

const isMac = typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform)

function isInputFocused() {
  const tag = document.activeElement?.tagName?.toLowerCase()
  return tag === 'input' || tag === 'textarea' || tag === 'select'
}

export function useKeyboardShortcuts(shortcuts) {
  const showHelp = ref(false)

  function handleKeydown(e) {
    // ? toggles help overlay (shift+/ on US keyboards)
    if (e.key === '?' && !isInputFocused()) {
      e.preventDefault()
      showHelp.value = !showHelp.value
      return
    }

    // Escape closes help if open
    if (e.key === 'Escape' && showHelp.value) {
      showHelp.value = false
      return
    }

    for (const s of shortcuts) {
      const wantsMod = !!s.mod
      const hasMod = isMac ? e.metaKey : e.ctrlKey
      if (wantsMod !== hasMod) continue
      if (e.key !== s.key) continue
      // Skip when typing unless shortcut opts in via global or uses modifier
      if (isInputFocused() && !s.global && !wantsMod) continue

      e.preventDefault()
      s.action()
      return
    }
  }

  onMounted(() => window.addEventListener('keydown', handleKeydown))
  onUnmounted(() => window.removeEventListener('keydown', handleKeydown))

  return { showHelp, modLabel: isMac ? '⌘' : 'Ctrl' }
}
