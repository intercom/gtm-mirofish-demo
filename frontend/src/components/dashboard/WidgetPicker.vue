<script setup>
import { ref, computed } from 'vue'
import { getWidgetsByCategory } from './WidgetRegistry.js'

defineProps({
  open: Boolean,
})

const emit = defineEmits(['close', 'add-widget'])

const search = ref('')
const categorized = getWidgetsByCategory()

const filteredCategories = computed(() => {
  const q = search.value.toLowerCase().trim()
  const result = {}
  for (const [key, cat] of Object.entries(categorized)) {
    const widgets = q
      ? cat.widgets.filter(
          (w) =>
            w.label.toLowerCase().includes(q) ||
            w.description.toLowerCase().includes(q) ||
            w.type.toLowerCase().includes(q),
        )
      : cat.widgets
    if (widgets.length) {
      result[key] = { ...cat, widgets }
    }
  }
  return result
})

const sortedCategories = computed(() =>
  Object.entries(filteredCategories.value).sort(([, a], [, b]) => a.order - b.order),
)

const hasResults = computed(() => sortedCategories.value.length > 0)

function onDragStart(e, widgetDef) {
  e.dataTransfer.effectAllowed = 'copy'
  e.dataTransfer.setData('application/widget-type', widgetDef.type)

  // Create a compact drag ghost
  const ghost = document.createElement('div')
  ghost.textContent = widgetDef.label
  ghost.style.cssText =
    'position:absolute;top:-9999px;padding:8px 16px;background:#2068FF;color:#fff;border-radius:8px;font-size:14px;font-weight:600;white-space:nowrap;'
  document.body.appendChild(ghost)
  e.dataTransfer.setDragImage(ghost, 0, 0)
  requestAnimationFrame(() => ghost.remove())
}

function addWidget(widgetDef) {
  emit('add-widget', {
    type: widgetDef.type,
    config: { ...widgetDef.defaultConfig },
    size: { ...widgetDef.defaultSize },
  })
}

function onBackdropClick(e) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}

const WIDGET_ICONS = {
  kpi_card: `<rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.5" fill="none"/><path d="M7 14l3-4 3 2 4-5" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`,
  line_chart: `<path d="M3 20L7 14L12 16L17 8L21 12" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/><line x1="3" y1="21" x2="21" y2="21" stroke="currentColor" stroke-width="1.5"/>`,
  bar_chart: `<rect x="3" y="12" width="4" height="9" rx="1" fill="currentColor" opacity="0.3"/><rect x="10" y="7" width="4" height="14" rx="1" fill="currentColor" opacity="0.6"/><rect x="17" y="3" width="4" height="18" rx="1" fill="currentColor"/>`,
  donut_chart: `<circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="3" fill="none" opacity="0.2"/><path d="M12 4a8 8 0 0 1 6.93 4" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M18.93 8a8 8 0 0 1-1.93 10" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round" opacity="0.6"/>`,
  table: `<rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.5" fill="none"/><line x1="3" y1="9" x2="21" y2="9" stroke="currentColor" stroke-width="1.5"/><line x1="3" y1="15" x2="21" y2="15" stroke="currentColor" stroke-width="1.5"/><line x1="9" y1="3" x2="9" y2="21" stroke="currentColor" stroke-width="1.5"/>`,
  funnel: `<path d="M4 4h16l-3 6H7L4 4z" fill="currentColor" opacity="0.3"/><path d="M7 10h10l-2.5 5h-5L7 10z" fill="currentColor" opacity="0.6"/><path d="M9.5 15h5l-1.5 4h-2L9.5 15z" fill="currentColor"/>`,
  gauge: `<path d="M4 16a8 8 0 0 1 16 0" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M12 16l-3-6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>`,
  text: `<path d="M6 4h12M12 4v16M8 20h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>`,
  activity_feed: `<circle cx="6" cy="6" r="2" fill="currentColor" opacity="0.4"/><line x1="10" y1="6" x2="20" y2="6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.4"/><circle cx="6" cy="12" r="2" fill="currentColor" opacity="0.7"/><line x1="10" y1="12" x2="18" y2="12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.7"/><circle cx="6" cy="18" r="2" fill="currentColor"/><line x1="10" y1="18" x2="16" y2="18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>`,
}

