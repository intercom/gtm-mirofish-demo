import { describe, it, expect, vi, afterEach } from 'vitest'
import { ref, nextTick, inject } from 'vue'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { useTimelineScrubber, useTimelineContext, TIMELINE_KEY, DEFAULT_SPEEDS } from '../useTimelineScrubber.js'

function mountComposable(setup, childSetup) {
  const Child = childSetup
    ? defineComponent({
        setup() {
          const result = childSetup()
          return { result }
        },
        render() { return h('span') },
      })
    : null

  const Parent = defineComponent({
    setup() {
      const result = setup()
      return { result }
    },
    render() {
      return Child ? h('div', [h(Child)]) : h('div')
    },
  })
  return mount(Parent)
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
    let safety = 200
    while (queue.length > 0 && safety-- > 0) {
      const { cb } = queue.shift()
      cb(timestamp)
    }
  }
  return { raf, cancel, flush, queue }
}

describe('useTimelineScrubber', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('initializes with default state', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    expect(timeline.currentPosition.value).toBe(0)
    expect(timeline.isPlaying.value).toBe(false)
    expect(timeline.playbackSpeed.value).toBe(1)
    expect(timeline.marks.value).toEqual([])

    wrapper.unmount()
  })

  it('respects custom default speed', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber({ defaultSpeed: 2 })
      return timeline
    })

    expect(timeline.playbackSpeed.value).toBe(2)
    wrapper.unmount()
  })

  it('computes currentRound from position and totalRounds', () => {
    const rounds = ref(10)
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber({ totalRounds: rounds })
      return timeline
    })

    expect(timeline.currentRound.value).toBe(1)

    timeline.seek(0.5)
    expect(timeline.currentRound.value).toBe(6)

    timeline.seek(1)
    expect(timeline.currentRound.value).toBe(10)

    wrapper.unmount()
  })

  it('seek clamps position to [0, 1]', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    timeline.seek(-0.5)
    expect(timeline.currentPosition.value).toBe(0)

    timeline.seek(1.5)
    expect(timeline.currentPosition.value).toBe(1)

    timeline.seek(0.75)
    expect(timeline.currentPosition.value).toBe(0.75)

    wrapper.unmount()
  })

  it('seekToRound maps round number to normalized position', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber({ totalRounds: ref(10) })
      return timeline
    })

    timeline.seekToRound(1)
    expect(timeline.currentPosition.value).toBe(0)

    timeline.seekToRound(10)
    expect(timeline.currentPosition.value).toBe(1)

    timeline.seekToRound(5)
    expect(timeline.currentPosition.value).toBeCloseTo(4 / 9)

    wrapper.unmount()
  })

  it('stepForward and stepBack move by one round increment', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber({ totalRounds: ref(5) })
      return timeline
    })

    const step = 1 / 4

    timeline.stepForward()
    expect(timeline.currentPosition.value).toBeCloseTo(step)

    timeline.stepForward()
    expect(timeline.currentPosition.value).toBeCloseTo(step * 2)

    timeline.stepBack()
    expect(timeline.currentPosition.value).toBeCloseTo(step)

    wrapper.unmount()
  })

  it('setSpeed changes playback speed', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    timeline.setSpeed(4)
    expect(timeline.playbackSpeed.value).toBe(4)

    timeline.setSpeed(0.5)
    expect(timeline.playbackSpeed.value).toBe(0.5)

    wrapper.unmount()
  })

  it('setMarks updates marks array', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    const newMarks = [{ position: 0.25, type: 'decision' }, { position: 0.75, type: 'milestone' }]
    timeline.setMarks(newMarks)
    expect(timeline.marks.value).toEqual(newMarks)

    wrapper.unmount()
  })

  it('reset stops playback and resets position', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    timeline.seek(0.5)
    timeline.reset()

    expect(timeline.currentPosition.value).toBe(0)
    expect(timeline.isPlaying.value).toBe(false)

    wrapper.unmount()
  })

  it('play starts from 0 if position is at end', () => {
    const ctrl = createRafController()
    vi.stubGlobal('requestAnimationFrame', ctrl.raf)
    vi.stubGlobal('cancelAnimationFrame', ctrl.cancel)

    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    timeline.seek(1)
    timeline.play()
    expect(timeline.currentPosition.value).toBe(0)
    expect(timeline.isPlaying.value).toBe(true)

    wrapper.unmount()
  })

  it('pause stops playback and cancels animation frame', () => {
    const ctrl = createRafController()
    vi.stubGlobal('requestAnimationFrame', ctrl.raf)
    vi.stubGlobal('cancelAnimationFrame', ctrl.cancel)

    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    timeline.play()
    expect(timeline.isPlaying.value).toBe(true)

    timeline.pause()
    expect(timeline.isPlaying.value).toBe(false)
    expect(ctrl.cancel).toHaveBeenCalled()

    wrapper.unmount()
  })

  it('togglePlay alternates between play and pause', () => {
    const ctrl = createRafController()
    vi.stubGlobal('requestAnimationFrame', ctrl.raf)
    vi.stubGlobal('cancelAnimationFrame', ctrl.cancel)

    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    timeline.togglePlay()
    expect(timeline.isPlaying.value).toBe(true)

    timeline.togglePlay()
    expect(timeline.isPlaying.value).toBe(false)

    wrapper.unmount()
  })

  it('fires onPositionChange callbacks when position changes', async () => {
    const cb = vi.fn()
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      timeline.onPositionChange(cb)
      return timeline
    })

    timeline.seek(0.5)
    await nextTick()

    expect(cb).toHaveBeenCalledWith(0.5)

    wrapper.unmount()
  })

  it('fires onPlay and onPause callbacks', () => {
    const ctrl = createRafController()
    vi.stubGlobal('requestAnimationFrame', ctrl.raf)
    vi.stubGlobal('cancelAnimationFrame', ctrl.cancel)

    const playCb = vi.fn()
    const pauseCb = vi.fn()
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      timeline.onPlay(playCb)
      timeline.onPause(pauseCb)
      return timeline
    })

    timeline.play()
    expect(playCb).toHaveBeenCalledOnce()

    timeline.pause()
    expect(pauseCb).toHaveBeenCalledOnce()

    wrapper.unmount()
  })

  it('provides context to child components via inject', () => {
    let childContext
    const wrapper = mountComposable(
      () => useTimelineScrubber(),
      () => {
        childContext = useTimelineContext()
        return childContext
      },
    )

    expect(childContext).toBeDefined()
    expect(childContext.currentPosition.value).toBe(0)
    expect(typeof childContext.play).toBe('function')
    expect(typeof childContext.seek).toBe('function')

    wrapper.unmount()
  })

  it('useTimelineContext throws when no provider exists', () => {
    expect(() => {
      mountComposable(() => useTimelineContext())
    }).toThrow('useTimelineContext() requires an ancestor component that calls useTimelineScrubber()')
  })

  it('keyboard Space toggles play/pause', async () => {
    const ctrl = createRafController()
    vi.stubGlobal('requestAnimationFrame', ctrl.raf)
    vi.stubGlobal('cancelAnimationFrame', ctrl.cancel)

    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    document.dispatchEvent(new KeyboardEvent('keydown', { key: ' ' }))
    expect(timeline.isPlaying.value).toBe(true)

    document.dispatchEvent(new KeyboardEvent('keydown', { key: ' ' }))
    expect(timeline.isPlaying.value).toBe(false)

    wrapper.unmount()
  })

  it('keyboard ArrowRight steps forward', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber({ totalRounds: ref(10) })
      return timeline
    })

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }))
    expect(timeline.currentPosition.value).toBeGreaterThan(0)

    wrapper.unmount()
  })

  it('keyboard ArrowLeft steps backward', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber({ totalRounds: ref(10) })
      return timeline
    })

    timeline.seek(0.5)
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft' }))
    expect(timeline.currentPosition.value).toBeLessThan(0.5)

    wrapper.unmount()
  })

  it('keyboard +/- changes speed', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    expect(timeline.playbackSpeed.value).toBe(1)

    document.dispatchEvent(new KeyboardEvent('keydown', { key: '+' }))
    expect(timeline.playbackSpeed.value).toBe(2)

    document.dispatchEvent(new KeyboardEvent('keydown', { key: '-' }))
    expect(timeline.playbackSpeed.value).toBe(1)

    wrapper.unmount()
  })

  it('keyboard shortcuts are disabled for input elements', () => {
    const ctrl = createRafController()
    vi.stubGlobal('requestAnimationFrame', ctrl.raf)
    vi.stubGlobal('cancelAnimationFrame', ctrl.cancel)

    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    const event = new KeyboardEvent('keydown', { key: ' ' })
    Object.defineProperty(event, 'target', { value: { tagName: 'INPUT' } })
    document.dispatchEvent(event)

    expect(timeline.isPlaying.value).toBe(false)

    wrapper.unmount()
  })

  it('exports DEFAULT_SPEEDS array', () => {
    expect(DEFAULT_SPEEDS).toEqual([0.5, 1, 2, 4])
  })

  it('exposes availableSpeeds in context', () => {
    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    expect(timeline.availableSpeeds).toEqual([0.5, 1, 2, 4])
    wrapper.unmount()
  })

  it('cleans up on unmount', () => {
    const ctrl = createRafController()
    vi.stubGlobal('requestAnimationFrame', ctrl.raf)
    vi.stubGlobal('cancelAnimationFrame', ctrl.cancel)
    const removeListenerSpy = vi.spyOn(document, 'removeEventListener')

    let timeline
    const wrapper = mountComposable(() => {
      timeline = useTimelineScrubber()
      return timeline
    })

    timeline.play()
    wrapper.unmount()

    expect(timeline.isPlaying.value).toBe(false)
    expect(removeListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function))

    removeListenerSpy.mockRestore()
  })
})
