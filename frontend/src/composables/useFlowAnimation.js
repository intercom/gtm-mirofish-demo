import { ref, readonly, onUnmounted, nextTick, provide, inject } from 'vue'

const FLOW_KEY = Symbol('flowAnimation')

/**
 * Composable for managing requestAnimationFrame-based flow animations.
 * Provides play/pause, speed control, and IntersectionObserver auto-pause.
 */
export function useFlowAnimation(options = {}) {
  const { autoplay = false } = options

  const playing = ref(false)
  const speed = ref(1)
  const currentTime = ref(0)

  const _cbs = new Set()
  let _fid = null
  let _prev = null
  let _obs = null
  let _vis = true

  function onFrame(cb) {
    _cbs.add(cb)
    return () => _cbs.delete(cb)
  }

  function _tick(ts) {
    if (!_prev) _prev = ts
    const dt = (ts - _prev) * speed.value
    _prev = ts
    currentTime.value += dt
    for (const cb of _cbs) cb({ time: currentTime.value, delta: dt, speed: speed.value })
    if (playing.value && _vis) _fid = requestAnimationFrame(_tick)
  }

  function play() {
    if (playing.value) return
    playing.value = true
    _prev = null
    _fid = requestAnimationFrame(_tick)
  }

  function pause() {
    playing.value = false
    if (_fid) { cancelAnimationFrame(_fid); _fid = null }
    _prev = null
  }

  function setSpeed(v) {
    speed.value = Math.max(0.5, Math.min(4, v))
  }

  function seek(t) {
    currentTime.value = Math.max(0, t)
  }

  function observe(el) {
    if (!el || typeof IntersectionObserver === 'undefined') return
    _obs = new IntersectionObserver(([e]) => {
      _vis = e.isIntersecting
      if (_vis && playing.value && !_fid) {
        _prev = null
        _fid = requestAnimationFrame(_tick)
      } else if (!_vis && _fid) {
        cancelAnimationFrame(_fid)
        _fid = null
        _prev = null
      }
    }, { threshold: 0.1 })
    _obs.observe(el)
  }

  onUnmounted(() => {
    pause()
    _cbs.clear()
    if (_obs) _obs.disconnect()
  })

  if (autoplay) nextTick(play)

  return {
    playing: readonly(playing),
    speed: readonly(speed),
    currentTime: readonly(currentTime),
    play,
    pause,
    setSpeed,
    seek,
    onFrame,
    observe,
  }
}

export function provideFlowAnimation(a) {
  provide(FLOW_KEY, a)
}

export function injectFlowAnimation() {
  return inject(FLOW_KEY, null)
}
