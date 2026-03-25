<script setup>
import { ref, computed } from 'vue'

const emit = defineEmits(['add-section'])

const searchQuery = ref('')
const collapsedCategories = ref(new Set())

const SECTION_TYPES = [
  { id: 'heading', label: 'Heading', category: 'text', description: 'Section title or subtitle' },
  { id: 'paragraph', label: 'Paragraph', category: 'text', description: 'Rich text block' },
  { id: 'callout', label: 'Callout', category: 'text', description: 'Highlighted info box' },
  { id: 'line-chart', label: 'Line Chart', category: 'charts', description: 'Trend over time' },
  { id: 'bar-chart', label: 'Bar Chart', category: 'charts', description: 'Compare values' },
  { id: 'donut-chart', label: 'Donut Chart', category: 'charts', description: 'Part of whole' },
  { id: 'radar-chart', label: 'Radar Chart', category: 'charts', description: 'Multi-axis comparison' },
  { id: 'table', label: 'Table', category: 'data', description: 'Rows and columns' },
  { id: 'kpi-row', label: 'KPI Row', category: 'data', description: 'Key metric indicators' },
  { id: 'metric-cards', label: 'Metric Cards', category: 'data', description: 'Stat cards grid' },
  { id: 'divider', label: 'Divider', category: 'layout', description: 'Horizontal rule' },
  { id: 'spacer', label: 'Spacer', category: 'layout', description: 'Vertical spacing' },
  { id: 'columns', label: 'Columns', category: 'layout', description: 'Multi-column layout' },
]

const CATEGORIES = [
  { id: 'text', label: 'Text' },
  { id: 'charts', label: 'Charts' },
  { id: 'data', label: 'Data' },
  { id: 'layout', label: 'Layout' },
]

const filteredSections = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return SECTION_TYPES
  return SECTION_TYPES.filter(
    (s) => s.label.toLowerCase().includes(q) || s.description.toLowerCase().includes(q)
  )
})

function sectionsForCategory(categoryId) {
  return filteredSections.value.filter((s) => s.category === categoryId)
}

function toggleCategory(categoryId) {
  if (collapsedCategories.value.has(categoryId)) {
    collapsedCategories.value.delete(categoryId)
  } else {
    collapsedCategories.value.add(categoryId)
  }
}

function isCategoryExpanded(categoryId) {
  return !collapsedCategories.value.has(categoryId)
}

function onDragStart(event, section) {
  event.dataTransfer.setData('application/x-section-type', JSON.stringify(section))
  event.dataTransfer.effectAllowed = 'copy'
}

function addSection(section) {
  emit('add-section', { ...section })
}
</script>

<template>
  <div class="section-palette flex flex-col h-full">
    <div class="px-3 pt-3 pb-2">
      <h3 class="text-xs font-semibold text-[--color-text-muted] uppercase tracking-wider mb-2">
        Sections
      </h3>
      <div class="relative">
        <svg
          class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[--color-text-muted]"
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Filter sections..."
          class="w-full bg-[--color-surface] border border-[--color-border] rounded-lg pl-8 pr-3 py-1.5 text-xs text-[--color-text] placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-primary] focus:ring-1 focus:ring-[--color-primary] transition-colors"
        />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-3 pb-3">
      <template v-for="cat in CATEGORIES" :key="cat.id">
        <div v-if="sectionsForCategory(cat.id).length > 0" class="mb-3">
          <button
            class="flex items-center justify-between w-full py-1.5 text-xs font-semibold text-[--color-text-secondary] hover:text-[--color-text] transition-colors"
            @click="toggleCategory(cat.id)"
          >
            <span class="flex items-center gap-1.5">
              <!-- Category icons -->
              <svg v-if="cat.id === 'text'" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h10M4 18h14" />
              </svg>
              <svg v-else-if="cat.id === 'charts'" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <svg v-else-if="cat.id === 'data'" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18M3 6h18M3 18h18M10 6v12M17 6v12" />
              </svg>
              <svg v-else-if="cat.id === 'layout'" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm0 8a1 1 0 011-1h5a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zm9 0a1 1 0 011-1h5a1 1 0 011 1v6a1 1 0 01-1 1h-5a1 1 0 01-1-1v-6z" />
              </svg>
              {{ cat.label }}
            </span>
            <svg
              class="w-3 h-3 transition-transform"
              :class="{ '-rotate-90': !isCategoryExpanded(cat.id) }"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div v-show="isCategoryExpanded(cat.id)" class="grid grid-cols-2 gap-1.5 mt-1">
            <button
              v-for="section in sectionsForCategory(cat.id)"
              :key="section.id"
              class="palette-item group flex flex-col items-center gap-1 p-2.5 rounded-lg border border-[--color-border] bg-[--color-surface] hover:border-[--color-primary-border] hover:bg-[--color-primary-light] cursor-grab active:cursor-grabbing transition-all text-left"
              draggable="true"
              @dragstart="onDragStart($event, section)"
              @click="addSection(section)"
            >
              <div class="w-7 h-7 rounded-md bg-[--color-tint] group-hover:bg-[--color-primary-tint] flex items-center justify-center transition-colors">
                <!-- Section type icons -->
                <svg v-if="section.id === 'heading'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h8" />
                </svg>
                <svg v-else-if="section.id === 'paragraph'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h12M4 18h10" />
                </svg>
                <svg v-else-if="section.id === 'callout'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <svg v-else-if="section.id === 'line-chart'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4v16" />
                </svg>
                <svg v-else-if="section.id === 'bar-chart'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <svg v-else-if="section.id === 'donut-chart'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14a4 4 0 110-8 4 4 0 010 8z" />
                </svg>
                <svg v-else-if="section.id === 'radar-chart'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <polygon stroke-linecap="round" stroke-linejoin="round" stroke-width="2" points="12,2 22,8.5 19,19.5 5,19.5 2,8.5" fill="none" />
                  <polygon stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" points="12,7 17,10.5 15.5,16 8.5,16 7,10.5" fill="none" opacity="0.5" />
                </svg>
                <svg v-else-if="section.id === 'table'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18M3 6h18M3 18h18M10 6v12" />
                </svg>
                <svg v-else-if="section.id === 'kpi-row'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                <svg v-else-if="section.id === 'metric-cards'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                </svg>
                <svg v-else-if="section.id === 'divider'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12h18" />
                </svg>
                <svg v-else-if="section.id === 'spacer'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h16M4 4l16 0M4 16v4m0 0h16" />
                </svg>
                <svg v-else-if="section.id === 'columns'" class="w-4 h-4 text-[--color-text-secondary] group-hover:text-[--color-primary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 4v16M15 4v16M4 4h16v16H4z" />
                </svg>
              </div>
              <span class="text-[10px] font-medium text-[--color-text-secondary] group-hover:text-[--color-primary] text-center leading-tight transition-colors">
                {{ section.label }}
              </span>
            </button>
          </div>
        </div>
      </template>

      <!-- Empty search state -->
      <div
        v-if="searchQuery && filteredSections.length === 0"
        class="text-center py-8 text-[--color-text-muted]"
      >
        <svg class="w-8 h-8 mx-auto mb-2 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <p class="text-xs">No sections match "{{ searchQuery }}"</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.palette-item:active {
  transform: scale(0.96);
}
</style>
