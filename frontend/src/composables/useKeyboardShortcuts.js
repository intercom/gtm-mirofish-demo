import { ref, onMounted, onUnmounted } from 'vue'

const visible = ref(false)

const shortcuts = [
  {
    group: 'Global',
    items: [
      { keys: ['?'], description: 'Show keyboard shortcuts' },
      { keys: ['Esc'], description: 'Close dialogs & overlays' },
    ],
  },
  {
    group: 'Workspace',
    items: [
      { keys: ['1'], description: 'Switch to Graph tab' },
      { keys: ['2'], description: 'Switch to Simulation tab' },
    ],
  },
  {
    group: 'Chat & Interview',
    items: [
      { keys: ['Enter'], description: 'Send message' },
    ],
  },
]

function toggle() {
  visible.value = !visible.value
}

function close() {
  visible.value = false
}

export function useKeyboardShortcuts() {
  function handleKeydown(e) {
    const tag = document.activeElement?.tagName?.toLowerCase()
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return

    if (e.key === '?') {
      e.preventDefault()
      toggle()
    } else if (e.key === 'Escape' && visible.value) {
      close()
    }
  }

  onMounted(() => window.addEventListener('keydown', handleKeydown))
  onUnmounted(() => window.removeEventListener('keydown', handleKeydown))

  return { visible, shortcuts, toggle, close }
}
