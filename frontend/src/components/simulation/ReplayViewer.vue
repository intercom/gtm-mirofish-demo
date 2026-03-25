<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useReplay } from '../../composables/useReplay'
import LoadingSpinner from '../ui/LoadingSpinner.vue'
import ErrorState from '../ui/ErrorState.vue'

const props = defineProps({
  taskId: { type: String, required: true },
})

const replay = useReplay()
const timelineRef = ref(null)
const feedContainer = ref(null)
let resizeObserver = null
let resizeTimer = null

const platformFilter = ref('all')

const filteredActions = computed(() => {
  const actions = replay.currentRound.value?.actions || []
  if (platformFilter.value === 'all') return actions
  return actions.filter(a => a.platform === platformFilter.value)
})

function actionIcon(type) {
  const t = (type || '').toUpperCase()
  if (t.includes('CREATE_POST') || t.includes('POST')) return '\u270D'
  if (t.includes('LIKE') || t.includes('UPVOTE')) return '\u2764'
  if (t.includes('REPLY') || t.includes('COMMENT')) return '\u{1F4AC}'
  if (t.includes('REPOST') || t.includes('RETWEET') || t.includes('SHARE')) return '\u{1F501}'
  return '\u26A1'
}

function actionLabel(type) {
  const t = (type || '').toUpperCase()
  if (t.includes('CREATE_POST')) return 'Post'
  if (t.includes('LIKE')) return 'Like'
  if (t.includes('UPVOTE')) return 'Upvote'
  if (t.includes('REPLY')) return 'Reply'
  if (t.includes('COMMENT')) return 'Comment'
  if (t.includes('REPOST') || t.includes('RETWEET')) return 'Repost'
  if (t.includes('SHARE')) return 'Share'
  return type
}

function platformColor(platform) {
  return platform === 'twitter' ? '#2068FF' : '#ff5600'
}

// --- D3 activity timeline ---

function clearTimeline() {
  if (timelineRef.value) d3.select(timelineRef.value).selectAll('*').remove()
}

function renderTimeline() {
  clearTimeline()
  const container = timelineRef.value
  if (!container) return
  const data = replay.activityData.value
  if (!data.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 8, right: 12, bottom: 24, left: 32 }
  const width = containerWidth - margin.left - margin.right
  const height = 100
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleBand()
    .domain(data.map(d => d.round))
    .range([0, width])
    .padding(0.3)

  const maxVal = d3.max(data, d => d.total) || 1
  const y = d3.scaleLinear()
    .domain([0, maxVal])
    .range([height, 0])

  // Bars — stacked twitter/reddit
  g.selectAll('.bar-twitter')
    .data(data)
    .join('rect')
    .attr('x', d => x(d.round))
    .attr('y', d => y(d.twitter + d.reddit))
    .attr('width', x.bandwidth())
    .attr('height', d => height - y(d.twitter))
    .attr('fill', d => d.round === replay.currentRoundNum.value ? '#2068FF' : 'rgba(32,104,255,0.35)')
    .attr('rx', 2)

  g.selectAll('.bar-reddit')
    .data(data)
    .join('rect')
    .attr('x', d => x(d.round))
    .attr('y', d => y(d.reddit))
    .attr('width', x.bandwidth())
    .attr('height', d => height - y(d.reddit))
    .attr('fill', d => d.round === replay.currentRoundNum.value ? '#ff5600' : 'rgba(255,86,0,0.35)')
    .attr('rx', 2)

  // X-axis labels (show subset to avoid crowding)
  const step = Math.max(1, Math.floor(data.length / 10))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.round) + x.bandwidth() / 2)
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => `R${d.round}`)

  // Y-axis label
  g.append('text')
    .attr('x', -6)
    .attr('y', 0)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(maxVal)

  g.append('text')
    .attr('x', -6)
    .attr('y', height)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text('0')

  // Playhead line
  const currentData = data.find(d => d.round === replay.currentRoundNum.value)
  if (currentData) {
    const cx = x(currentData.round) + x.bandwidth() / 2
    g.append('line')
      .attr('x1', cx).attr('x2', cx)
      .attr('y1', -4).attr('y2', height + 4)
      .attr('stroke', '#2068FF')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '3,2')
  }

  // Click handler to seek
  svg.on('click', (event) => {
    const [mx] = d3.pointer(event, g.node())
    for (let i = 0; i < data.length; i++) {
      const bx = x(data[i].round)
      if (mx >= bx && mx <= bx + x.bandwidth()) {
        replay.seekTo(i)
        return
      }
    }
    // Approximate nearest
    const idx = Math.round((mx / width) * (data.length - 1))
    replay.seekTo(Math.max(0, Math.min(idx, data.length - 1)))
  })

  svg.style('cursor', 'pointer')
}

