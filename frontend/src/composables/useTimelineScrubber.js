import { ref, computed, watch, onUnmounted, provide, inject } from 'vue'

const TIMELINE_SCRUBBER_KEY = Symbol('timelineScrubber')

export function useTimelineScrubber(polling) {
  const currentRound = ref(0)
  const isPlaying = ref(false)
  const playbackSpeed = ref(1)
  const isLive = ref(true)
  let playbackTimer = null

  const totalRounds = computed(() => polling.runStatus.value?.total_rounds ?? 0)
  const liveRound = computed(() => polling.runStatus.value?.current_round ?? 0)
  const isCompleted = computed(() => polling.simStatus.value === 'completed')
  const isRunning = computed(() => polling.simStatus.value === 'running')
  const hasData = computed(() => (polling.timeline.value?.length ?? 0) > 0)

  const position = computed(() => {
    if (totalRounds.value === 0) return 0
    return currentRound.value / totalRounds.value
  })

  const roundData = computed(() =>
    polling.timeline.value?.find(r => r.round_num === currentRound.value) ?? null,
  )

  // Derive notable events from timeline data for markers
  const events = computed(() => {
    const tl = polling.timeline.value || []
    if (!tl.length) return []

    const avgActions = tl.reduce(
      (sum, r) => sum + (r.twitter_actions || 0) + (r.reddit_actions || 0), 0,
    ) / tl.length
    const result = []

    for (const round of tl) {
      const total = (round.twitter_actions || 0) + (round.reddit_actions || 0)
      if (total > avgActions * 1.5) {
        result.push({
          round: round.round_num,
          type: 'spike',
          label: `High activity: ${total} actions`,
        })
      }
    }

    if (tl.length > 0) {
      result.push({ round: tl[0].round_num, type: 'milestone', label: 'Simulation start' })
      if (isCompleted.value) {
        result.push({
          round: tl[tl.length - 1].round_num,
          type: 'milestone',
          label: 'Simulation end',
        })
      }
    }

    return result
  })

  // In live mode, track the simulation head
  watch(liveRound, (round) => {
    if (isLive.value && round > 0) {
      currentRound.value = round
    }
  })

  // Auto-enter live mode when simulation starts running
  watch(isRunning, (running) => {
    if (running && currentRound.value === 0) {
      isLive.value = true
    }
  })

  function seek(round) {
    const clamped = Math.max(0, Math.min(round, totalRounds.value))
    currentRound.value = clamped
    if (clamped < liveRound.value && isRunning.value) {
      isLive.value = false
    } else if (clamped >= liveRound.value) {
      isLive.value = true
    }
  }

  function seekToPosition(pos) {
    seek(Math.round(pos * totalRounds.value))
  }

  function stepForward() {
    seek(currentRound.value + 1)
  }

  function stepBack() {
    seek(currentRound.value - 1)
  }

  function goToLive() {
    isLive.value = true
    currentRound.value = liveRound.value
    pause()
  }

  function play() {
    if (!isCompleted.value && !isRunning.value) return
    if (!isCompleted.value) {
      goToLive()
      return
    }
    isPlaying.value = true
    isLive.value = false
    if (currentRound.value >= totalRounds.value) {
      currentRound.value = 0
    }
    startPlayback()
  }

  function pause() {
    isPlaying.value = false
    stopPlayback()
  }

  function togglePlay() {
    isPlaying.value ? pause() : play()
  }

  function setSpeed(speed) {
    playbackSpeed.value = speed
    if (isPlaying.value) {
      stopPlayback()
      startPlayback()
    }
  }

  function startPlayback() {
    stopPlayback()
    const interval = 1000 / playbackSpeed.value
    playbackTimer = setInterval(() => {
      if (currentRound.value >= totalRounds.value) {
        pause()
        return
      }
      currentRound.value++
    }, interval)
  }

  function stopPlayback() {
    if (playbackTimer) {
      clearInterval(playbackTimer)
      playbackTimer = null
    }
  }

  onUnmounted(stopPlayback)

  return {
    currentRound,
    totalRounds,
    liveRound,
    position,
    isPlaying,
    playbackSpeed,
    isLive,
    isCompleted,
    isRunning,
    hasData,
    roundData,
    events,
    seek,
    seekToPosition,
    stepForward,
    stepBack,
    goToLive,
    play,
    pause,
    togglePlay,
    setSpeed,
  }
}

export function provideTimelineScrubber(scrubber) {
  provide(TIMELINE_SCRUBBER_KEY, scrubber)
}

export function useTimelineScrubberInject() {
  return inject(TIMELINE_SCRUBBER_KEY, null)
}
