<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  runs: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['select-run'])

const currentMonth = ref(new Date())
const selectedDate = ref(null)

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

const monthLabel = computed(() =>
  d3.timeFormat('%B %Y')(currentMonth.value),
)

const runsByDate = computed(() => {
  const map = new Map()
  for (const run of props.runs) {
    const key = d3.timeFormat('%Y-%m-%d')(new Date(run.timestamp))
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(run)
  }
  return map
})

const calendarDays = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  const startOffset = firstDay.getDay()
  const days = []

  // Previous month padding
  for (let i = startOffset - 1; i >= 0; i--) {
    const d = new Date(year, month, -i)
    days.push({ date: d, key: d3.timeFormat('%Y-%m-%d')(d), outside: true })
  }

  // Current month
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const d = new Date(year, month, i)
    days.push({ date: d, key: d3.timeFormat('%Y-%m-%d')(d), outside: false })
  }

  // Next month padding to fill final row
  const remaining = 7 - (days.length % 7)
  if (remaining < 7) {
    for (let i = 1; i <= remaining; i++) {
      const d = new Date(year, month + 1, i)
      days.push({ date: d, key: d3.timeFormat('%Y-%m-%d')(d), outside: true })
    }
  }

  return days
})

const todayKey = computed(() =>
  d3.timeFormat('%Y-%m-%d')(new Date()),
)

const maxRunsInDay = computed(() => {
  let max = 0
  for (const [, runs] of runsByDate.value) {
    if (runs.length > max) max = runs.length
  }
  return max
})

const intensityScale = computed(() =>
  d3.scaleLinear()
    .domain([0, Math.max(maxRunsInDay.value, 1)])
    .range([0, 1]),
)

const selectedDayRuns = computed(() => {
  if (!selectedDate.value) return []
  return runsByDate.value.get(selectedDate.value) || []
})

function prevMonth() {
  const d = new Date(currentMonth.value)
  d.setMonth(d.getMonth() - 1)
  currentMonth.value = d
  selectedDate.value = null
}

function nextMonth() {
  const d = new Date(currentMonth.value)
  d.setMonth(d.getMonth() + 1)
  currentMonth.value = d
  selectedDate.value = null
}

function goToToday() {
  currentMonth.value = new Date()
  selectedDate.value = todayKey.value
}

function selectDay(day) {
  if (day.outside) return
  selectedDate.value = selectedDate.value === day.key ? null : day.key
}

function dayRunCount(day) {
  return runsByDate.value.get(day.key)?.length || 0
}

function dayIntensityStyle(day) {
  const count = dayRunCount(day)
  if (count === 0) return {}
  const alpha = 0.12 + intensityScale.value(count) * 0.3
  return { backgroundColor: `rgba(32, 104, 255, ${alpha})` }
}

function normalizeStatus(status) {
  if (!status) return 'completed'
  const s = status.toLowerCase()
  if (s === 'completed' || s === 'complete') return 'completed'
  if (s === 'failed' || s === 'error') return 'failed'
  return 'in_progress'
}

function statusDotClass(status) {
  const s = normalizeStatus(status)
  if (s === 'completed') return 'bg-emerald-500'
  if (s === 'failed') return 'bg-red-500'
  return 'bg-[#2068FF]'
}

function formatRunTime(ts) {
  return d3.timeFormat('%-I:%M %p')(new Date(ts))
}

function formatRunDate(ts) {
  return d3.timeFormat('%b %-d, %Y')(new Date(ts))
}

function onRunClick(run) {
  emit('select-run', run)
}

// Navigate to month of most recent run on mount
onMounted(() => {
  if (props.runs.length > 0) {
    const latest = props.runs.reduce((a, b) =>
      (b.timestamp || 0) > (a.timestamp || 0) ? b : a,
    )
    if (latest.timestamp) {
      currentMonth.value = new Date(latest.timestamp)
    }
  }
})
</script>

