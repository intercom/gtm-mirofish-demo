import { describe, it, expect, vi, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { useCountUp } from '../useCountUp.js'

function mountComposable(setup) {
  const Comp = defineComponent({
    setup() {
      const result = setup()
      return { result }
    },
    render() {
      return h('div')
    },
  })
  return mount(Comp)
}

function createRafController() {
  const queue = []
  let nextId = 1
  const raf = (cb) => {
    const id = nextId++
    queue.push({ id, cb })
    return id
  }
  const cancel = vi.fn((id) => {
    const idx = queue.findIndex((item) => item.id === id)
    if (idx !== -1) queue.splice(idx, 1)
  })
  const flush = (timestamp) => {
    // Process all queued callbacks (they may enqueue more)
    let safety = 200
    while (queue.length > 0 && safety-- > 0) {
      const { cb } = queue.shift()
      cb(timestamp)
    }
  }
  return { raf, cancel, flush, queue }
}

describe('useCountUp', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('starts at 0 when source is 0', () => {
    const source = ref(0)
    let display
    const wrapper = mountComposable(() => {
      display = useCountUp(source)
      return display
    })

    expect(display.value).toBe(0)
    wrapper.unmount()
  })

  it('animates to target value', async () => {
    const ctrl = createRafController()
    vi.stubGlobal('requestAnimationFrame', ctrl.raf)
    vi.stubGlobal('cancelAnimationFrame', ctrl.cancel)

    const source = ref(0)
    let display

    const wrapper = mountComposable(() => {
      display = useCountUp(source, { duration: 1000 })
      return display
    })

    source.value = 100
    await nextTick()

    // Flush at a time well past the duration to complete animation
    ctrl.flush(performance.now() + 2000)

    expect(display.value).toBe(100)
    wrapper.unmount()
  })

  it('shows intermediate values mid-animation', async () => {
    const ctrl = createRafController()
    vi.stubGlobal('requestAnimationFrame', ctrl.raf)
    vi.stubGlobal('cancelAnimationFrame', ctrl.cancel)

    const source = ref(0)
    let display

    const wrapper = mountComposable(() => {
      display = useCountUp(source, { duration: 1000 })
      return display
    })

    source.value = 1000
    await nextTick()

    // Advance to ~50% of duration — value should be partially animated
    const startTime = performance.now()
    const { cb } = ctrl.queue.shift()
    cb(startTime + 500)

    expect(display.value).toBeGreaterThan(0)
    expect(display.value).toBeLessThan(1000)

    wrapper.unmount()
  })

  it('handles non-numeric values gracefully', async () => {
    const source = ref(0)
    let display

    const wrapper = mountComposable(() => {
      display = useCountUp(source)
      return display
    })

    source.value = NaN
    await nextTick()
    expect(display.value).toBe(0)

    wrapper.unmount()
  })

  it('accepts a getter function as source', () => {
    const data = ref({ count: 0 })
    let display

    const wrapper = mountComposable(() => {
      display = useCountUp(() => data.value.count)
      return display
    })

    expect(display.value).toBe(0)
    wrapper.unmount()
  })

  it('cancels animation on unmount', async () => {
    const ctrl = createRafController()
    vi.stubGlobal('requestAnimationFrame', ctrl.raf)
    vi.stubGlobal('cancelAnimationFrame', ctrl.cancel)

    const source = ref(0)
    let display

    const wrapper = mountComposable(() => {
      display = useCountUp(source, { duration: 1000 })
      return display
    })

    source.value = 100
    await nextTick()
    expect(ctrl.queue.length).toBeGreaterThan(0)

    wrapper.unmount()
    expect(ctrl.cancel).toHaveBeenCalled()
  })
})