const WIDGET_PREVIEWS = {
  kpi_card: { value: '$1.2M', trend: '+12.3%', label: 'Revenue' },
  line_chart: { points: [20, 35, 28, 45, 52, 48, 60] },
  bar_chart: { bars: [65, 45, 80, 55, 70] },
  donut_chart: { segments: [40, 25, 20, 15] },
  table: { rows: 3, cols: 3 },
  funnel: { stages: [100, 68, 42, 18] },
  gauge: { value: 73 },
  text: { content: 'Aa' },
  activity_feed: { items: 4 },
}
</script>

<template>
  <Teleport to="body">
    <Transition name="slideover">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex justify-end"
        @click="onBackdropClick"
      >
        <div class="widget-picker-panel bg-[--color-surface] shadow-lg w-full max-w-md h-full flex flex-col overflow-hidden border-l border-[--color-border]">
          <!-- Header -->
          <div class="flex items-center justify-between px-5 py-4 border-b border-[--color-border] shrink-0">
            <h2 class="text-lg font-semibold text-[--color-text]">Add Widget</h2>
            <button
              class="text-[--color-text-muted] hover:text-[--color-text] transition-colors cursor-pointer p-1"
              @click="emit('close')"
              aria-label="Close"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Search -->
          <div class="px-5 py-3 border-b border-[--color-border] shrink-0">
            <div class="relative">
              <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[--color-text-muted]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                v-model="search"
                type="text"
                placeholder="Search widgets..."
                class="w-full bg-[--color-bg] border border-[--color-border] rounded-lg pl-9 pr-3 py-2 text-sm text-[--color-text] placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-primary] focus:ring-1 focus:ring-[--color-primary] transition-colors"
              />
            </div>
          </div>

          <!-- Widget List -->
          <div class="flex-1 overflow-y-auto px-5 py-4">
            <template v-if="hasResults">
              <div
                v-for="[catKey, cat] in sortedCategories"
                :key="catKey"
                class="mb-6 last:mb-0"
              >
                <h3 class="text-xs font-semibold text-[--color-text-muted] uppercase tracking-wider mb-3">
                  {{ cat.label }}
                </h3>
                <div class="space-y-2">
                  <button
                    v-for="widget in cat.widgets"
                    :key="widget.type"
                    class="widget-card w-full text-left bg-[--color-bg] hover:bg-[--card-highlight-bg] border border-[--color-border] hover:border-[--color-primary-border] rounded-lg p-3 transition-all cursor-pointer group"
                    draggable="true"
                    @dragstart="onDragStart($event, widget)"
                    @click="addWidget(widget)"
                  >
                    <div class="flex items-start gap-3">
                      <!-- Icon + Preview -->
                      <div class="shrink-0 w-12 h-12 rounded-lg bg-[--color-surface] border border-[--color-border] flex items-center justify-center text-[--color-text-muted] group-hover:text-[--color-primary] group-hover:border-[--color-primary-border] transition-colors">
                        <svg
                          class="w-6 h-6"
                          viewBox="0 0 24 24"
                          v-html="WIDGET_ICONS[widget.type]"
                        />
                      </div>

                      <!-- Info -->
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                          <span class="text-sm font-semibold text-[--color-text] group-hover:text-[--color-primary] transition-colors">
                            {{ widget.label }}
                          </span>
                        </div>
                        <p class="text-xs text-[--color-text-muted] mt-0.5 line-clamp-2">
                          {{ widget.description }}
                        </p>

                        <!-- Mini Preview -->
                        <div class="mt-2 widget-preview">
                          <!-- KPI preview -->
                          <div v-if="widget.type === 'kpi_card'" class="flex items-baseline gap-2">
                            <span class="text-sm font-bold text-[--color-text]">{{ WIDGET_PREVIEWS.kpi_card.value }}</span>
                            <span class="text-[10px] font-medium text-[--color-success]">{{ WIDGET_PREVIEWS.kpi_card.trend }}</span>
                          </div>

                          <!-- Line chart preview -->
                          <svg v-else-if="widget.type === 'line_chart'" class="w-full h-5" viewBox="0 0 100 20" preserveAspectRatio="none">
                            <polyline
                              :points="WIDGET_PREVIEWS.line_chart.points.map((v, i) => `${(i / 6) * 100},${20 - (v / 60) * 20}`).join(' ')"
                              fill="none"
                              stroke="var(--color-primary)"
                              stroke-width="1.5"
                              stroke-linecap="round"
                              stroke-linejoin="round"
                            />
                          </svg>

                          <!-- Bar chart preview -->
                          <svg v-else-if="widget.type === 'bar_chart'" class="w-full h-5" viewBox="0 0 100 20">
                            <rect
                              v-for="(val, i) in WIDGET_PREVIEWS.bar_chart.bars"
                              :key="i"
                              :x="i * 20 + 2"
                              :y="20 - (val / 80) * 20"
                              width="14"
                              :height="(val / 80) * 20"
                              rx="1"
                              fill="var(--color-primary)"
                              :opacity="0.4 + (val / 80) * 0.6"
                            />
                          </svg>

                          <!-- Donut chart preview -->
                          <div v-else-if="widget.type === 'donut_chart'" class="flex items-center gap-1">
                            <span
                              v-for="(seg, i) in WIDGET_PREVIEWS.donut_chart.segments"
                              :key="i"
                              class="h-2 rounded-full"
                              :style="{
                                width: seg + '%',
                                backgroundColor: ['#2068FF', '#ff5600', '#AA00FF', '#009900'][i],
                                opacity: 0.7,
                              }"
                            />
                          </div>

                          <!-- Table preview -->
                          <div v-else-if="widget.type === 'table'" class="flex flex-col gap-0.5">
                            <div
                              v-for="r in WIDGET_PREVIEWS.table.rows"
                              :key="r"
                              class="flex gap-0.5"
                            >
                              <span
                                v-for="c in WIDGET_PREVIEWS.table.cols"
                                :key="c"
                                class="flex-1 h-1.5 rounded-sm"
                                :class="r === 1 ? 'bg-[--color-primary] opacity-30' : 'bg-[--color-border]'"
                              />
                            </div>
                          </div>

                          <!-- Funnel preview -->
                          <div v-else-if="widget.type === 'funnel'" class="flex flex-col items-center gap-0.5">
                            <div
                              v-for="(val, i) in WIDGET_PREVIEWS.funnel.stages"
                              :key="i"
                              class="h-1.5 rounded-sm bg-[--color-primary]"
                              :style="{ width: val + '%', opacity: 0.3 + (i / 3) * 0.7 }"
                            />
                          </div>

                          <!-- Gauge preview -->
                          <div v-else-if="widget.type === 'gauge'" class="flex items-center gap-1.5">
                            <div class="flex-1 h-1.5 bg-[--color-border] rounded-full overflow-hidden">
                              <div
                                class="h-full bg-[--color-primary] rounded-full"
                                :style="{ width: WIDGET_PREVIEWS.gauge.value + '%' }"
                              />
                            </div>
                            <span class="text-[10px] font-medium text-[--color-text-muted]">{{ WIDGET_PREVIEWS.gauge.value }}%</span>
                          </div>

                          <!-- Text preview -->
                          <div v-else-if="widget.type === 'text'" class="text-xs text-[--color-text-muted] italic">
                            {{ WIDGET_PREVIEWS.text.content }}
                          </div>

                          <!-- Activity feed preview -->
                          <div v-else-if="widget.type === 'activity_feed'" class="flex flex-col gap-0.5">
                            <div
                              v-for="n in WIDGET_PREVIEWS.activity_feed.items"
                              :key="n"
                              class="flex items-center gap-1"
                            >
                              <span class="w-1.5 h-1.5 rounded-full bg-[--color-primary]" :style="{ opacity: 1 - (n - 1) * 0.2 }" />
                              <span class="flex-1 h-1 rounded-sm bg-[--color-border]" />
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Add indicator -->
                      <div class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-[--color-primary]">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                        </svg>
                      </div>
                    </div>
                  </button>
                </div>
              </div>
            </template>

            <!-- Empty state -->
            <div v-else class="flex flex-col items-center justify-center py-12 text-center">
              <svg class="w-10 h-10 text-[--color-text-muted] mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <p class="text-sm text-[--color-text-muted]">
                No widgets match "<span class="font-medium">{{ search }}</span>"
              </p>
              <button
                class="mt-2 text-xs text-[--color-primary] hover:underline cursor-pointer"
                @click="search = ''"
              >
                Clear search
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.slideover-enter-active,
.slideover-leave-active {
  transition: opacity var(--transition-fast);
}
.slideover-enter-active .widget-picker-panel,
.slideover-leave-active .widget-picker-panel {
  transition: transform var(--transition-base);
}
.slideover-enter-from,
.slideover-leave-to {
  opacity: 0;
}
.slideover-enter-from .widget-picker-panel,
.slideover-leave-to .widget-picker-panel {
  transform: translateX(100%);
}

.widget-card:active {
  transform: scale(0.98);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
