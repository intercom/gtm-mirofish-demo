<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const VIEWERS = [
  { name: 'Alice Chen', initials: 'AC', color: '#2068FF' },
  { name: 'Marcus Rodriguez', initials: 'MR', color: '#ff5600' },
  { name: 'Sarah Kim', initials: 'SK', color: '#AA00FF' },
]

const PAGES = [
  'Dashboard', 'Scenarios', 'Workspace', 'Report', 'Chat', 'Settings',
]

const activeViewers = ref([])
const viewerPages = ref({})
const hoveredViewer = ref(null)
let changeTimeout = null

function randomPage() {
  return PAGES[Math.floor(Math.random() * PAGES.length)]
}

function initViewers() {
  const count = 2 + Math.floor(Math.random() * 2)
  const shuffled = [...VIEWERS].sort(() => Math.random() - 0.5)
  activeViewers.value = shuffled.slice(0, count)
  const pages = {}
  for (const v of activeViewers.value) {
    pages[v.name] = randomPage()
  }
  viewerPages.value = pages
}

function changeRandomViewerPage() {
  const viewers = activeViewers.value
  if (!viewers.length) return
  const viewer = viewers[Math.floor(Math.random() * viewers.length)]
  const currentPage = viewerPages.value[viewer.name]
  let newPage = randomPage()
  while (newPage === currentPage && PAGES.length > 1) {
    newPage = randomPage()
  }
  viewerPages.value = { ...viewerPages.value, [viewer.name]: newPage }
}

function scheduleChange() {
  changeTimeout = setTimeout(() => {
    changeRandomViewerPage()
    scheduleChange()
  }, 5000 + Math.random() * 7000)
}

onMounted(() => {
  initViewers()
  scheduleChange()
})

onUnmounted(() => {
  clearTimeout(changeTimeout)
})
</script>

<template>
  <div class="hidden sm:flex items-center">
    <div
      v-for="(viewer, i) in activeViewers"
      :key="viewer.name"
      class="relative"
      :class="{ '-ml-1.5': i > 0 }"
      @mouseenter="hoveredViewer = viewer.name"
      @mouseleave="hoveredViewer = null"
    >
      <div
        class="presence-avatar"
        :style="{ backgroundColor: viewer.color, zIndex: activeViewers.length - i }"
      >
        {{ viewer.initials }}
      </div>

      <Transition
        enter-active-class="transition duration-150 ease-out"
        enter-from-class="opacity-0 translate-y-1"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-1"
      >
        <div
          v-if="hoveredViewer === viewer.name"
          class="absolute top-full mt-2 left-1/2 -translate-x-1/2 px-3 py-1.5 bg-[#050505] text-white text-xs rounded-lg shadow-lg whitespace-nowrap z-50 pointer-events-none border border-white/10"
        >
          <span class="font-medium">{{ viewer.name }}</span>
          <span class="text-white/50"> is viewing </span>
          <span class="text-[#2068FF]">{{ viewerPages[viewer.name] }}</span>
          <div class="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-[#050505] border-l border-t border-white/10 rotate-45" />
        </div>
      </Transition>
    </div>

    <span class="w-2 h-2 rounded-full bg-emerald-500 ml-1.5 animate-pulse" />
  </div>
</template>

<style scoped>
.presence-avatar {
  position: relative;
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.625rem;
  font-weight: 600;
  color: white;
  border: 2px solid var(--color-navy);
  cursor: default;
  transition: transform 150ms ease;
}
.presence-avatar:hover {
  transform: scale(1.15);
  z-index: 10 !important;
}
</style>
