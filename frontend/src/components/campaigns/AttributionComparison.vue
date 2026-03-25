<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import * as d3 from 'd3'
import { fetchAttributionComparison } from '../../api/campaigns'

const loading = ref(true)
const error = ref(null)
const campaigns = ref([])
const models = ref([])
const modelDescriptions = ref({})
const attribution = ref({})
const recommendation = ref(null)

const selectedCampaign = ref(null)
const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  text: '#050505',
}

const MODEL_COLORS = {
  first_touch: COLORS.primary,
  last_touch: COLORS.orange,
  linear: COLORS.green,
  time_decay: COLORS.purple,
  position_based: '#888',
}

const MODEL_LABELS = {
  first_touch: 'First Touch',
  last_touch: 'Last Touch',
  linear: 'Linear',
  time_decay: 'Time Decay',
  position_based: 'Position Based',
}

const DISAGREE_THRESHOLD = 12

function cellClass(campaignId, model) {
  const credits = attribution.value[campaignId]
  if (!credits) return ''
  const values = Object.values(credits)
  const val = credits[model]
  const max = Math.max(...values)
  const min = Math.min(...values)
  if (val === max && max - min >= DISAGREE_THRESHOLD) return 'bg-[#2068FF]/10 font-semibold text-[#2068FF]'
  if (val === min && max - min >= DISAGREE_THRESHOLD) return 'bg-[#ff5600]/10 font-semibold text-[#ff5600]'
  return ''
}

const chartData = computed(() => {
  const camp = selectedCampaign.value
  if (!camp || !attribution.value[camp.id]) return []
  const credits = attribution.value[camp.id]
  return models.value.map(m => ({
    model: m,
    label: MODEL_LABELS[m],
    credit: credits[m],
    revenue: Math.round(camp.total_revenue * credits[m] / 100),
  }))
})

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const data = chartData.value
  if (!data.length || !chartRef.value) return

  const container = chartRef.value
  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 24, bottom: 40, left: 64 }
  const width = containerWidth - margin.left - margin.right
  const height = 220
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text(`Revenue by Model — ${selectedCampaign.value.name}`)

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('How each attribution model distributes this campaign\'s revenue')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleBand()
    .domain(data.map(d => d.label))
    .range([0, width])
    .padding(0.3)

  const maxVal = d3.max(data, d => d.revenue)
  const y = d3.scaleLinear()
    .domain([0, maxVal * 1.15])
    .range([height, 0])

  const yTicks = y.ticks(5)
  g.selectAll('.grid-line')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => `$${d3.format(',.0f')(d)}`)

  g.selectAll('.bar')
    .data(data)
    .join('rect')
    .attr('x', d => x(d.label))
    .attr('y', height)
    .attr('width', x.bandwidth())
    .attr('height', 0)
    .attr('rx', 4)
    .attr('fill', d => MODEL_COLORS[d.model])
    .attr('opacity', 0.85)
    .transition()
    .duration(600)
    .delay((d, i) => i * 80)
    .ease(d3.easeCubicOut)
    .attr('y', d => y(d.revenue))
    .attr('height', d => height - y(d.revenue))

  g.selectAll('.bar-value')
    .data(data)
    .join('text')
    .attr('x', d => x(d.label) + x.bandwidth() / 2)
    .attr('y', d => y(d.revenue) - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .attr('fill', d => MODEL_COLORS[d.model])
    .style('opacity', 0)
    .text(d => `$${d3.format(',.0f')(d.revenue)}`)
    .transition()
    .duration(300)
    .delay((d, i) => 600 + i * 80)
    .style('opacity', 1)

  g.selectAll('.x-label')
    .data(data)
    .join('text')
    .attr('x', d => x(d.label) + x.bandwidth() / 2)
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text(d => d.label)
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const res = await fetchAttributionComparison()
    const d = res.data.data
    campaigns.value = d.campaigns
    models.value = d.models
    modelDescriptions.value = d.model_descriptions
    attribution.value = d.attribution
    recommendation.value = d.recommendation
    if (d.campaigns.length) selectedCampaign.value = d.campaigns[0]
  } catch (e) {
    error.value = e.message || 'Failed to load attribution data'
  } finally {
    loading.value = false
  }
}

