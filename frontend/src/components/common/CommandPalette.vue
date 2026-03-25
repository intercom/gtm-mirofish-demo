<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useCommandPalette } from '../../composables/useCommandPalette'
import { useTheme } from '../../composables/useTheme'
import { useSimulationStore } from '../../stores/simulation'

const router = useRouter()
const { isOpen, close } = useCommandPalette()
const { isDark, setTheme } = useTheme()
const simulation = useSimulationStore()

const query = ref('')
const activeIndex = ref(0)
const inputRef = ref(null)

const navigationItems = [
  { id: 'nav-home', label: 'Go to Home', category: 'Navigation', icon: 'home', action: () => router.push('/') },
  { id: 'nav-simulations', label: 'Go to Simulations', category: 'Navigation', icon: 'grid', action: () => router.push('/simulations') },
  { id: 'nav-settings', label: 'Go to Settings', category: 'Navigation', icon: 'settings', action: () => router.push('/settings') },
]

const actionItems = computed(() => [
  {
    id: 'action-theme',
    label: isDark.value ? 'Switch to Light Mode' : 'Switch to Dark Mode',
    category: 'Actions',
    icon: isDark.value ? 'sun' : 'moon',
    action: () => setTheme(isDark.value ? 'light' : 'dark'),
  },
])

const recentRunItems = computed(() => {
  return simulation.sessionRuns
    .slice()
    .reverse()
    .slice(0, 5)
    .map((run) => ({
      id: `run-${run.id}`,
      label: run.scenarioName || 'Untitled Simulation',
      category: 'Recent Simulations',
      icon: 'play',
      subtitle: run.status,
      action: () => router.push(`/workspace/${run.id}`),
    }))
})

const allItems = computed(() => [
  ...navigationItems,
  ...actionItems.value,
  ...recentRunItems.value,
])

const filteredItems = computed(() => {
  const q = query.value.toLowerCase().trim()
  if (!q) return allItems.value
  return allItems.value.filter(
    (item) =>
      item.label.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q) ||
      (item.subtitle && item.subtitle.toLowerCase().includes(q)),
  )
})

const groupedItems = computed(() => {
  const groups = {}
  for (const item of filteredItems.value) {
    if (!groups[item.category]) groups[item.category] = []
    groups[item.category].push(item)
  }
  return groups
})

watch(isOpen, (open) => {
  if (open) {
    query.value = ''
    activeIndex.value = 0
    nextTick(() => inputRef.value?.focus())
  }
})

watch(query, () => {
  activeIndex.value = 0
})

function selectItem(item) {
  close()
  item.action()
}

function onKeydown(e) {
  const count = filteredItems.value.length
  if (!count) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIndex.value = (activeIndex.value + 1) % count
    scrollActiveIntoView()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIndex.value = (activeIndex.value - 1 + count) % count
    scrollActiveIntoView()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const item = filteredItems.value[activeIndex.value]
    if (item) selectItem(item)
  }
}

function scrollActiveIntoView() {
  nextTick(() => {
    const el = document.querySelector('[data-palette-active="true"]')
    el?.scrollIntoView({ block: 'nearest' })
  })
}

function onBackdropClick(e) {
  if (e.target === e.currentTarget) close()
}

function getFlatIndex(category, indexInGroup) {
  let offset = 0
  for (const [cat, items] of Object.entries(groupedItems.value)) {
    if (cat === category) return offset + indexInGroup
    offset += items.length
  }
  return 0
}

const isMac = navigator.platform.includes('Mac')
</script>

