import { onMounted, onUnmounted } from 'vue'

/**
 * Adds a Material-style ripple effect to a template ref element.
 * Uses pointerdown for instant feedback on touch devices (no click delay).
 * The element must have `position: relative; overflow: hidden` (or use .ripple-container class).
 */
export function useRipple(elRef) {
  function handlePointerDown(e) {
    const el = elRef.value?.$el || elRef.value
    if (!el || el.disabled) return

    const rect = el.getBoundingClientRect()
    const size = Math.max(rect.width, rect.height)
    const x = e.clientX - rect.left - size / 2
    const y = e.clientY - rect.top - size / 2

    const ripple = document.createElement('span')
    ripple.className = 'ripple'
    ripple.style.width = ripple.style.height = `${size}px`
    ripple.style.left = `${x}px`
    ripple.style.top = `${y}px`

    el.appendChild(ripple)
    ripple.addEventListener('animationend', () => ripple.remove())
  }

  onMounted(() => {
    const el = elRef.value?.$el || elRef.value
    el?.addEventListener('pointerdown', handlePointerDown)
  })

  onUnmounted(() => {
    const el = elRef.value?.$el || elRef.value
    el?.removeEventListener('pointerdown', handlePointerDown)
  })
}