watch(selectedCampaign, () => {
  nextTick(() => renderChart())
})

onMounted(async () => {
  await loadData()
  await nextTick()
  renderChart()

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => renderChart(), 200)
  })
  if (chartRef.value) resizeObserver.observe(chartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="space-y-6">
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="h-6 w-6 border-2 border-[#2068FF] border-t-transparent rounded-full animate-spin" />
      <span class="ml-3 text-[var(--color-text-muted)] text-sm">Loading attribution data…</span>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-[#ff5600]/5 border border-[#ff5600]/20 rounded-lg p-4 text-sm text-[#ff5600]">
      {{ error }}
    </div>

    <template v-else>
      <!-- Attribution Comparison Table -->
      <div class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)]"
           style="box-shadow: var(--card-shadow)">
        <div class="p-5 border-b border-[var(--card-border)]">
          <h3 class="text-sm font-semibold text-[var(--color-text)]">Attribution Model Comparison</h3>
          <p class="text-xs text-[var(--color-text-muted)] mt-1">
            Credit percentage assigned to each campaign by different attribution models.
            <span class="text-[#2068FF]">Blue</span> = highest credit,
            <span class="text-[#ff5600]">orange</span> = lowest ({{ DISAGREE_THRESHOLD }}pp+ spread).
          </p>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-[var(--card-border)]">
                <th class="text-left px-4 py-3 text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">
                  Campaign
                </th>
                <th v-for="m in models" :key="m"
                    class="text-right px-4 py-3 text-xs font-medium uppercase tracking-wider"
                    :style="{ color: MODEL_COLORS[m] }">
                  {{ MODEL_LABELS[m] }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="camp in campaigns" :key="camp.id"
                  class="border-b border-[var(--card-border)] last:border-b-0 hover:bg-[var(--color-surface)] cursor-pointer transition-colors"
                  :class="{ 'bg-[#2068FF]/5': selectedCampaign?.id === camp.id }"
                  @click="selectedCampaign = camp">
                <td class="px-4 py-3 font-medium text-[var(--color-text)] whitespace-nowrap">
                  {{ camp.name }}
                  <span class="ml-2 text-xs text-[var(--color-text-muted)]">
                    ${{ (camp.total_revenue / 1000).toFixed(0) }}k
                  </span>
                </td>
                <td v-for="m in models" :key="m"
                    class="text-right px-4 py-3 tabular-nums transition-colors"
                    :class="cellClass(camp.id, m)">
                  {{ attribution[camp.id]?.[m]?.toFixed(1) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Bar Chart: Revenue by Model -->
      <div class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] p-5"
           style="box-shadow: var(--card-shadow)">
        <div ref="chartRef" class="w-full" />
      </div>

      <!-- Model Explanations -->
      <div class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] p-5"
           style="box-shadow: var(--card-shadow)">
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">How Each Model Works</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-for="m in models" :key="m"
               class="flex items-start gap-2 text-xs text-[var(--color-text-secondary)]">
            <span class="mt-0.5 w-2 h-2 rounded-full shrink-0" :style="{ backgroundColor: MODEL_COLORS[m] }" />
            <div>
              <span class="font-medium text-[var(--color-text)]">{{ MODEL_LABELS[m] }}</span>
              <p class="mt-0.5 leading-relaxed">{{ modelDescriptions[m] }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Recommendation -->
      <div v-if="recommendation"
           class="bg-[#2068FF]/5 border border-[#2068FF]/20 rounded-lg p-4">
        <div class="flex items-start gap-2">
          <svg class="w-4 h-4 mt-0.5 text-[#2068FF] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          <div class="text-sm">
            <p class="font-semibold text-[#2068FF]">
              Recommended: {{ MODEL_LABELS[recommendation.model] }}
            </p>
            <p class="text-[var(--color-text-secondary)] mt-1 text-xs leading-relaxed">
              {{ recommendation.reason }}
            </p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