<template>
  <div class="scenario-calendar">
    <!-- Calendar header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <h3 class="text-base font-semibold text-[var(--color-text)]">{{ monthLabel }}</h3>
        <button
          @click="goToToday"
          class="text-[10px] font-medium px-2 py-0.5 rounded-full border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[#2068FF] hover:border-[#2068FF]/40 transition-colors"
        >
          Today
        </button>
      </div>
      <div class="flex items-center gap-1">
        <button
          @click="prevMonth"
          class="p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-tint)] transition-colors"
          aria-label="Previous month"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
          </svg>
        </button>
        <button
          @click="nextMonth"
          class="p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-tint)] transition-colors"
          aria-label="Next month"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Weekday headers -->
    <div class="grid grid-cols-7 mb-1">
      <div
        v-for="day in WEEKDAYS"
        :key="day"
        class="text-center text-[10px] font-medium text-[var(--color-text-muted)] py-1"
      >
        {{ day }}
      </div>
    </div>

    <!-- Calendar grid -->
    <div class="grid grid-cols-7 gap-px bg-[var(--color-border)] rounded-lg overflow-hidden">
      <button
        v-for="day in calendarDays"
        :key="day.key"
        @click="selectDay(day)"
        class="relative bg-[var(--color-surface)] min-h-[56px] p-1.5 text-left transition-colors"
        :class="{
          'hover:bg-[var(--color-tint)]': !day.outside,
          'opacity-40 cursor-default': day.outside,
          'cursor-pointer': !day.outside,
          'ring-2 ring-[#2068FF] ring-inset z-10': selectedDate === day.key,
        }"
        :style="!day.outside ? dayIntensityStyle(day) : {}"
        :disabled="day.outside"
      >
        <span
          class="text-xs font-medium block leading-none"
          :class="{
            'text-[var(--color-text)]': !day.outside,
            'text-[var(--color-text-muted)]': day.outside,
          }"
        >
          <span
            v-if="day.key === todayKey"
            class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-[#2068FF] text-white text-[10px] font-semibold"
          >
            {{ day.date.getDate() }}
          </span>
          <span v-else>{{ day.date.getDate() }}</span>
        </span>

        <!-- Run dots -->
        <div v-if="dayRunCount(day) > 0" class="flex flex-wrap gap-0.5 mt-1.5">
          <span
            v-for="(run, i) in (runsByDate.get(day.key) || []).slice(0, 4)"
            :key="i"
            class="w-1.5 h-1.5 rounded-full"
            :class="statusDotClass(run.status)"
          />
          <span
            v-if="dayRunCount(day) > 4"
            class="text-[8px] text-[var(--color-text-muted)] leading-none self-center ml-0.5"
          >
            +{{ dayRunCount(day) - 4 }}
          </span>
        </div>
      </button>
    </div>

    <!-- Selected day detail panel -->
    <transition name="slide-up">
      <div
        v-if="selectedDate && selectedDayRuns.length > 0"
        class="mt-4 border border-[var(--color-border)] bg-[var(--color-surface)] rounded-lg overflow-hidden"
      >
        <div class="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
          <span class="text-xs font-semibold text-[var(--color-text)]">
            {{ formatRunDate(selectedDayRuns[0].timestamp) }}
          </span>
          <span class="text-[10px] font-medium text-[#2068FF] bg-[rgba(32,104,255,0.08)] px-2 py-0.5 rounded-full">
            {{ selectedDayRuns.length }} run{{ selectedDayRuns.length === 1 ? '' : 's' }}
          </span>
        </div>
        <div class="divide-y divide-[var(--color-border)]">
          <button
            v-for="run in selectedDayRuns"
            :key="run.id"
            @click="onRunClick(run)"
            class="w-full text-left px-4 py-3 hover:bg-[var(--color-tint)] transition-colors flex items-center gap-3"
          >
            <span class="w-2 h-2 rounded-full shrink-0" :class="statusDotClass(run.status)" />
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-[var(--color-text)] truncate">
                {{ run.scenarioName || 'Untitled Scenario' }}
              </div>
              <div class="text-xs text-[var(--color-text-muted)] mt-0.5">
                {{ formatRunTime(run.timestamp) }}
                <span v-if="run.totalActions" class="mx-1">·</span>
                <span v-if="run.totalActions">{{ run.totalActions }} actions</span>
                <span v-if="run.agentCount" class="mx-1">·</span>
                <span v-if="run.agentCount">{{ run.agentCount }} agents</span>
              </div>
            </div>
            <svg class="w-4 h-4 text-[var(--color-text-muted)] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
            </svg>
          </button>
        </div>
      </div>
    </transition>

    <!-- Empty selected day -->
    <transition name="slide-up">
      <div
        v-if="selectedDate && selectedDayRuns.length === 0"
        class="mt-4 border border-[var(--color-border)] bg-[var(--color-surface)] rounded-lg px-4 py-6 text-center"
      >
        <p class="text-xs text-[var(--color-text-muted)]">No simulations on this day</p>
      </div>
    </transition>

    <!-- Legend -->
    <div class="flex items-center gap-4 mt-4 text-[10px] text-[var(--color-text-muted)]">
      <div class="flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-emerald-500" />
        Completed
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-[#2068FF]" />
        In Progress
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-red-500" />
        Failed
      </div>
    </div>
  </div>
</template>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.2s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
