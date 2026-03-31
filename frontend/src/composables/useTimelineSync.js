import { inject, provide, ref, readonly, computed } from 'vue'

// Injection keys — shared contract between timeline providers and consumers
export const TIMELINE_POSITION = Symbol('timeline-position')
export const TIMELINE_RANGE = Symbol('timeline-range')
export const TIMELINE_SET_POSITION = Symbol('timeline-set-position')
export const TIMELINE_PLAYING = Symbol('timeline-playing')

/**
 * Provide timeline state for descendant components (e.g. SyncedChart).
 * Called by a timeline controller such as TimelineScrubber.
 */
export function provideTimelineSync(options = {}) {
  const position = ref(options.initialPosition ?? 0)
  const range = ref(options.range ?? { start: 0, end: 1 })
  const playing = ref(false)

  function setPosition(value) {
    position.value = Math.max(range.value.start, Math.min(range.value.end, value))
  }

  provide(TIMELINE_POSITION, readonly(position))
  provide(TIMELINE_RANGE, readonly(range))
  provide(TIMELINE_SET_POSITION, setPosition)
  provide(TIMELINE_PLAYING, readonly(playing))

  return { position, range, playing, setPosition }
}

/**
 * Consume timeline state from a parent provider.
 * Falls back to standalone local state when no provider exists,
 * so SyncedChart works even without a TimelineScrubber ancestor.
 */
export function useTimelineSync() {
  const fallbackPosition = ref(0)
  const fallbackRange = ref({ start: 0, end: 1 })
  const fallbackPlaying = ref(false)
  const fallbackSetPosition = (v) => { fallbackPosition.value = Math.max(0, Math.min(1, v)) }

  const position = inject(TIMELINE_POSITION, fallbackPosition)
  const range = inject(TIMELINE_RANGE, fallbackRange)
  const setPosition = inject(TIMELINE_SET_POSITION, fallbackSetPosition)
  const playing = inject(TIMELINE_PLAYING, fallbackPlaying)

  const connected = computed(() => position !== fallbackPosition)

  return { position, range, setPosition, playing, connected }
}