watch(
  [() => replay.activityData.value.length, () => replay.currentRoundNum.value],
  () => nextTick(renderTimeline),
)

onMounted(async () => {
  await replay.fetchReplay(props.taskId)
  nextTick(renderTimeline)

  if (timelineRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderTimeline, 200)
    })
    resizeObserver.observe(timelineRef.value)
  }
})

onUnmounted(() => {
  replay.pause()
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})

// Keyboard shortcuts
function onKeydown(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
  if (e.key === ' ' || e.key === 'k') { e.preventDefault(); replay.togglePlay() }
  else if (e.key === 'ArrowRight' || e.key === 'l') replay.stepForward()
  else if (e.key === 'ArrowLeft' || e.key === 'j') replay.stepBackward()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- Loading -->
    <div v-if="replay.loading.value" class="flex items-center justify-center py-20">
      <LoadingSpinner label="Loading replay data..." />
    </div>

    <!-- Error -->
    <ErrorState
      v-else-if="replay.error.value"
      :message="replay.error.value"
      @retry="replay.fetchReplay(props.taskId)"
    />

    <!-- Replay content -->
    <template v-else-if="replay.rounds.value.length > 0">
      <!-- Demo banner -->
      <div
        v-if="replay.isDemo.value"
        class="bg-[rgba(32,104,255,0.06)] border border-[#2068FF]/20 rounded-lg px-4 py-2 text-xs text-[#2068FF] font-medium"
      >
        Demo Mode — Showing synthetic replay data
      </div>

      <!-- Header metrics -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
          <div class="text-xs text-[var(--color-text-muted)]">Round</div>
          <div class="text-lg font-semibold text-[var(--color-text)]">
            {{ replay.currentRoundNum.value }}
            <span class="text-xs font-normal text-[var(--color-text-muted)]">/ {{ replay.totalRounds.value }}</span>
          </div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
          <div class="text-xs text-[var(--color-text-muted)]">Actions so far</div>
          <div class="text-lg font-semibold text-[var(--color-text)]">{{ replay.cumulativeMetrics.value.totalActions }}</div>
        </div>
        <div class="bg-[rgba(32,104,255,0.06)] border border-[#2068FF]/10 rounded-lg px-4 py-3">
          <div class="text-xs text-[#2068FF]">Twitter</div>
          <div class="text-lg font-semibold text-[var(--color-text)]">{{ replay.cumulativeMetrics.value.twitterActions }}</div>
        </div>
        <div class="bg-[rgba(255,86,0,0.06)] border border-[#ff5600]/10 rounded-lg px-4 py-3">
          <div class="text-xs text-[#ff5600]">Reddit</div>
          <div class="text-lg font-semibold text-[var(--color-text)]">{{ replay.cumulativeMetrics.value.redditActions }}</div>
        </div>
      </div>

      <!-- Activity timeline chart -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-[var(--color-text)]">Activity Timeline</h3>
          <div class="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
            <span class="flex items-center gap-1.5">
              <span class="inline-block w-2.5 h-2.5 rounded-sm bg-[#2068FF]" /> Twitter
            </span>
            <span class="flex items-center gap-1.5">
              <span class="inline-block w-2.5 h-2.5 rounded-sm bg-[#ff5600]" /> Reddit
            </span>
          </div>
        </div>
        <div ref="timelineRef" class="w-full" style="height: 132px" />
      </div>

      <!-- Playback controls -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="flex items-center gap-3">
          <!-- Step backward -->
          <button
            @click="replay.stepBackward()"
            :disabled="replay.currentRoundIndex.value === 0"
            class="p-1.5 rounded-md text-[var(--color-text-secondary)] hover:text-[#2068FF] hover:bg-[rgba(32,104,255,0.08)] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            title="Previous round (←)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
            </svg>
          </button>

          <!-- Play / pause -->
          <button
            @click="replay.togglePlay()"
            class="w-9 h-9 flex items-center justify-center rounded-full bg-[#2068FF] hover:bg-[#1a5ae0] text-white transition-colors"
            :title="replay.isPlaying.value ? 'Pause (Space)' : 'Play (Space)'"
          >
            <!-- Pause icon -->
            <svg v-if="replay.isPlaying.value" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="4" width="4" height="16" rx="1" />
              <rect x="14" y="4" width="4" height="16" rx="1" />
            </svg>
            <!-- Play icon -->
            <svg v-else class="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5.14v14.72a1 1 0 0 0 1.5.86l11-7.36a1 1 0 0 0 0-1.72l-11-7.36A1 1 0 0 0 8 5.14z" />
            </svg>
          </button>

          <!-- Step forward -->
          <button
            @click="replay.stepForward()"
            :disabled="replay.currentRoundIndex.value >= replay.rounds.value.length - 1"
            class="p-1.5 rounded-md text-[var(--color-text-secondary)] hover:text-[#2068FF] hover:bg-[rgba(32,104,255,0.08)] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            title="Next round (→)"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
            </svg>
          </button>

          <!-- Progress bar -->
          <div class="flex-1 mx-2">
            <input
              type="range"
              :min="0"
              :max="Math.max(0, replay.rounds.value.length - 1)"
              :value="replay.currentRoundIndex.value"
              @input="replay.seekTo(Number($event.target.value))"
              class="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-[#2068FF] bg-[var(--color-border)]"
            />
          </div>

          <!-- Speed -->
          <button
            @click="replay.cycleSpeed()"
            class="text-xs font-semibold px-2.5 py-1 rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF] transition-colors tabular-nums min-w-[3rem] text-center"
            title="Change playback speed"
          >
            {{ replay.speed.value }}x
          </button>
        </div>

        <!-- Keyboard hint -->
        <div class="mt-2 text-[10px] text-[var(--color-text-muted)] text-center">
          Space: play/pause &middot; ←/→: step &middot; Click timeline to seek
        </div>
      </div>

      <!-- Round actions feed -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg">
        <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)]">
          <h3 class="text-sm font-semibold text-[var(--color-text)]">
            Round {{ replay.currentRoundNum.value }} Actions
            <span class="text-xs font-normal text-[var(--color-text-muted)] ml-1">
              ({{ filteredActions.length }})
            </span>
          </h3>
          <div class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
            <button
              v-for="tab in [{key:'all',label:'All'},{key:'twitter',label:'Twitter'},{key:'reddit',label:'Reddit'}]"
              :key="tab.key"
              @click="platformFilter = tab.key"
              class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
              :class="platformFilter === tab.key
                ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>

        <div
          ref="feedContainer"
          class="max-h-[360px] overflow-y-auto divide-y divide-[var(--color-border)]"
        >
          <div
            v-for="(action, idx) in filteredActions"
            :key="`${action.round_num}-${idx}`"
            class="flex items-start gap-3 px-4 py-3 hover:bg-[var(--color-tint)] transition-colors"
          >
            <!-- Platform dot -->
            <div
              class="w-2 h-2 rounded-full mt-1.5 shrink-0"
              :style="{ backgroundColor: platformColor(action.platform) }"
            />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 text-sm">
                <span class="font-medium text-[var(--color-text)]">{{ action.agent_name }}</span>
                <span class="text-xs text-[var(--color-text-muted)]">
                  {{ actionIcon(action.action_type) }} {{ actionLabel(action.action_type) }}
                </span>
                <span class="text-[10px] font-medium px-1.5 py-0.5 rounded-full border"
                  :class="action.platform === 'twitter'
                    ? 'bg-[rgba(32,104,255,0.06)] text-[#2068FF] border-[#2068FF]/15'
                    : 'bg-[rgba(255,86,0,0.06)] text-[#ff5600] border-[#ff5600]/15'"
                >
                  {{ action.platform }}
                </span>
              </div>
              <p
                v-if="action.action_args?.content"
                class="text-xs text-[var(--color-text-secondary)] mt-1 line-clamp-2"
              >
                {{ action.action_args.content }}
              </p>
            </div>
          </div>

          <!-- Empty state for current round -->
          <div
            v-if="filteredActions.length === 0"
            class="flex items-center justify-center py-10 text-sm text-[var(--color-text-muted)]"
          >
            No actions in this round
          </div>
        </div>
      </div>
    </template>

    <!-- No data -->
    <div v-else class="text-center py-16">
      <div class="w-14 h-14 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mx-auto mb-4">
        <svg class="w-6 h-6 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
        </svg>
      </div>
      <h2 class="text-base font-semibold text-[var(--color-text)] mb-1">No replay data</h2>
      <p class="text-sm text-[var(--color-text-secondary)]">
        Run a simulation first, then come back to replay it.
      </p>
    </div>
  </div>
</template>
