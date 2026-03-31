import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useStaggerAnimation } from '../useStaggerAnimation.js'

function createMockElement(index = 0) {
  const style = { opacity: '', transform: '' }
  const animations = []
  return {
    style,
    dataset: { index: String(index) },
    animate(keyframes, options) {
      const anim = { keyframes, options, onfinish: null }
      animations.push(anim)
      return anim
    },
    _animations: animations,
  }
}

describe('useStaggerAnimation', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  it('returns required hook functions', () => {
    const result = useStaggerAnimation()
    expect(result.onBeforeEnter).toBeTypeOf('function')
    expect(result.onEnter).toBeTypeOf('function')
    expect(result.onLeave).toBeTypeOf('function')
    expect(result.reset).toBeTypeOf('function')
  })

  it('onBeforeEnter sets initial hidden state', () => {
    const { onBeforeEnter } = useStaggerAnimation({ distance: 12 })
    const el = createMockElement()
    onBeforeEnter(el)
    expect(el.style.opacity).toBe(0)
    expect(el.style.transform).toBe('translateY(12px)')
  })

  it('onEnter applies stagger delay based on data-index for initial batch', () => {
    const { onEnter } = useStaggerAnimation({ delay: 50, duration: 300, distance: 12 })
    const el0 = createMockElement(0)
    const el1 = createMockElement(1)
    const el2 = createMockElement(2)
    const done = vi.fn()

    onEnter(el0, done)
    onEnter(el1, done)
    onEnter(el2, done)

    expect(el0._animations[0].options.delay).toBe(0)
    expect(el1._animations[0].options.delay).toBe(50)
    expect(el2._animations[0].options.delay).toBe(100)
    expect(el0._animations[0].options.duration).toBe(300)
  })

  it('onEnter calls done and clears styles on finish', () => {
    const { onEnter } = useStaggerAnimation()
    const el = createMockElement(0)
    el.style.opacity = 0
    el.style.transform = 'translateY(12px)'
    const done = vi.fn()

    onEnter(el, done)
    el._animations[0].onfinish()

    expect(done).toHaveBeenCalled()
    expect(el.style.opacity).toBe('')
    expect(el.style.transform).toBe('')
  })

  it('items after initial batch enter without stagger delay', () => {
    const { onEnter } = useStaggerAnimation({ delay: 50 })
    const done = vi.fn()

    // Simulate initial batch
    onEnter(createMockElement(0), done)
    onEnter(createMockElement(1), done)

    // Flush the setTimeout(0) that marks end of initial batch
    vi.runAllTimers()

    // New item added later
    const laterEl = createMockElement(5)
    onEnter(laterEl, done)
    expect(laterEl._animations[0].options.delay).toBe(0)
  })

  it('reset re-enables stagger for next batch', () => {
    const { onEnter, reset } = useStaggerAnimation({ delay: 50 })
    const done = vi.fn()

    onEnter(createMockElement(0), done)
    vi.runAllTimers()

    // After reset, stagger should apply again
    reset()
    const el = createMockElement(3)
    onEnter(el, done)
    expect(el._animations[0].options.delay).toBe(150)
  })

  it('onLeave animates opacity to 0', () => {
    const { onLeave } = useStaggerAnimation({ duration: 300 })
    const el = createMockElement()
    const done = vi.fn()

    onLeave(el, done)

    const anim = el._animations[0]
    expect(anim.keyframes).toEqual([{ opacity: 1 }, { opacity: 0 }])
    expect(anim.options.duration).toBe(150) // 300 * 0.5
    anim.onfinish()
    expect(done).toHaveBeenCalled()
  })

  it('accepts custom options', () => {
    const { onBeforeEnter, onEnter } = useStaggerAnimation({
      delay: 100,
      duration: 500,
      distance: 20,
    })
    const el = createMockElement(2)
    onBeforeEnter(el)
    expect(el.style.transform).toBe('translateY(20px)')

    onEnter(el, vi.fn())
    expect(el._animations[0].options.delay).toBe(200)
    expect(el._animations[0].options.duration).toBe(500)
  })
})
