import { ref } from 'vue'

/**
 * Composable for triggering form interaction animations programmatically.
 * Uses CSS animation classes defined in style.css (animate-shake, animate-success).
 */
export function useFormAnimations() {
  const shaking = ref(false)
  const flashing = ref(false)

  function triggerShake(el) {
    if (el instanceof HTMLElement) {
      el.classList.add('animate-shake')
      el.addEventListener('animationend', () => el.classList.remove('animate-shake'), { once: true })
    } else {
      shaking.value = true
      setTimeout(() => { shaking.value = false }, 400)
    }
  }

  function triggerSuccess(el) {
    if (el instanceof HTMLElement) {
      el.classList.add('animate-success')
      el.addEventListener('animationend', () => el.classList.remove('animate-success'), { once: true })
    } else {
      flashing.value = true
      setTimeout(() => { flashing.value = false }, 600)
    }
  }

  return { shaking, flashing, triggerShake, triggerSuccess }
}
