import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import HeroSwarm from '../HeroSwarm.vue'

let rafQueue = []
let rafId = 1

function createCanvasContext() {
  return {
    clearRect: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    arc: vi.fn(),
    fill: vi.fn(),
    stroke: vi.fn(),
    setTransform: vi.fn(),
    globalAlpha: 1,
    strokeStyle: '',
    fillStyle: '',
    lineWidth: 1,
  }
}

beforeEach(() => {
  rafQueue = []
  rafId = 1

  vi.stubGlobal('requestAnimationFrame', vi.fn((cb) => {
    const id = rafId++
    rafQueue.push({ id, cb })
    return id
  }))
  vi.stubGlobal('cancelAnimationFrame', vi.fn((id) => {
    rafQueue = rafQueue.filter(item => item.id !== id)
  }))
  vi.stubGlobal('devicePixelRatio', 1)

  // Mock HTMLCanvasElement.getContext before any component mounts
  const ctx = createCanvasContext()
  const origGetContext = HTMLCanvasElement.prototype.getContext
  HTMLCanvasElement.prototype.getContext = function (type) {
    if (type === '2d') return ctx
    return origGetContext.call(this, type)
  }
  HTMLCanvasElement.prototype._origGetContext = origGetContext
  HTMLCanvasElement.prototype._mockCtx = ctx
})

afterEach(() => {
  // Restore original getContext
  if (HTMLCanvasElement.prototype._origGetContext) {
    HTMLCanvasElement.prototype.getContext = HTMLCanvasElement.prototype._origGetContext
    delete HTMLCanvasElement.prototype._origGetContext
    delete HTMLCanvasElement.prototype._mockCtx
  }
  vi.unstubAllGlobals()
})

function mountHeroSwarm() {
  const container = document.createElement('div')
  Object.defineProperty(container, 'getBoundingClientRect', {
    value: () => ({ width: 800, height: 600, top: 0, left: 0, right: 800, bottom: 600 }),
    configurable: true,
  })
  document.body.appendChild(container)
  const wrapper = mount(HeroSwarm, { attachTo: container })
  return { wrapper, container }
}

describe('HeroSwarm', () => {
  describe('rendering', () => {
    it('renders a canvas element', () => {
      const { wrapper, container } = mountHeroSwarm()
      expect(wrapper.find('canvas').exists()).toBe(true)
      wrapper.unmount()
      container.remove()
    })

    it('canvas has correct CSS classes', () => {
      const { wrapper, container } = mountHeroSwarm()
      const canvas = wrapper.find('canvas')
      expect(canvas.classes()).toContain('absolute')
      expect(canvas.classes()).toContain('inset-0')
      expect(canvas.classes()).toContain('pointer-events-none')
      wrapper.unmount()
      container.remove()
    })
  })

  describe('animation lifecycle', () => {
    it('starts requestAnimationFrame loop on mount', () => {
      const { wrapper, container } = mountHeroSwarm()
      expect(requestAnimationFrame).toHaveBeenCalled()
      wrapper.unmount()
      container.remove()
    })

    it('cancels animation frame on unmount', () => {
      const { wrapper, container } = mountHeroSwarm()
      wrapper.unmount()
      expect(cancelAnimationFrame).toHaveBeenCalled()
      container.remove()
    })
  })

  describe('resize handling', () => {
    it('adds resize event listener on mount', () => {
      const addSpy = vi.spyOn(window, 'addEventListener')
      const { wrapper, container } = mountHeroSwarm()

      const resizeCalls = addSpy.mock.calls.filter(([event]) => event === 'resize')
      expect(resizeCalls.length).toBeGreaterThan(0)

      wrapper.unmount()
      container.remove()
      addSpy.mockRestore()
    })

    it('removes resize event listener on unmount', () => {
      const removeSpy = vi.spyOn(window, 'removeEventListener')
      const { wrapper, container } = mountHeroSwarm()
      wrapper.unmount()

      const resizeCalls = removeSpy.mock.calls.filter(([event]) => event === 'resize')
      expect(resizeCalls.length).toBeGreaterThan(0)

      container.remove()
      removeSpy.mockRestore()
    })
  })
})
