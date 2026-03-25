import { ref, computed, watch, toValue, onUnmounted } from 'vue'
import { batchGet } from '../api/batch'
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
      const res = await batchGet(`/graph/task/${taskId}`)
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
      const res = await batchGet(`/simulation/${taskId}/run-status`)
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
          totalRounds: json.data.total_rounds ?? 0,
          totalActions: json.data.total_actions_count ?? 0,
          twitterActions: json.data.twitter_actions_count ?? 0,
          redditActions: json.data.reddit_actions_count ?? 0,
          status: 'completed',
        })
      } else if (rs === 'failed') {
        simStatus.value = 'failed'
        errorMsg.value = json.data.error || 'Simulation failed'
        stopSimTimers()
        simStore.addSessionRun({ id: taskId, status: 'failed' })
      } else if (rs === 'running' || rs === 'starting' || rs === 'paused') {
        simStatus.value = 'running'
        simStore.addSessionRun({ id: taskId, status: 'running' })
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
      const res = await batchGet(`/simulation/${taskId}/run-status/detail`)
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
      const res = await batchGet(`/simulation/${taskId}/timeline`)
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

  function completeDemoRun() {
    const taskId = resolveTaskId()
    const demoActions = Math.floor(Math.random() * 300) + 150
    const demoRounds = Math.floor(Math.random() * 8) + 5
    const twitterShare = Math.floor(demoActions * 0.55)
    const redditShare = demoActions - twitterShare

    runStatus.value = {
      runner_status: 'completed',
      progress_percent: 100,
      current_round: demoRounds,
      total_rounds: demoRounds,
      total_actions_count: demoActions,
      twitter_actions_count: twitterShare,
      reddit_actions_count: redditShare,
    }
    simStatus.value = 'completed'
    stopSimTimers()

    simStore.updateProgress({ progress_percent: 100, current_round: demoRounds, total_rounds: demoRounds })
    simStore.updateMetrics({ total_actions_count: demoActions, twitter_actions_count: twitterShare, reddit_actions_count: redditShare })
    simStore.complete()
    simStore.addSessionRun({
      id: taskId,
      totalRounds: demoRounds,
      totalActions: demoActions,
      twitterActions: twitterShare,
      redditActions: redditShare,
    })

    // Generate demo activity data
    const agentNames = [
      'Sarah Chen, VP Support @ Acme SaaS',
      'James Wright, CX Director @ Retail Plus',
      'Robert Williams, IT Director @ EduSpark',
      'Michael Chang, Head of Ops @ FinEdge',
      'Anika Sharma, Head of Support Engineering @ DevStack',
      'Sofia Martinez, Support Manager @ QuickShip',
      'Rachel Torres, VP Support @ CloudOps Inc',
      'David Park, CX Lead @ HealthFirst',
      'Emily Watson, IT Manager @ DataPulse',
      'Carlos Rivera, Director of Operations @ NovaPay',
    ]
    const actionTypes = [
      'CREATE_POST', 'REPLY', 'LIKE', 'REPOST', 'COMMENT',
      'UPVOTE', 'SHARE', 'CREATE_THREAD',
    ]
    const platforms = ['twitter', 'reddit']
    const sampleContent = [
      'The ROI claims are compelling but I need to see case studies from our vertical before recommending to the board.',
      'Has anyone actually migrated from Zendesk to Intercom? What was the timeline like?',
      'AI-first resolution sounds great in theory. Concerned about edge cases our team handles daily.',
      'Just saw the Fin AI demo — the intent understanding is genuinely impressive.',
      '40% cost reduction is bold. We spend $15K/mo on Zendesk, so that would be significant.',
      'Our IT team would need 3 months minimum for any migration. The "30 days" claim feels aggressive.',
      'Shared this with our CX team. The personalization capabilities are worth evaluating.',
      'Interesting that they position against Zendesk directly. Shows confidence in the product.',
      'We tested Freshdesk last quarter. If Intercom can beat that experience, I am interested.',
      'The compliance angle is missing from their messaging. Critical for our healthcare clients.',
      'Liked this thread — good comparison of support platforms for mid-market.',
      'Our support costs went up 60% last year. Open to alternatives that can scale better.',
      'The AI agent concept is the future. Question is whether Fin is production-ready today.',
      'Reposting — our ops team should see the pricing comparison data.',
      'Support automation has been on our roadmap for Q3. This timeline could work.',
    ]

    const demoActionsList = []
    for (let round = 1; round <= demoRounds; round++) {
      const actionsInRound = Math.floor(Math.random() * 8) + 3
      for (let j = 0; j < actionsInRound; j++) {
        demoActionsList.push({
          agent_id: Math.floor(Math.random() * agentNames.length),
          agent_name: agentNames[Math.floor(Math.random() * agentNames.length)],
          action_type: actionTypes[Math.floor(Math.random() * actionTypes.length)],
          platform: platforms[Math.floor(Math.random() * platforms.length)],
          round_num: round,
          action_args: {
            content: sampleContent[Math.floor(Math.random() * sampleContent.length)],
          },
        })
      }
    }
    recentActions.value = demoActionsList

    // Generate demo timeline
    const demoTimeline = []
    for (let round = 1; round <= demoRounds; round++) {
      const roundActions = demoActionsList.filter(a => a.round_num === round)
      demoTimeline.push({
        round_num: round,
        twitter_actions: roundActions.filter(a => a.platform === 'twitter').length,
        reddit_actions: roundActions.filter(a => a.platform === 'reddit').length,
      })
    }
    timeline.value = demoTimeline
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
    completeDemoRun,
    forceRefresh,
  }
}
