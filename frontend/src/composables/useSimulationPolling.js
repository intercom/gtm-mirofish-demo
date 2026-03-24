import { ref, computed, watch, toValue, onUnmounted } from 'vue'
import client, { API_BASE } from '../api/client'
import { graphApi } from '../api/graph'
import { useSimulationStore } from '../stores/simulation'

export function useSimulationPolling(taskIdSource) {
  const simStore = useSimulationStore()

  // --- Graph state ---
  const graphTask = ref(null)
  const graphStatus = ref('building') // 'building' | 'complete' | 'failed'
  const graphProgress = ref(0)
  const graphData = ref({ nodes: [], edges: [] })
  const graphId = ref(null)

  // --- Simulation state ---
  const runStatus = ref(null)
  const simStatus = ref('idle') // 'idle' | 'building' | 'running' | 'completed' | 'failed'
  const recentActions = ref([])
  const timeline = ref([])

  // --- Error / fallback ---
  const errorMsg = ref('')
  const isDemoFallback = ref(false)

  // --- Timers ---
  let graphTimer = null
  let runStatusTimer = null
  let detailTimer = null
  let timelineTimer = null

  // --- Computed ---
  const overallPhase = computed(() => {
    if (graphStatus.value === 'failed' || simStatus.value === 'failed') return 'failed'
    if (simStatus.value === 'completed') return 'complete'
    if (simStatus.value === 'running' || simStatus.value === 'building') return 'running_simulation'
    if (graphStatus.value === 'building') return 'building_graph'
    if (graphStatus.value === 'complete') return 'running_simulation'
    return 'building_graph'
  })

  // --- Helpers ---
  function resolveTaskId() {
    return toValue(taskIdSource)
  }

  function clearTimer(timerRef) {
    if (timerRef) clearInterval(timerRef)
    return null
  }

  // --- Graph polling ---
  async function fetchGraphTask() {
    const taskId = resolveTaskId()
    if (!taskId) return

    try {
      const res = await graphApi.getTask(taskId)
      const json = res.data
      if (!json.success) {
        errorMsg.value = json.error || 'Unknown error'
        return
      }

      graphTask.value = json.data
      graphProgress.value = json.data.progress || 0

      if (json.data.status === 'completed') {
        graphStatus.value = 'complete'
        graphTimer = clearTimer(graphTimer)
        const gid = json.data.result?.graph_id
        if (gid) {
          graphId.value = gid
          await fetchGraphData(gid)
        }
      } else if (json.data.status === 'failed') {
        graphStatus.value = 'failed'
        errorMsg.value = json.data.message || 'Build failed'
        graphTimer = clearTimer(graphTimer)
      } else {
        graphStatus.value = 'building'
      }
    } catch (err) {
      // Distinguish network errors from task-not-found
      const isNetworkError = !err.status || err.status === 0
      if (isNetworkError) {
        isDemoFallback.value = true
        graphTimer = clearTimer(graphTimer)
      } else {
        errorMsg.value = err.message || 'Failed to poll graph task'
      }
    }
  }

  async function fetchGraphData(gid) {
    try {
      const res = await graphApi.getData(gid)
      if (res.data?.success) {
        const data = res.data.data
        graphData.value = {
          nodes: data.nodes || [],
          edges: data.edges || [],
          node_count: data.node_count || data.nodes?.length || 0,
          edge_count: data.edge_count || data.edges?.length || 0,
        }
      }
    } catch (err) {
      errorMsg.value = err.message || 'Failed to load graph data'
    }
  }

  // --- Simulation run-status polling ---
  async function fetchRunStatus() {
    const taskId = resolveTaskId()
    if (!taskId) return

    try {
      const res = await client.get(`/simulation/${taskId}/run-status`)
      const json = res.data
      if (!json.success) return

      runStatus.value = json.data

      simStore.updateProgress({
        progress_percent: json.data.progress_percent,
        current_round: json.data.current_round,
        total_rounds: json.data.total_rounds,
      })
      simStore.updateMetrics({
        total_actions_count: json.data.total_actions_count,
        twitter_actions_count: json.data.twitter_actions_count,
        reddit_actions_count: json.data.reddit_actions_count,
      })

      const rs = json.data.runner_status
      if (rs === 'completed' || rs === 'stopped') {
        simStatus.value = 'completed'
        stopSimTimers()
        simStore.complete()
        simStore.addSessionRun({
          id: taskId,
          scenarioName: 'GTM Simulation',
          totalRounds: json.data.total_rounds ?? 0,
          totalActions: json.data.total_actions_count ?? 0,
          twitterActions: json.data.twitter_actions_count ?? 0,
          redditActions: json.data.reddit_actions_count ?? 0,
        })
      } else if (rs === 'failed') {
        simStatus.value = 'failed'
        errorMsg.value = json.data.error || 'Simulation failed'
        stopSimTimers()
      } else if (rs === 'running' || rs === 'starting' || rs === 'paused') {
        simStatus.value = 'running'
        ensureDetailPolling()
      } else if (rs === 'idle') {
        simStatus.value = 'building'
      }
    } catch {
      // Non-critical — run status just won't update this cycle
    }
  }

  // --- Detail polling ---
  async function fetchDetail() {
    const taskId = resolveTaskId()
    if (!taskId) return

    try {
      const res = await client.get(`/simulation/${taskId}/run-status/detail`)
      const json = res.data
      if (json.success) {
        recentActions.value = json.data.recent_actions || json.data.all_actions || []
      }
    } catch {
      // Non-critical
    }
  }

  // --- Timeline polling ---
  async function fetchTimeline() {
    const taskId = resolveTaskId()
    if (!taskId) return

    try {
      const res = await client.get(`/simulation/${taskId}/timeline`)
      const json = res.data
      if (json.success) {
        timeline.value = json.data.timeline || []
      }
    } catch {
      // Non-critical
    }
  }

  // --- Timer management ---
  function ensureDetailPolling() {
    if (!detailTimer) {
      fetchDetail()
      detailTimer = setInterval(fetchDetail, 5000)
    }
    if (!timelineTimer) {
      fetchTimeline()
      timelineTimer = setInterval(fetchTimeline, 5000)
    }
  }

  function stopSimTimers() {
    runStatusTimer = clearTimer(runStatusTimer)
    detailTimer = clearTimer(detailTimer)
    timelineTimer = clearTimer(timelineTimer)
  }

  // --- Public methods ---
  function start() {
    stop()

    fetchGraphTask()
    graphTimer = setInterval(fetchGraphTask, 2000)

    fetchRunStatus()
    runStatusTimer = setInterval(fetchRunStatus, 3000)
  }

  function stop() {
    graphTimer = clearTimer(graphTimer)
    stopSimTimers()
  }

  function setGraphData(data) {
    graphData.value = {
      nodes: data.nodes || [],
      edges: data.edges || [],
      node_count: data.node_count || data.nodes?.length || 0,
      edge_count: data.edge_count || data.edges?.length || 0,
    }
    graphStatus.value = 'complete'
    graphTimer = clearTimer(graphTimer)
  }

  async function forceRefresh() {
    const promises = [fetchGraphTask(), fetchRunStatus(), fetchDetail(), fetchTimeline()]
    await Promise.allSettled(promises)
  }

  // Stop detail/timeline timers when sim completes or fails
  watch(simStatus, (val) => {
    if (val === 'completed' || val === 'failed') {
      fetchDetail()
      fetchTimeline()
      stopSimTimers()
    }
  })

  onUnmounted(stop)

  return {
    // Graph state
    graphTask,
    graphStatus,
    graphProgress,
    graphData,
    graphId,

    // Simulation state
    runStatus,
    simStatus,
    recentActions,
    timeline,

    // Derived
    overallPhase,
    errorMsg,
    isDemoFallback,

    // Methods
    start,
    stop,
    setGraphData,
    forceRefresh,
  }
}
