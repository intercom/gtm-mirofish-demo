<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  personality: {
    type: Object,
    default: () => ({
      analytical: 50,
      creative: 50,
      assertive: 50,
      empathetic: 50,
      riskTolerant: 50,
    }),
  },
  communicationStyle: {
    type: String,
    default: 'formal',
  },
})

const emit = defineEmits(['update:personality', 'update:communicationStyle'])

// --- Trait definitions ---

const traits = [
  { key: 'analytical', label: 'Analytical', icon: '🔬', color: '#2068FF' },
  { key: 'creative', label: 'Creative', icon: '🎨', color: '#AA00FF' },
  { key: 'assertive', label: 'Assertive', icon: '⚡', color: '#ff5600' },
  { key: 'empathetic', label: 'Empathetic', icon: '💙', color: '#009900' },
  { key: 'riskTolerant', label: 'Risk Tolerant', icon: '🎯', color: '#f59e0b' },
]

// --- Preset personalities ---

const presets = [
  {
    name: 'The Analyst',
    description: 'Data-driven decision maker',
    values: { analytical: 90, creative: 30, assertive: 40, empathetic: 35, riskTolerant: 25 },
  },
  {
    name: 'The Visionary',
    description: 'Forward-thinking innovator',
    values: { analytical: 35, creative: 95, assertive: 55, empathetic: 50, riskTolerant: 85 },
  },
  {
    name: 'The Leader',
    description: 'Decisive and commanding',
    values: { analytical: 55, creative: 45, assertive: 95, empathetic: 40, riskTolerant: 70 },
  },
  {
    name: 'The Mediator',
    description: 'Empathetic bridge builder',
    values: { analytical: 40, creative: 50, assertive: 25, empathetic: 95, riskTolerant: 30 },
  },
  {
    name: 'The Innovator',
    description: 'Bold risk taker',
    values: { analytical: 60, creative: 80, assertive: 60, empathetic: 35, riskTolerant: 95 },
  },
  {
    name: 'The Balanced',
    description: 'Well-rounded generalist',
    values: { analytical: 55, creative: 55, assertive: 55, empathetic: 55, riskTolerant: 55 },
  },
]

// --- Communication styles ---

const communicationStyles = [
  { value: 'formal', label: 'Formal', description: 'Structured communication with precise, professional language' },
  { value: 'casual', label: 'Casual', description: 'Conversational tone with approachable, friendly language' },
  { value: 'data_driven', label: 'Data-Driven', description: 'Numbers-focused with heavy emphasis on metrics and evidence' },
  { value: 'storytelling', label: 'Storytelling', description: 'Narrative-driven with anecdotes, analogies, and examples' },
  { value: 'diplomatic', label: 'Diplomatic', description: 'Measured, balanced approach that considers all perspectives' },
]

// --- Active preset detection ---

const activePreset = computed(() => {
  return presets.find((p) =>
    traits.every((t) => p.values[t.key] === props.personality[t.key])
  )?.name ?? null
})

// --- Trait update ---

function updateTrait(key, value) {
  emit('update:personality', { ...props.personality, [key]: Number(value) })
}

function applyPreset(preset) {
  emit('update:personality', { ...preset.values })
}

// --- Preview text generation ---

