<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { reportApi } from '../../api/report'

const props = defineProps({
  reportId: { type: String, required: true },
  isGenerating: { type: Boolean, default: false },
})

const logs = ref([])
const loading = ref(true)
const error = ref(null)
const expandedSteps = ref(new Set())
let pollTimer = null

const STEP_TYPES = {
  react_thought: { label: 'Thought', color: '#2068FF', icon: '💭', bg: 'rgba(32,104,255,0.08)' },
  tool_call: { label: 'Action', color: '#AA00FF', icon: '⚡', bg: 'rgba(170,0,255,0.08)' },
  tool_result: { label: 'Observation', color: '#009900', icon: '👁', bg: 'rgba(0,153,0,0.08)' },
  llm_response: { label: 'LLM Response', color: '#ff5600', icon: '🤖', bg: 'rgba(255,86,0,0.08)' },
  planning_start: { label: 'Planning', color: '#2068FF', icon: '📋', bg: 'rgba(32,104,255,0.08)' },
  planning_context: { label: 'Context', color: '#2068FF', icon: '📊', bg: 'rgba(32,104,255,0.08)' },
  planning_complete: { label: 'Plan Ready', color: '#009900', icon: '✅', bg: 'rgba(0,153,0,0.08)' },
  report_start: { label: 'Start', color: '#050505', icon: '🚀', bg: 'rgba(5,5,5,0.08)' },
  section_start: { label: 'Section', color: '#2068FF', icon: '📝', bg: 'rgba(32,104,255,0.08)' },
  section_content: { label: 'Content', color: '#009900', icon: '✏️', bg: 'rgba(0,153,0,0.08)' },
  section_complete: { label: 'Complete', color: '#009900', icon: '✅', bg: 'rgba(0,153,0,0.08)' },
  report_complete: { label: 'Done', color: '#009900', icon: '🎉', bg: 'rgba(0,153,0,0.08)' },
}

const summary = computed(() => {
  const toolCalls = logs.value.filter(l => l.action === 'tool_call')
  const sections = logs.value.filter(l => l.action === 'section_start')
  const lastLog = logs.value[logs.value.length - 1]
  const elapsed = lastLog?.elapsed_seconds || 0

  const toolBreakdown = {}
  for (const tc of toolCalls) {
    const name = tc.details?.tool_name || 'unknown'
    toolBreakdown[name] = (toolBreakdown[name] || 0) + 1
  }

  return {
    totalToolCalls: toolCalls.length,
    totalSections: sections.length,
    elapsedSeconds: elapsed,
    toolBreakdown,
  }
})

const reactSteps = computed(() => {
  const steps = []
  let currentSection = null

  for (const log of logs.value) {
    if (log.action === 'section_start') {
      currentSection = log.section_title
    }

    const meta = STEP_TYPES[log.action]
    if (!meta) continue

    steps.push({
      id: steps.length,
      action: log.action,
      label: meta.label,
      color: meta.color,
      icon: meta.icon,
      bg: meta.bg,
      section: log.section_title || currentSection,
      elapsed: log.elapsed_seconds,
      iteration: log.details?.iteration,
      details: log.details,
    })
  }

  return steps
})

function toggleStep(id) {
  if (expandedSteps.value.has(id)) {
    expandedSteps.value.delete(id)
  } else {
    expandedSteps.value.add(id)
  }
  // Force reactivity
  expandedSteps.value = new Set(expandedSteps.value)
}

function formatElapsed(seconds) {
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const mins = Math.floor(seconds / 60)
  const secs = (seconds % 60).toFixed(0)
  return `${mins}m ${secs}s`
}

