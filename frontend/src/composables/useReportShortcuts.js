import { ref, onMounted, onUnmounted } from 'vue'

export const REPORT_SHORTCUTS = [
  { keys: '⌘/Ctrl + P', label: 'Preview report' },
  { keys: '⌘/Ctrl + E', label: 'Export report' },
  { keys: '⌘/Ctrl + ⇧ + S', label: 'Save as template' },
  { keys: 'Delete', label: 'Remove section' },
  { keys: '⌘/Ctrl + ↑', label: 'Previous chapter' },
  { keys: '⌘/Ctrl + ↓', label: 'Next chapter' },
  { keys: '?', label: 'Toggle shortcuts help' },
]

export function useReportShortcuts(callbacks = {}) {
  const showHelp = ref(false)

  function isInputFocused() {
    const tag = document.activeElement?.tagName?.toLowerCase()
    return tag === 'input' || tag === 'textarea' || tag === 'select'
  }

  function isMod(e) {
    return e.metaKey || e.ctrlKey
  }

  function handleKeydown(e) {
    if (isInputFocused()) return

    if (isMod(e) && e.key.toLowerCase() === 'p') {
      e.preventDefault()
      callbacks.onPreview?.()
      return
    }

    if (isMod(e) && e.key.toLowerCase() === 'e') {
      e.preventDefault()
      callbacks.onExport?.()
      return
    }

    if (isMod(e) && e.shiftKey && e.key.toLowerCase() === 's') {
      e.preventDefault()
      callbacks.onSaveTemplate?.()
      return
    }

    if (e.key === 'Delete') {
      callbacks.onDeleteSection?.()
      return
    }

    if (isMod(e) && e.key === 'ArrowUp') {
      e.preventDefault()
      callbacks.onMoveUp?.()
      return
    }

    if (isMod(e) && e.key === 'ArrowDown') {
      e.preventDefault()
      callbacks.onMoveDown?.()
      return
    }

    if (e.key === '?') {
      showHelp.value = !showHelp.value
    }
  }

  onMounted(() => window.addEventListener('keydown', handleKeydown))
  onUnmounted(() => window.removeEventListener('keydown', handleKeydown))

  return { showHelp, shortcuts: REPORT_SHORTCUTS }
}
