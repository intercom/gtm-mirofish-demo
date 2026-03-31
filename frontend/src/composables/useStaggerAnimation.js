/**
 * Composable for staggered list entrance animations using Web Animations API.
 * Returns hooks for <TransitionGroup :css="false" appear>.
 *
 * First batch of items staggers in with incremental delays.
 * Items added later (e.g. via polling) enter immediately.
 * Call reset() to re-enable stagger for the next batch.
 */
export function useStaggerAnimation(options = {}) {
  const { delay = 50, duration = 300, distance = 12 } = options
  let initialBatch = true
  let batchTimer = null

  function onBeforeEnter(el) {
    el.style.opacity = 0
    el.style.transform = `translateY(${distance}px)`
  }

  function onEnter(el, done) {
    const index = Number(el.dataset.index) || 0
    const staggerDelay = initialBatch ? index * delay : 0

    const animation = el.animate(
      [
        { opacity: 0, transform: `translateY(${distance}px)` },
        { opacity: 1, transform: 'translateY(0)' },
      ],
      { duration, delay: staggerDelay, easing: 'ease', fill: 'forwards' },
    )
    animation.onfinish = () => {
      el.style.opacity = ''
      el.style.transform = ''
      done()
    }

    if (initialBatch) {
      clearTimeout(batchTimer)
      batchTimer = setTimeout(() => { initialBatch = false }, 0)
    }
  }

  function onLeave(el, done) {
    const animation = el.animate(
      [{ opacity: 1 }, { opacity: 0 }],
      { duration: duration * 0.5, easing: 'ease', fill: 'forwards' },
    )
    animation.onfinish = done
  }

  function reset() {
    initialBatch = true
  }

  return { onBeforeEnter, onEnter, onLeave, reset }
}