const previewText = computed(() => {
  const p = props.personality
  const style = props.communicationStyle

  const dominant = traits.reduce((max, t) =>
    p[t.key] > p[max.key] ? t : max
  , traits[0])

  const fragments = {
    formal: {
      analytical: "Based on our Q3 data analysis, the proposed integration demonstrates a 34% improvement in pipeline velocity. I'd recommend we proceed with a structured pilot before committing additional resources.",
      creative: "I see an opportunity to fundamentally rethink our approach here. What if we combined the onboarding flow with proactive outreach to create a seamless experience that differentiates us from the competition?",
      assertive: "We need to make a decision on this by end of week. The data supports moving forward, and further delays will cost us market position. I propose we commit to the enterprise tier immediately.",
      empathetic: "I understand the team has concerns about the timeline. Let me outline a phased approach that addresses both the urgency of our goals and the capacity constraints the engineering team has raised.",
      riskTolerant: "The market window is closing. I recommend we fast-track the launch with our MVP feature set and iterate post-release. The competitive advantage of being first outweighs the risk of minor gaps.",
    },
    casual: {
      analytical: "So I ran the numbers on this and honestly the results are pretty clear - we're looking at a 34% boost in pipeline velocity. Definitely worth a pilot run before we go all in.",
      creative: "Here's a wild idea - what if we flip the whole onboarding process on its head? Instead of the usual flow, we blend it with proactive outreach. Could be a real differentiator.",
      assertive: "Look, we've been going back and forth on this for too long. The numbers are there, the opportunity is there. Let's just pull the trigger on the enterprise tier and move forward.",
      empathetic: "Hey, I hear you on the timeline concerns. Totally valid. How about we break this into phases so we can hit our targets without burning out the engineering team?",
      riskTolerant: "The window's closing fast on this one. I say we ship the MVP now and polish later. Being first to market is worth way more than having every feature perfect.",
    },
    data_driven: {
      analytical: "Pipeline velocity is up 34% QoQ with the current integration. CAC decreased 12% while LTV grew 8%. These metrics support expanding the pilot. Recommend allocating 15% of Q4 budget.",
      creative: "Customer engagement scores show a 2.3x multiplier when onboarding includes proactive outreach. NPS jumps from 42 to 67. The data suggests a combined flow would yield measurable differentiation.",
      assertive: "Decision delay cost: $45K/week in lost pipeline. Win rate drops 3 points per week of delay. ROI on enterprise tier: 280% over 18 months. The numbers demand immediate action.",
      empathetic: "Team velocity has dropped 18% in the last sprint due to scope creep. A phased approach would restore throughput while maintaining 90% of our target delivery date.",
      riskTolerant: "First-mover advantage in this segment is worth ~$2.1M ARR based on competitive analysis. MVP covers 73% of use cases. Ship now, iterate with beta feedback.",
    },
    storytelling: {
      analytical: "Remember when we ran the Acme Corp pilot last quarter? The integration cut their pipeline review from 3 hours to 45 minutes. Now imagine that across our entire enterprise segment.",
      creative: "Think about the last time you signed up for a product and thought 'wow, they really get me.' That's what we can create. Not just onboarding — a welcome experience that tells a story.",
      assertive: "Last year we hesitated on the SMB expansion and watched Competitor X grab 30% of that market in six months. We can't afford to repeat that. This is our moment to lead.",
      empathetic: "I spoke with three people on the engineering team this week. They're not pushing back on the goal — they're worried about quality. A phased rollout gives them the breathing room to deliver their best work.",
      riskTolerant: "Slack shipped with bugs. Stripe launched before they had full compliance. The companies that win are the ones that move fast and learn faster. Let's be that company.",
    },
    diplomatic: {
      analytical: "The data presents a compelling case, though I want to ensure we've accounted for seasonal variance. Perhaps we could run a controlled pilot that satisfies both the growth team's timeline and finance's risk threshold.",
      creative: "There are merits to both the traditional and experimental approaches. What I'd propose is a hybrid — we keep the proven onboarding core while testing the proactive elements with a subset of new users.",
      assertive: "I appreciate the range of perspectives here. While urgency is warranted, I think we can find a path that moves quickly without leaving key stakeholders behind. Let me suggest a compressed timeline with clear checkpoints.",
      empathetic: "Both the business urgency and the team's capacity concerns are valid and important. I'd like to propose a framework that honors both — a phased approach with built-in flexibility for the team.",
      riskTolerant: "There's opportunity in moving quickly, and there's wisdom in being prepared. I suggest we define a 'minimum viable launch' that captures the first-mover advantage while maintaining our quality standards.",
    },
  }

  const styleFallback = fragments[style] || fragments.formal
  return styleFallback[dominant.key] || styleFallback.analytical
})

// --- Radar chart ---

const radarRef = ref(null)
let resizeObserver = null
let resizeTimer = null

function clearChart() {
  if (radarRef.value) {
    d3.select(radarRef.value).selectAll('*').remove()
  }
}