<template>
  <Teleport to="body">
    <Transition name="palette">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[60] flex items-start justify-center pt-[15vh] bg-black/50 backdrop-blur-sm"
        @click="onBackdropClick"
        @keydown="onKeydown"
      >
        <div class="palette-container bg-[--color-surface] rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden border border-[--color-border]">
          <!-- Search input -->
          <div class="flex items-center gap-3 px-4 py-3 border-b border-[--color-border]">
            <svg class="w-5 h-5 text-[--color-text-muted] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              ref="inputRef"
              v-model="query"
              type="text"
              class="flex-1 bg-transparent text-[--color-text] text-sm outline-none placeholder:text-[--color-text-muted]"
              placeholder="Search commands, pages, simulations..."
            />
            <kbd class="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-medium text-[--color-text-muted] bg-[--color-bg] border border-[--color-border] rounded">
              ESC
            </kbd>
          </div>

          <!-- Results -->
          <div class="max-h-[50vh] overflow-y-auto py-2">
            <template v-if="filteredItems.length">
              <div v-for="(items, category) in groupedItems" :key="category">
                <div class="px-4 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-[--color-text-muted]">
                  {{ category }}
                </div>
                <button
                  v-for="(item, idx) in items"
                  :key="item.id"
                  :data-palette-active="getFlatIndex(category, idx) === activeIndex ? 'true' : undefined"
                  class="w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm transition-colors"
                  :class="getFlatIndex(category, idx) === activeIndex
                    ? 'bg-[--color-primary] text-white'
                    : 'text-[--color-text] hover:bg-[--color-bg]'"
                  @click="selectItem(item)"
                  @mouseenter="activeIndex = getFlatIndex(category, idx)"
                >
                  <!-- Icons -->
                  <span class="w-5 h-5 shrink-0 flex items-center justify-center" :class="getFlatIndex(category, idx) === activeIndex ? 'text-white/80' : 'text-[--color-text-muted]'">
                    <svg v-if="item.icon === 'home'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                    <svg v-else-if="item.icon === 'grid'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                    </svg>
                    <svg v-else-if="item.icon === 'settings'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <svg v-else-if="item.icon === 'sun'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    <svg v-else-if="item.icon === 'moon'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                    </svg>
                    <svg v-else-if="item.icon === 'play'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </span>

                  <div class="flex-1 min-w-0">
                    <span class="block truncate">{{ item.label }}</span>
                    <span v-if="item.subtitle" class="block text-xs truncate" :class="getFlatIndex(category, idx) === activeIndex ? 'text-white/60' : 'text-[--color-text-muted]'">
                      {{ item.subtitle }}
                    </span>
                  </div>
                </button>
              </div>
            </template>

            <!-- Empty state -->
            <div v-else class="px-4 py-8 text-center text-sm text-[--color-text-muted]">
              No results for "{{ query }}"
            </div>
          </div>

          <!-- Footer hint -->
          <div class="flex items-center gap-4 px-4 py-2.5 border-t border-[--color-border] text-[11px] text-[--color-text-muted]">
            <span class="flex items-center gap-1">
              <kbd class="px-1 py-0.5 bg-[--color-bg] border border-[--color-border] rounded text-[10px]">&uarr;</kbd>
              <kbd class="px-1 py-0.5 bg-[--color-bg] border border-[--color-border] rounded text-[10px]">&darr;</kbd>
              navigate
            </span>
            <span class="flex items-center gap-1">
              <kbd class="px-1 py-0.5 bg-[--color-bg] border border-[--color-border] rounded text-[10px]">&crarr;</kbd>
              select
            </span>
            <span class="flex items-center gap-1">
              <kbd class="px-1 py-0.5 bg-[--color-bg] border border-[--color-border] rounded text-[10px]">{{ isMac ? '⌘' : 'Ctrl' }}</kbd>
              <kbd class="px-1 py-0.5 bg-[--color-bg] border border-[--color-border] rounded text-[10px]">K</kbd>
              toggle
            </span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.palette-enter-active,
.palette-leave-active {
  transition: opacity 150ms ease;
}
.palette-enter-active .palette-container,
.palette-leave-active .palette-container {
  transition: transform 150ms ease, opacity 150ms ease;
}
.palette-enter-from,
.palette-leave-to {
  opacity: 0;
}
.palette-enter-from .palette-container {
  opacity: 0;
  transform: scale(0.96) translateY(-8px);
}
.palette-leave-to .palette-container {
  opacity: 0;
  transform: scale(0.96) translateY(-8px);
}
</style>
