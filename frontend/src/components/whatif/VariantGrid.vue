<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  variants: { type: Array, default: () => [] },
  baseVariant: { type: Object, default: null },
  targetMetric: { type: String, default: null },
  targetDirection: {
    type: String,
    default: 'higher',
    validator: (v) => ['higher', 'lower'].includes(v),
  },
})

const emit = defineEmits(['select-variant'])

const THRESHOLD = 0.05

const COLORS = {
  better: '#009900',
  betterBg: 'rgba(0, 153, 0, 0.08)',
  worse: '#ef4444',
  worseBg: 'rgba(239, 68, 68, 0.08)',
  similar: 'var(--color-text, #1a1a1a)',
  similarBg: 'transparent',
  best: 'rgba(0, 153, 0, 0.14)',
  sparkline: '#2068FF',
}

// --- Demo data fallback ---

const DEMO_METRICS = ['open_rate', 'reply_rate', 'conversion_rate', 'spam_rate']

const DEMO_BASE = {
  id: 'base',
  name: 'Base Scenario',
  parameter: '—',
  value: '—',
  metrics: {
    open_rate: { current: 32.1, history: [28, 29, 30, 31, 31.5, 32, 32.1] },
    reply_rate: { current: 8.4, history: [6, 7, 7.5, 8, 8.2, 8.3, 8.4] },
    conversion_rate: { current: 3.2, history: [2, 2.5, 2.8, 3, 3.1, 3.15, 3.2] },
    spam_rate: { current: 4.8, history: [5.5, 5.2, 5, 4.9, 4.85, 4.82, 4.8] },
  },
}

const DEMO_VARIANTS = [
  {
    id: 'v1',
    name: 'Aggressive Subject Line',
    parameter: 'subject_tone',
    value: 'urgent',
    metrics: {
      open_rate: { current: 38.7, history: [30, 33, 35, 37, 38, 38.5, 38.7] },
      reply_rate: { current: 6.1, history: [7, 6.8, 6.5, 6.3, 6.2, 6.1, 6.1] },
      conversion_rate: { current: 2.8, history: [2.5, 2.6, 2.7, 2.75, 2.78, 2.8, 2.8] },
      spam_rate: { current: 9.2, history: [5, 6, 7, 8, 8.5, 9, 9.2] },
    },
  },
  {
    id: 'v2',
    name: 'Personalized Intro',
    parameter: 'personalization',
    value: 'company_pain_point',
    metrics: {
      open_rate: { current: 35.4, history: [29, 30, 32, 33, 34, 35, 35.4] },
      reply_rate: { current: 12.1, history: [7, 8, 9, 10, 11, 11.8, 12.1] },
      conversion_rate: { current: 5.1, history: [2.5, 3, 3.5, 4, 4.5, 4.9, 5.1] },
      spam_rate: { current: 3.1, history: [5, 4.5, 4, 3.8, 3.5, 3.2, 3.1] },
    },
  },
  {
    id: 'v3',
    name: 'Short Copy (< 80 words)',
    parameter: 'body_length',
    value: '75_words',
    metrics: {
      open_rate: { current: 33.0, history: [30, 31, 31.5, 32, 32.5, 33, 33] },
      reply_rate: { current: 9.8, history: [7, 7.5, 8, 8.5, 9, 9.5, 9.8] },
      conversion_rate: { current: 3.5, history: [2.8, 3, 3.1, 3.2, 3.3, 3.4, 3.5] },
      spam_rate: { current: 4.5, history: [5, 4.9, 4.8, 4.7, 4.6, 4.55, 4.5] },
    },
  },
  {
    id: 'v4',
    name: 'Social Proof CTA',
    parameter: 'cta_style',
    value: 'peer_reference',
    metrics: {
      open_rate: { current: 31.8, history: [30, 30.5, 31, 31.2, 31.5, 31.7, 31.8] },
      reply_rate: { current: 10.2, history: [7, 8, 8.5, 9, 9.5, 10, 10.2] },
      conversion_rate: { current: 4.4, history: [2.5, 3, 3.5, 3.8, 4, 4.2, 4.4] },
      spam_rate: { current: 3.9, history: [5, 4.8, 4.5, 4.3, 4.1, 4, 3.9] },
    },
  },
]