function formatToolName(name) {
  return (name || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function getStepSummary(step) {
  const d = step.details
  if (!d) return ''

  switch (step.action) {
    case 'react_thought':
      return d.thought ? truncate(d.thought, 120) : ''
    case 'tool_call':
      return `${formatToolName(d.tool_name)}(${summarizeParams(d.parameters)})`
    case 'tool_result':
      return `${formatToolName(d.tool_name)} → ${d.result_length || 0} chars`
    case 'llm_response':
      return d.has_final_answer ? 'Final answer generated' : `Iteration ${d.iteration || '?'}`
    case 'planning_complete':
      return d.outline?.sections
        ? `${d.outline.sections.length} sections planned`
        : 'Outline ready'
    case 'section_start':
      return d.message || step.section || ''
    default:
      return d.message || ''
  }
}

function getStepDetail(step) {
  const d = step.details
  if (!d) return null

  switch (step.action) {
    case 'react_thought':
      return d.thought || null
    case 'tool_call':
      return d.parameters ? JSON.stringify(d.parameters, null, 2) : null
    case 'tool_result':
      return d.result || null
    case 'llm_response':
      return d.response ? truncate(d.response, 2000) : null
    case 'planning_context':
      return d.context ? JSON.stringify(d.context, null, 2) : null
    case 'planning_complete':
      return d.outline ? JSON.stringify(d.outline, null, 2) : null
    default:
      return null
  }
}

function truncate(str, max) {
  if (!str || str.length <= max) return str
  return str.slice(0, max) + '…'
}

function summarizeParams(params) {
  if (!params) return ''
  const keys = Object.keys(params)
  if (keys.length === 0) return ''
  const first = params[keys[0]]
  const val = typeof first === 'string' ? truncate(first, 40) : JSON.stringify(first)
  return keys.length === 1 ? `"${val}"` : `"${val}", +${keys.length - 1}`
}

async function fetchLogs() {
  try {
    const { data: res } = await reportApi.getAgentLogStream(props.reportId)
    if (res.success) {
      logs.value = res.data.logs || []
    }
  } catch (e) {
    if (!logs.value.length) {
      error.value = e.message || 'Failed to load agent log'
    }
  } finally {
    loading.value = false
  }
}

function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(fetchLogs, 3000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

watch(() => props.isGenerating, (gen) => {
  if (gen) startPolling()
  else stopPolling()
}, { immediate: true })

onMounted(fetchLogs)
onUnmounted(stopPolling)
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
    <!-- Header with summary stats -->
    <div class="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="text-sm font-semibold text-[var(--color-text)]">Agent Reasoning Log</span>
        <span
          v-if="isGenerating"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-[rgba(32,104,255,0.1)] text-[#2068FF]"
        >
          <span class="w-1.5 h-1.5 rounded-full bg-[#2068FF] animate-pulse" />
          Live
        </span>
      </div>
      <div v-if="!loading && logs.length" class="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
        <span class="flex items-center gap-1">
          <span class="font-semibold text-[#AA00FF]">{{ summary.totalToolCalls }}</span> tool calls
        </span>
        <span class="flex items-center gap-1">
          <span class="font-semibold text-[#2068FF]">{{ summary.totalSections }}</span> sections
        </span>
        <span class="flex items-center gap-1">
          ⏱ {{ formatElapsed(summary.elapsedSeconds) }}
        </span>
      </div>
    </div>

    <!-- Tool breakdown bar -->
    <div v-if="!loading && Object.keys(summary.toolBreakdown).length" class="px-4 py-2 border-b border-[var(--color-border)] flex flex-wrap gap-2">
      <span
        v-for="(count, tool) in summary.toolBreakdown"
        :key="tool"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-[rgba(170,0,255,0.08)] text-[#AA00FF]"
      >
        {{ formatToolName(tool) }} × {{ count }}
      </span>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="flex flex-col items-center gap-2">
        <div class="w-6 h-6 rounded-full border-2 border-[#2068FF] border-t-transparent animate-spin" />
        <span class="text-xs text-[var(--color-text-muted)]">Loading agent log...</span>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="px-4 py-8 text-center">
      <p class="text-sm text-[var(--color-text-muted)]">{{ error }}</p>
      <button @click="fetchLogs" class="mt-2 text-xs text-[#2068FF] hover:underline">Retry</button>
    </div>

    <!-- Empty state -->
    <div v-else-if="!reactSteps.length" class="px-4 py-8 text-center">
      <p class="text-sm text-[var(--color-text-muted)]">No reasoning steps recorded yet.</p>
    </div>

    <!-- ReACT step timeline -->
    <div v-else class="max-h-[600px] overflow-y-auto">
      <div class="px-4 py-3 space-y-0">
        <div
          v-for="step in reactSteps"
          :key="step.id"
          class="relative pl-6 pb-3 last:pb-0"
        >
          <!-- Timeline connector -->
          <div
            class="absolute left-[9px] top-5 bottom-0 w-px"
            :style="{ backgroundColor: step.color + '33' }"
          />

          <!-- Timeline dot -->
          <div
            class="absolute left-0 top-1 w-[18px] h-[18px] rounded-full flex items-center justify-center text-[10px] border-2 bg-[var(--color-surface)]"
            :style="{ borderColor: step.color }"
          >
            {{ step.icon }}
          </div>

          <!-- Step card -->
          <div
            class="rounded-lg border transition-colors cursor-pointer"
            :style="{ borderColor: step.color + '33', backgroundColor: step.bg }"
            @click="getStepDetail(step) && toggleStep(step.id)"
          >
            <div class="px-3 py-2 flex items-center gap-2 min-w-0">
              <!-- Type badge -->
              <span
                class="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide text-white"
                :style="{ backgroundColor: step.color }"
              >
                {{ step.label }}
              </span>

              <!-- Summary text -->
              <span class="text-xs text-[var(--color-text-secondary)] truncate flex-1 min-w-0">
                {{ getStepSummary(step) }}
              </span>

              <!-- Timing -->
              <span class="shrink-0 text-[10px] text-[var(--color-text-muted)] tabular-nums">
                {{ formatElapsed(step.elapsed) }}
              </span>

              <!-- Expand indicator -->
              <span
                v-if="getStepDetail(step)"
                class="shrink-0 text-[10px] text-[var(--color-text-muted)] transition-transform"
                :class="expandedSteps.has(step.id) ? 'rotate-90' : ''"
              >▶</span>
            </div>

            <!-- Expanded detail -->
            <div
              v-if="expandedSteps.has(step.id) && getStepDetail(step)"
              class="px-3 pb-2"
            >
              <pre class="text-[11px] font-mono text-[var(--color-text-secondary)] whitespace-pre-wrap break-all max-h-[300px] overflow-y-auto bg-[var(--color-bg)] rounded p-2 border border-[var(--color-border)]">{{ getStepDetail(step) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
