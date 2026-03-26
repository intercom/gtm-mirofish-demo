import { ref, computed, watch, onUnmounted } from 'vue'
import { simulationApi } from '../api/simulation'

const SPEED_OPTIONS = [0.5, 1, 2, 4]

export function useReplay(taskIdSource) {
  const rounds = ref([])
  const agents = ref([])
  const totalRounds = ref(0)
  const totalActions = ref(0)
  const isDemo = ref(false)
  const loading = ref(false)
  const error = ref(null)

  // Playback state
  const currentRoundIndex = ref(0)
  const isPlaying = ref(false)
  const speedIndex = ref(1) // default 1x
  let playTimer = null

  const speed = computed(() => SPEED_OPTIONS[speedIndex.value])
  const intervalMs = computed(() => 1500 / speed.value)

  const currentRound = computed(() => rounds.value[currentRoundIndex.value] || null)
  const currentRoundNum = computed(() => currentRound.value?.round_num ?? 0)

  const progress = computed(() =>
    totalRounds.value > 0 ? ((currentRoundIndex.value + 1) / totalRounds.value) * 100 : 0,
  )

  // All actions up to and including current round
  const cumulativeActions = computed(() => {
    const result = []
    for (let i = 0; i <= currentRoundIndex.value && i < rounds.value.length; i++) {
      result.push(...rounds.value[i].actions)
    }
    return result
  })

  // Per-round cumulative metrics
  const cumulativeMetrics = computed(() => {
    let twitter = 0
    let reddit = 0
    let agentSet = new Set()
    for (let i = 0; i <= currentRoundIndex.value && i < rounds.value.length; i++) {
      const r = rounds.value[i]
      twitter += r.twitter_actions
      reddit += r.reddit_actions
      for (const a of r.active_agents) agentSet.add(a)
    }
    return {
      totalActions: twitter + reddit,
      twitterActions: twitter,
      redditActions: reddit,
      activeAgents: agentSet.size,
    }
  })

  // Activity per round for the timeline chart
  const activityData = computed(() =>
    rounds.value.map(r => ({
      round: r.round_num,
      total: r.total_actions,
      twitter: r.twitter_actions,
      reddit: r.reddit_actions,
      agents: r.active_agents.length,
    })),
  )

  async function fetchReplay(taskId) {
    if (!taskId) return
    loading.value = true
    error.value = null
    try {
      const res = await simulationApi.getReplay(taskId)
      const json = res.data
      if (!json.success) {
        error.value = json.error || 'Failed to load replay data'
        return
      }
      rounds.value = json.data.rounds
      agents.value = json.data.agents
      totalRounds.value = json.data.total_rounds
      totalActions.value = json.data.total_actions
      isDemo.value = json.demo ?? false
      currentRoundIndex.value = 0
    } catch (e) {
      error.value = e.message || 'Network error'
    } finally {
      loading.value = false
    }
  }

  function play() {
    if (rounds.value.length === 0) return
    // If at end, restart
    if (currentRoundIndex.value >= rounds.value.length - 1) {
      currentRoundIndex.value = 0
    }
    isPlaying.value = true
    scheduleNext()
  }

  function pause() {
    isPlaying.value = false
    clearTimeout(playTimer)
    playTimer = null
  }

  function togglePlay() {
    isPlaying.value ? pause() : play()
  }

  function stepForward() {
    pause()
    if (currentRoundIndex.value < rounds.value.length - 1) {
      currentRoundIndex.value++
    }
  }

  function stepBackward() {
    pause()
    if (currentRoundIndex.value > 0) {
      currentRoundIndex.value--
    }
  }

  function seekTo(index) {
    const wasPlaying = isPlaying.value
    pause()
    currentRoundIndex.value = Math.max(0, Math.min(index, rounds.value.length - 1))
    if (wasPlaying) play()
  }

  function cycleSpeed() {
    speedIndex.value = (speedIndex.value + 1) % SPEED_OPTIONS.length
    if (isPlaying.value) {
      clearTimeout(playTimer)
      scheduleNext()
    }
  }

  function scheduleNext() {
    playTimer = setTimeout(() => {
      if (!isPlaying.value) return
      if (currentRoundIndex.value < rounds.value.length - 1) {
        currentRoundIndex.value++
        scheduleNext()
      } else {
        isPlaying.value = false
      }
    }, intervalMs.value)
  }

  // Cleanup on unmount
  onUnmounted(() => {
    clearTimeout(playTimer)
  })

  return {
    rounds,
    agents,
    totalRounds,
    totalActions,
    isDemo,
    loading,
    error,
    currentRoundIndex,
    currentRound,
    currentRoundNum,
    isPlaying,
    speed,
    progress,
    cumulativeActions,
    cumulativeMetrics,
    activityData,
    speedOptions: SPEED_OPTIONS,
    fetchReplay,
    play,
    pause,
    togglePlay,
    stepForward,
    stepBackward,
    seekTo,
    cycleSpeed,
  }
}
