import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  fadeIn,
  fadeOut,
  slideIn,
  slideOut,
  scaleIn,
  bounceIn,
  staggerChildren,
} from '../animations.js'

function mockElement() {
  const animations = []
  return {
    animate: vi.fn((keyframes, options) => {
      const anim = { keyframes, options, finished: Promise.resolve(), cancel: vi.fn() }
      animations.push(anim)
      return anim
    }),
    children: [],
    _animations: animations,
  }
}

function mockParent(childCount) {
  const children = Array.from({ length: childCount }, () => mockElement())
  return { children, _children: children }
}

function mockReducedMotion(enabled) {
  vi.stubGlobal('matchMedia', vi.fn(() => ({ matches: enabled })))
}

describe('animations.js', () => {
  beforeEach(() => {
    mockReducedMotion(false)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe('fadeIn', () => {
    it('animates opacity from 0 to 1', () => {
      const el = mockElement()
      const anim = fadeIn(el)
      expect(el.animate).toHaveBeenCalledOnce()
      const [keyframes, options] = el.animate.mock.calls[0]
      expect(keyframes).toEqual([{ opacity: 0 }, { opacity: 1 }])
      expect(options.fill).toBe('forwards')
      expect(anim).toBeDefined()
    })

    it('uses custom duration', () => {
      const el = mockElement()
      fadeIn(el, 500)
      expect(el.animate.mock.calls[0][1].duration).toBe(500)
    })

    it('defaults to 300ms duration', () => {
      const el = mockElement()
      fadeIn(el)
      expect(el.animate.mock.calls[0][1].duration).toBe(300)
    })
  })

  describe('fadeOut', () => {
    it('animates opacity from 1 to 0', () => {
      const el = mockElement()
      fadeOut(el)
      const [keyframes] = el.animate.mock.calls[0]
      expect(keyframes).toEqual([{ opacity: 1 }, { opacity: 0 }])
    })
  })

  describe('slideIn', () => {
    it('slides up by default', () => {
      const el = mockElement()
      slideIn(el)
      const [keyframes] = el.animate.mock.calls[0]
      expect(keyframes[0].transform).toBe('translate(0px, 16px)')
      expect(keyframes[1].transform).toBe('translate(0, 0)')
    })

    it('supports all four directions', () => {
      for (const dir of ['up', 'down', 'left', 'right']) {
        const el = mockElement()
        slideIn(el, dir)
        expect(el.animate).toHaveBeenCalledOnce()
      }
    })

    it('slides from right for direction "left"', () => {
      const el = mockElement()
      slideIn(el, 'left')
      const [keyframes] = el.animate.mock.calls[0]
      expect(keyframes[0].transform).toBe('translate(16px, 0px)')
    })
  })

  describe('slideOut', () => {
    it('slides upward by default', () => {
      const el = mockElement()
      slideOut(el)
      const [keyframes] = el.animate.mock.calls[0]
      expect(keyframes[0].transform).toBe('translate(0, 0)')
      expect(keyframes[1].transform).toBe('translate(0px, -16px)')
    })
  })

  describe('scaleIn', () => {
    it('scales from 0.85 to 1 with overshoot easing', () => {
      const el = mockElement()
      scaleIn(el)
      const [keyframes, options] = el.animate.mock.calls[0]
      expect(keyframes[0].transform).toBe('scale(0.85)')
      expect(keyframes[1].transform).toBe('scale(1)')
      expect(options.easing).toBe('cubic-bezier(0.34, 1.56, 0.64, 1)')
    })
  })

  describe('bounceIn', () => {
    it('uses multi-step keyframes with overshoot', () => {
      const el = mockElement()
      bounceIn(el)
      const [keyframes, options] = el.animate.mock.calls[0]
      expect(keyframes).toHaveLength(4)
      expect(keyframes[0].transform).toBe('scale(0.3)')
      expect(keyframes[1].transform).toBe('scale(1.05)')
      expect(keyframes[2].transform).toBe('scale(0.95)')
      expect(keyframes[3].transform).toBe('scale(1)')
      expect(options.duration).toBe(500)
    })
  })

  describe('staggerChildren', () => {
    it('animates each child with incremental delay', () => {
      const parent = mockParent(3)
      const anims = staggerChildren(parent, 100)
      expect(anims).toHaveLength(3)
      expect(parent._children[0].animate.mock.calls[0][1].delay).toBe(0)
      expect(parent._children[1].animate.mock.calls[0][1].delay).toBe(100)
      expect(parent._children[2].animate.mock.calls[0][1].delay).toBe(200)
    })

    it('uses fill: both so children are hidden during delay', () => {
      const parent = mockParent(2)
      staggerChildren(parent)
      expect(parent._children[0].animate.mock.calls[0][1].fill).toBe('both')
    })

    it('defaults to 50ms stagger delay', () => {
      const parent = mockParent(2)
      staggerChildren(parent)
      expect(parent._children[1].animate.mock.calls[0][1].delay).toBe(50)
    })
  })

  describe('prefers-reduced-motion', () => {
    beforeEach(() => {
      mockReducedMotion(true)
    })

    it('sets duration to 0 for fadeIn', () => {
      const el = mockElement()
      fadeIn(el, 500)
      expect(el.animate.mock.calls[0][1].duration).toBe(0)
    })

    it('sets duration to 0 for slideIn', () => {
      const el = mockElement()
      slideIn(el, 'up', 400)
      expect(el.animate.mock.calls[0][1].duration).toBe(0)
    })

    it('sets duration and delay to 0 for staggerChildren', () => {
      const parent = mockParent(3)
      staggerChildren(parent, 100)
      for (const child of parent._children) {
        const opts = child.animate.mock.calls[0][1]
        expect(opts.duration).toBe(0)
        expect(opts.delay).toBe(0)
      }
    })
  })
})
