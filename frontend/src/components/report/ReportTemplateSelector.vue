<script setup>
import { ref, onMounted } from 'vue'
import { API_BASE } from '../../api/client'

const emit = defineEmits(['select'])

const templates = ref([])
const selected = ref(null)
const loading = ref(true)

const ICON_MAP = {
  briefcase: 'M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM10 2h4a2 2 0 012 2v1H8V4a2 2 0 012-2z',
  'chart-bar': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
  shield: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  users: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
  'document-text': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
}

const CATEGORY_COLORS = {
  leadership: '#2068FF',
  marketing: '#ff5600',
  strategy: '#AA00FF',
  research: '#009900',
  comprehensive: '#050505',
}

function iconPath(icon) {
  return ICON_MAP[icon] || ICON_MAP['document-text']
}

function categoryColor(category) {
  return CATEGORY_COLORS[category] || '#2068FF'
}

function selectTemplate(tpl) {
  selected.value = tpl.id
  emit('select', tpl)
}

onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/report/templates`)
    if (res.ok) {
      const json = await res.json()
      if (json.success) {
        templates.value = json.data
        // Pre-select the comprehensive template (full GTM analysis)
        const comprehensive = json.data.find((t) => t.category === 'comprehensive')
        if (comprehensive) {
          selected.value = comprehensive.id
          emit('select', comprehensive)
        }
      }
    }
  } catch {
    // Templates are optional — fall through to default generation
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Report Template</h3>
      <span class="text-xs text-[var(--color-text-muted)]">{{ templates.length }} templates</span>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <div
        v-for="i in 3"
        :key="i"
        class="h-28 rounded-lg bg-[var(--color-tint)] animate-pulse"
      />
    </div>

    <!-- Template cards -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <button
        v-for="tpl in templates"
        :key="tpl.id"
        @click="selectTemplate(tpl)"
        class="text-left p-4 rounded-lg border-2 transition-all duration-150 group"
        :class="
          selected === tpl.id
            ? 'border-[#2068FF] bg-[rgba(32,104,255,0.04)]'
            : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-border-strong)]'
        "
      >
        <div class="flex items-start gap-3">
          <!-- Icon -->
          <span
            class="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
            :style="{ backgroundColor: categoryColor(tpl.category) + '12' }"
          >
            <svg
              class="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              :style="{ color: categoryColor(tpl.category) }"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                :d="iconPath(tpl.icon)"
              />
            </svg>
          </span>

          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-[var(--color-text)] truncate">{{ tpl.name }}</span>
              <!-- Selected check -->
              <svg
                v-if="selected === tpl.id"
                class="w-4 h-4 shrink-0 text-[#2068FF]"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
            <p class="text-xs text-[var(--color-text-muted)] mt-1 line-clamp-2">{{ tpl.description }}</p>
            <span class="inline-block mt-2 text-[10px] font-medium px-1.5 py-0.5 rounded-full"
              :style="{
                backgroundColor: categoryColor(tpl.category) + '14',
                color: categoryColor(tpl.category),
              }"
            >
              {{ tpl.section_count === 0 ? 'AI-planned' : tpl.section_count + ' sections' }}
            </span>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>