// --- Resolved data (props or demo fallback) ---

const resolvedBase = computed(() => props.baseVariant || DEMO_BASE)
const resolvedVariants = computed(() =>
  props.variants.length ? props.variants : DEMO_VARIANTS,
)

const metricKeys = computed(() => {
  const base = resolvedBase.value
  if (base?.metrics) return Object.keys(base.metrics)
  return DEMO_METRICS
})

const resolvedTarget = computed(() => props.targetMetric || metricKeys.value[2] || null)

// --- Sorting ---

const sortKey = ref(null)
const sortDir = ref('desc')

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'desc'
  }
}

const sortedVariants = computed(() => {
  const list = [...resolvedVariants.value]
  if (!sortKey.value) return list

  return list.sort((a, b) => {
    let aVal, bVal

    if (sortKey.value === 'name') {
      aVal = a.name || ''
      bVal = b.name || ''
      return sortDir.value === 'asc'
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal)
    }

    if (sortKey.value === 'parameter') {
      aVal = a.parameter || ''
      bVal = b.parameter || ''
      return sortDir.value === 'asc'
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal)
    }

    // Metric column
    aVal = a.metrics?.[sortKey.value]?.current ?? 0
    bVal = b.metrics?.[sortKey.value]?.current ?? 0
    return sortDir.value === 'asc' ? aVal - bVal : bVal - aVal
  })
})

// --- Best variant detection ---

const bestVariantId = computed(() => {
  const target = resolvedTarget.value
  if (!target) return null

  const variants = resolvedVariants.value
  if (!variants.length) return null

  let best = null
  let bestVal = props.targetDirection === 'higher' ? -Infinity : Infinity

  for (const v of variants) {
    const val = v.metrics?.[target]?.current
    if (val == null) continue
    if (props.targetDirection === 'higher' ? val > bestVal : val < bestVal) {
      bestVal = val
      best = v.id
    }
  }
  return best
})

// --- Cell coloring ---

function cellComparison(metricKey, variantMetrics) {
  const baseVal = resolvedBase.value?.metrics?.[metricKey]?.current
  const varVal = variantMetrics?.[metricKey]?.current
  if (baseVal == null || varVal == null || baseVal === 0) return 'similar'

  const pctChange = (varVal - baseVal) / Math.abs(baseVal)

  // For "bad" metrics like spam_rate, lower is better
  const lowerIsBetter = metricKey.includes('spam') || metricKey.includes('churn') || metricKey.includes('bounce')
  const isImprovement = lowerIsBetter ? pctChange < -THRESHOLD : pctChange > THRESHOLD
  const isDegradation = lowerIsBetter ? pctChange > THRESHOLD : pctChange < -THRESHOLD

  if (isImprovement) return 'better'
  if (isDegradation) return 'worse'
  return 'similar'
}

function cellStyle(comparison) {
  return {
    color: COLORS[comparison],
    backgroundColor: comparison === 'better' ? COLORS.betterBg : comparison === 'worse' ? COLORS.worseBg : COLORS.similarBg,
  }
}

function formatDelta(metricKey, variantMetrics) {
  const baseVal = resolvedBase.value?.metrics?.[metricKey]?.current
  const varVal = variantMetrics?.[metricKey]?.current
  if (baseVal == null || varVal == null) return ''

  const diff = varVal - baseVal
  const sign = diff > 0 ? '+' : ''
  return `${sign}${diff.toFixed(1)}`
}