function renderRadar() {
  clearChart()
  const container = radarRef.value
  if (!container) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const size = Math.min(containerWidth, 280)
  const center = size / 2
  const maxRadius = size / 2 - 32

  const svg = d3.select(container)
    .append('svg')
    .attr('width', size)
    .attr('height', size)
    .attr('viewBox', `0 0 ${size} ${size}`)
    .style('display', 'block')
    .style('margin', '0 auto')

  const g = svg.append('g')
    .attr('transform', `translate(${center},${center})`)

  const angleSlice = (Math.PI * 2) / traits.length

  // Concentric grid rings
  const rings = [20, 40, 60, 80, 100]
  rings.forEach((ringVal) => {
    const r = (ringVal / 100) * maxRadius
    const points = traits.map((_, i) => {
      const angle = angleSlice * i - Math.PI / 2
      return [r * Math.cos(angle), r * Math.sin(angle)]
    })
    g.append('polygon')
      .attr('points', points.map((p) => p.join(',')).join(' '))
      .attr('fill', 'none')
      .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')
      .attr('stroke-width', ringVal === 100 ? 1 : 0.5)
  })

  // Axis lines from center to each vertex
  traits.forEach((_, i) => {
    const angle = angleSlice * i - Math.PI / 2
    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', maxRadius * Math.cos(angle))
      .attr('y2', maxRadius * Math.sin(angle))
      .attr('stroke', 'var(--color-border, rgba(0,0,0,0.1))')
      .attr('stroke-width', 0.5)
  })

  // Axis labels
  traits.forEach((trait, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const labelRadius = maxRadius + 20
    const x = labelRadius * Math.cos(angle)
    const y = labelRadius * Math.sin(angle)

    g.append('text')
      .attr('x', x)
      .attr('y', y)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', trait.color)
      .text(trait.label)
  })

  // Data polygon
  const dataPoints = traits.map((trait, i) => {
    const val = props.personality[trait.key] || 0
    const r = (val / 100) * maxRadius
    const angle = angleSlice * i - Math.PI / 2
    return [r * Math.cos(angle), r * Math.sin(angle)]
  })

  // Filled area
  g.append('polygon')
    .attr('points', dataPoints.map((p) => p.join(',')).join(' '))
    .attr('fill', 'rgba(32, 104, 255, 0.15)')
    .attr('stroke', '#2068FF')
    .attr('stroke-width', 2)
    .style('transition', 'all 0.3s ease')

  // Data point dots
  dataPoints.forEach((point, i) => {
    g.append('circle')
      .attr('cx', point[0])
      .attr('cy', point[1])
      .attr('r', 4)
      .attr('fill', traits[i].color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
  })
}

watch(
  () => props.personality,
  () => nextTick(renderRadar),
  { deep: true }
)

onMounted(() => {
  renderRadar()
  if (radarRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderRadar, 200)
    })
    resizeObserver.observe(radarRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="space-y-8">
    <!-- Preset Profiles -->
    <section>
      <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">Personality Presets</h3>
      <p class="text-xs text-[var(--color-text-muted)] mb-3">Start from a preset or customize each trait below</p>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
        <button
          v-for="preset in presets"
          :key="preset.name"
          class="text-left p-3 rounded-lg border transition-all cursor-pointer"
          :class="activePreset === preset.name
            ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)] shadow-sm'
            : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary-border)] hover:bg-[var(--color-primary-lighter)]'"
          @click="applyPreset(preset)"
        >
          <span class="block text-sm font-semibold text-[var(--color-text)]">{{ preset.name }}</span>
          <span class="block text-xs text-[var(--color-text-muted)] mt-0.5">{{ preset.description }}</span>
        </button>
      </div>
    </section>

    <!-- Sliders + Radar side by side -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Personality Sliders -->
      <section>
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">Personality Traits</h3>
        <div class="space-y-4">
          <div v-for="trait in traits" :key="trait.key">
            <div class="flex items-center justify-between mb-1.5">
              <label class="text-xs font-semibold text-[var(--color-text)]">
                {{ trait.label }}
              </label>
              <span
                class="text-xs font-semibold min-w-[2.5rem] text-right"
                :style="{ color: trait.color }"
              >
                {{ personality[trait.key] }}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              :value="personality[trait.key]"
              class="trait-slider w-full"
              :style="{
                '--slider-color': trait.color,
                '--slider-pct': personality[trait.key] + '%',
              }"
              @input="updateTrait(trait.key, $event.target.value)"
            />
          </div>
        </div>
      </section>

      <!-- Radar Chart -->
      <section>
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">Personality Shape</h3>
        <div
          ref="radarRef"
          class="flex items-center justify-center"
          style="min-height: 240px"
        />
      </section>
    </div>

    <!-- Communication Style -->
    <section>
      <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">Communication Style</h3>
      <p class="text-xs text-[var(--color-text-muted)] mb-3">How this agent expresses ideas in conversations</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        <label
          v-for="style in communicationStyles"
          :key="style.value"
          class="flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all"
          :class="communicationStyle === style.value
            ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
            : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary-border)]'"
        >
          <input
            type="radio"
            :value="style.value"
            :checked="communicationStyle === style.value"
            class="mt-0.5 accent-[var(--color-primary)]"
            @change="emit('update:communicationStyle', style.value)"
          />
          <div>
            <span class="block text-sm font-semibold text-[var(--color-text)]">{{ style.label }}</span>
            <span class="block text-xs text-[var(--color-text-muted)] mt-0.5 leading-relaxed">{{ style.description }}</span>
          </div>
        </label>
      </div>
    </section>

    <!-- Preview Message -->
    <section>
      <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">Preview</h3>
      <p class="text-xs text-[var(--color-text-muted)] mb-3">Sample message showing how this personality communicates</p>
      <div class="bg-[var(--color-bg-alt)] border border-[var(--color-border)] rounded-lg p-4">
        <p class="text-sm text-[var(--color-text)] leading-relaxed italic">
          "{{ previewText }}"
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.trait-slider {
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(
    to right,
    var(--slider-color) 0%,
    var(--slider-color) var(--slider-pct),
    var(--color-border, rgba(0, 0, 0, 0.1)) var(--slider-pct),
    var(--color-border, rgba(0, 0, 0, 0.1)) 100%
  );
  outline: none;
  cursor: pointer;
}

.trait-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--slider-color);
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: transform 0.15s ease;
}

.trait-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.trait-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--slider-color);
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}
</style>
