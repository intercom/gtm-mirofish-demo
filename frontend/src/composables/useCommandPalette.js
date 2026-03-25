import { ref, onMounted, onUnmounted } from 'vue'

const isOpen = ref(false)

export function useCommandPalette() {
  function open() {
    isOpen.value = true
  }

  function close() {
    isOpen.value = false
  }

  function toggle() {
    isOpen.value = !isOpen.value
  }

  function onKeydown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      toggle()
    }
    if (e.key === 'Escape' && isOpen.value) {
      e.preventDefault()
      close()
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', onKeydown)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', onKeydown)
  })

  return { isOpen, open, close, toggle }
}
