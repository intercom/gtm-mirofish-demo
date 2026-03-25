import { ref, onMounted, onUnmounted } from 'vue'

const showHelp = ref(false)
let listenerCount = 0

const shortcuts = [
  {
    group: 'General',
    items: [
      { keys: ['?'], description: 'Show keyboard shortcuts' },
      { keys: ['Esc'], description: 'Close modal / dialog' },
    ],
  },
  {
    group: 'Workspace',
    items: [
      { keys: ['1'], description: 'Switch to Knowledge Graph tab' },
      { keys: ['2'], description: 'Switch to Simulation tab' },
    ],
  },
  {
    group: 'Chat',
    items: [
      { keys: ['Enter'], description: 'Send message' },
      { keys: ['Shift', 'Enter'], description: 'New line in message' },
    ],
  },
]

function isInputFocused() {
  const tag = document.activeElement?.tagName?.toLowerCase()
  return tag === 'input' || tag === 'textarea' || tag === 'select'
}

function handleKeydown(e) {
  if (e.key === 'Escape') {
    showHelp.value = false
    return
  }

  if (isInputFocused()) return

  if (e.key === '?') {
    e.preventDefault()
    showHelp.value = !showHelp.value
  }
}

export function useKeyboardShortcuts() {
  onMounted(() => {
    if (listenerCount === 0) {
      window.addEventListener('keydown', handleKeydown)
    }
    listenerCount++
  })

  onUnmounted(() => {
    listenerCount--
    if (listenerCount === 0) {
      window.removeEventListener('keydown', handleKeydown)
    }
  })

  return { showHelp, shortcuts }
}