function formatMetricLabel(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatValue(val) {
  if (val == null) return '—'
  return typeof val === 'number' ? val.toFixed(1) : String(val)
}

// --- Sparklines via D3 ---

const sparklineRefs = ref({})

function setSparklineRef(variantId, metricKey, el) {
  if (el) {
    const key = `${variantId}__${metricKey}`
    sparklineRefs.value[key] = el
  }
}

function renderSparklines() {
  const base = resolvedBase.value
  const allVariants = [base, ...resolvedVariants.value].filter(Boolean)

  for (const variant of allVariants) {
    for (const metricKey of metricKeys.value) {
      const refKey = `${variant.id}__${metricKey}`
      const el = sparklineRefs.value[refKey]
      if (!el) continue

      const history = variant.metrics?.[metricKey]?.history
      if (!history || !history.length) continue

      d3.select(el).selectAll('*').remove()

      const w = 60
      const h = 20

      const svg = d3.select(el)
        .append('svg')
        .attr('width', w)
        .attr('height', h)
        .attr('viewBox', `0 0 ${w} ${h}`)

      const x = d3.scaleLinear()
        .domain([0, history.length - 1])
        .range([1, w - 1])

      const y = d3.scaleLinear()
        .domain(d3.extent(history))
        .range([h - 2, 2])

      const line = d3.line()
        .x((_, i) => x(i))
        .y((d) => y(d))
        .curve(d3.curveMonotoneX)

      const comparison = variant.id === base?.id ? 'similar' : cellComparison(metricKey, variant.metrics)
      const strokeColor = comparison === 'better' ? COLORS.better : comparison === 'worse' ? COLORS.worse : COLORS.sparkline

      svg.append('path')
        .datum(history)
        .attr('d', line)
        .attr('fill', 'none')
        .attr('stroke', strokeColor)
        .attr('stroke-width', 1.5)
        .attr('stroke-linecap', 'round')
    }
  }
}

watch([sortedVariants, resolvedBase], () => {
  nextTick(renderSparklines)
}, { deep: true })

onMounted(() => {
  nextTick(renderSparklines)
})
</script>

<template>
  <div class="bg-[var(--color-surface,#fff)] border border-[var(--color-border,rgba(0,0,0,0.1))] rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="px-5 py-4 border-b border-[var(--color-border,rgba(0,0,0,0.1))]">
      <h3 class="text-sm font-semibold text-[var(--color-text,#050505)]">Variant Comparison</h3>
      <p class="text-xs text-[var(--color-text-muted,#888)] mt-0.5">
        Color-coded against base scenario. Click a row for full results.
      </p>
    </div>

    <!-- Scrollable table -->
    <div class="overflow-x-auto">
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="bg-[var(--color-tint,rgba(0,0,0,0.02))]">
            <th
              class="sticky left-0 z-10 bg-[var(--color-tint,rgba(0,0,0,0.02))] text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary,#555)] cursor-pointer select-none hover:text-[var(--color-text,#050505)] transition-colors"
              @click="toggleSort('name')"
            >
              <span class="inline-flex items-center gap-1">
                Variant
                <span v-if="sortKey === 'name'" class="text-[10px]">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
              </span>
            </th>
            <th
              class="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary,#555)] cursor-pointer select-none hover:text-[var(--color-text,#050505)] transition-colors whitespace-nowrap"
              @click="toggleSort('parameter')"
            >
              <span class="inline-flex items-center gap-1">
                Parameter
                <span v-if="sortKey === 'parameter'" class="text-[10px]">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
              </span>
            </th>
            <th class="text-left px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary,#555)] whitespace-nowrap">
              Value
            </th>
            <th
              v-for="mk in metricKeys"
              :key="mk"
              class="text-right px-4 py-2.5 text-xs font-semibold text-[var(--color-text-secondary,#555)] cursor-pointer select-none hover:text-[var(--color-text,#050505)] transition-colors whitespace-nowrap"
              :class="{ 'underline decoration-dotted underline-offset-4': mk === resolvedTarget }"
              @click="toggleSort(mk)"
            >
              <span class="inline-flex items-center justify-end gap-1">
                {{ formatMetricLabel(mk) }}
                <span v-if="sortKey === mk" class="text-[10px]">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <!-- Base scenario summary row -->
          <tr class="border-b border-[var(--color-border,rgba(0,0,0,0.1))] bg-[var(--color-tint,rgba(0,0,0,0.02))]">
            <td class="sticky left-0 z-10 bg-[var(--color-tint,rgba(0,0,0,0.02))] px-4 py-2.5 font-medium text-[var(--color-text-secondary,#555)] whitespace-nowrap">
              <div class="flex items-center gap-2">
                <span class="inline-block w-1.5 h-1.5 rounded-full bg-[#2068FF]" />
                {{ resolvedBase?.name || 'Base' }}
              </div>
            </td>
            <td class="px-4 py-2.5 text-[var(--color-text-muted,#888)]">{{ resolvedBase?.parameter || '—' }}</td>
            <td class="px-4 py-2.5 text-[var(--color-text-muted,#888)]">{{ resolvedBase?.value || '—' }}</td>
            <td
              v-for="mk in metricKeys"
              :key="mk"
              class="px-4 py-2.5 text-right text-[var(--color-text-secondary,#555)] font-medium whitespace-nowrap"
            >
              <div class="flex items-center justify-end gap-2">
                <div :ref="(el) => setSparklineRef(resolvedBase?.id || 'base', mk, el)" class="shrink-0" />
                <span>{{ formatValue(resolvedBase?.metrics?.[mk]?.current) }}</span>
              </div>
            </td>
          </tr>

          <!-- Variant rows -->
          <tr
            v-for="variant in sortedVariants"
            :key="variant.id"
            class="border-b border-[var(--color-border,rgba(0,0,0,0.1))] cursor-pointer transition-colors hover:bg-[var(--color-primary-light,rgba(32,104,255,0.04))]"
            :class="{ 'ring-1 ring-inset ring-[#009900]/30': variant.id === bestVariantId }"
            :style="variant.id === bestVariantId ? { backgroundColor: COLORS.best } : {}"
            @click="emit('select-variant', variant)"
          >
            <td class="sticky left-0 z-10 px-4 py-2.5 font-medium text-[var(--color-text,#050505)] whitespace-nowrap"
              :style="variant.id === bestVariantId ? { backgroundColor: COLORS.best } : { backgroundColor: 'var(--color-surface, #fff)' }"
            >
              <div class="flex items-center gap-2">
                <span
                  v-if="variant.id === bestVariantId"
                  class="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-[#009900]"
                >
                  <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1l2.1 4.3 4.7.7-3.4 3.3.8 4.7L8 11.8 3.8 14l.8-4.7L1.2 6l4.7-.7z"/></svg>
                  Best
                </span>
                <span>{{ variant.name }}</span>
              </div>
            </td>
            <td class="px-4 py-2.5 text-[var(--color-text-secondary,#555)] whitespace-nowrap">
              <code class="text-xs bg-[var(--color-tint,rgba(0,0,0,0.04))] px-1.5 py-0.5 rounded">{{ variant.parameter }}</code>
            </td>
            <td class="px-4 py-2.5 text-[var(--color-text-secondary,#555)] whitespace-nowrap">
              {{ variant.value }}
            </td>
            <td
              v-for="mk in metricKeys"
              :key="mk"
              class="px-4 py-2.5 text-right whitespace-nowrap"
              :style="cellStyle(cellComparison(mk, variant.metrics))"
            >
              <div class="flex items-center justify-end gap-2">
                <div :ref="(el) => setSparklineRef(variant.id, mk, el)" class="shrink-0" />
                <span class="font-medium">{{ formatValue(variant.metrics?.[mk]?.current) }}</span>
                <span class="text-[11px] opacity-75">{{ formatDelta(mk, variant.metrics) }}</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty state -->
    <div
      v-if="!sortedVariants.length && !resolvedBase"
      class="flex items-center justify-center py-12 text-sm text-[var(--color-text-muted,#888)]"
    >
      No variants to compare. Run a what-if analysis to generate variants.
    </div>

    <!-- Legend -->
    <div class="flex items-center gap-5 px-5 py-3 border-t border-[var(--color-border,rgba(0,0,0,0.1))] text-[11px] text-[var(--color-text-muted,#888)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" :style="{ backgroundColor: COLORS.betterBg, border: '1px solid rgba(0,153,0,0.2)' }" />
        Better than base
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm" :style="{ backgroundColor: COLORS.worseBg, border: '1px solid rgba(239,68,68,0.2)' }" />
        Worse than base
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm border border-[var(--color-border,rgba(0,0,0,0.1))]" />
        Similar (within 5%)
      </span>
      <span class="flex items-center gap-1.5 ml-auto">
        <svg width="12" height="12" viewBox="0 0 16 16" fill="#009900"><path d="M8 1l2.1 4.3 4.7.7-3.4 3.3.8 4.7L8 11.8 3.8 14l.8-4.7L1.2 6l4.7-.7z"/></svg>
        Best variant
      </span>
    </div>
  </div>
</template>
