<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTutorialStore } from '../stores/tutorial'

const tutorial = useTutorialStore()
const activeCategory = ref(null)

onMounted(() => {
  tutorial.fetchCatalog()
})

const filteredTutorials = computed(() => {
  if (!activeCategory.value) return tutorial.catalog
  return tutorial.catalog.filter((t) => t.category === activeCategory.value)
})

const groupedByCategory = computed(() => {
  const groups = {}
  for (const t of filteredTutorials.value) {
    if (!groups[t.category]) groups[t.category] = []
    groups[t.category].push(t)
  }
  // Sort groups by category order
  const ordered = []
  for (const cat of tutorial.categories) {
    if (groups[cat.id]) {
      ordered.push({ ...cat, tutorials: groups[cat.id] })
    }
  }
  return ordered
})

function difficultyColor(d) {
  if (d === 'beginner') return '#22c55e'
  if (d === 'intermediate') return '#f59e0b'
  return '#ef4444'
}

function difficultyBg(d) {
  if (d === 'beginner') return 'rgba(34, 197, 94, 0.1)'
  if (d === 'intermediate') return 'rgba(245, 158, 11, 0.1)'
  return 'rgba(239, 68, 68, 0.1)'
}

const iconPaths = {
  compass: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 0 l3 7 7 3-7 3-3 7-3-7-7-3 7-3z',
  'play-circle': 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M10 8l6 4-6 4z',
  'share-2': 'M18 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM6 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM18 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M8.59 13.51l6.83 3.98 M15.41 6.51l-6.82 3.98',
  'bar-chart-2': 'M18 20V10 M12 20V4 M6 20v-6',
  'git-branch': 'M6 3v12 M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M18 9c0 6-12 6-12 12',
}

function getStepProgress(t) {
  const progress = tutorial.getTutorialProgress(t.id)
  return progress.completedSteps.length
}
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 md:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-[var(--color-text)] mb-2">Interactive Tutorials</h1>
      <p class="text-sm text-[var(--color-text-muted)] max-w-2xl">
        Learn how to use MiroFish through guided, step-by-step tutorials. Each tutorial walks you through a specific feature with interactive actions and explanations.
      </p>
    </div>

    <!-- Overall progress -->
    <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 mb-8">
      <div class="flex items-center justify-between mb-3">
        <div>
          <span class="text-sm font-bold text-[var(--color-text)]">Your Progress</span>
          <span class="ml-2 text-xs text-[var(--color-text-muted)]">
            {{ tutorial.completedTutorialIds.length }} of {{ tutorial.catalog.length }} completed
          </span>
        </div>
        <button
          v-if="tutorial.completedTutorialIds.length > 0"
          class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer"
          @click="tutorial.resetAllProgress()"
        >
          Reset all
        </button>
      </div>
      <div class="w-full h-2 bg-[var(--color-border)] rounded-full overflow-hidden">
        <div
          class="h-full bg-[#2068FF] rounded-full transition-all duration-500"
          :style="{ width: `${tutorial.overallProgress}%` }"
        />
      </div>
    </div>

    <!-- Category filter -->
    <div class="flex items-center gap-2 mb-6 flex-wrap">
      <button
        class="px-3 py-1.5 text-xs font-semibold rounded-lg cursor-pointer transition-colors"
        :class="!activeCategory
          ? 'bg-[#2068FF] text-white'
          : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] bg-[var(--color-surface)] border border-[var(--color-border)]'"
        @click="activeCategory = null"
      >
        All
      </button>
      <button
        v-for="cat in tutorial.categories"
        :key="cat.id"
        class="px-3 py-1.5 text-xs font-semibold rounded-lg cursor-pointer transition-colors"
        :class="activeCategory === cat.id
          ? 'bg-[#2068FF] text-white'
          : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] bg-[var(--color-surface)] border border-[var(--color-border)]'"
        @click="activeCategory = cat.id"
      >
        {{ cat.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="tutorial.catalogLoading" class="text-center py-16 text-[var(--color-text-muted)] text-sm">
      Loading tutorials...
    </div>

    <!-- Tutorial groups -->
    <div v-else class="space-y-8">
      <section v-for="group in groupedByCategory" :key="group.id">
        <h2 class="text-sm font-bold text-[var(--color-text)] mb-4 uppercase tracking-wider">
          {{ group.label }}
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div
            v-for="t in group.tutorials"
            :key="t.id"
            class="tutorial-card group"
            :class="{ 'tutorial-card--completed': tutorial.isTutorialCompleted(t.id) }"
          >
            <!-- Icon + title -->
            <div class="flex items-start gap-3 mb-3">
              <div class="w-10 h-10 rounded-xl bg-[#2068FF]/8 flex items-center justify-center shrink-0 group-hover:bg-[#2068FF]/15 transition-colors">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2068FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path :d="iconPaths[t.icon] || iconPaths.compass" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-0.5">
                  <h3 class="text-sm font-bold text-[var(--color-text)] truncate">{{ t.title }}</h3>
                  <svg
                    v-if="tutorial.isTutorialCompleted(t.id)"
                    width="16" height="16" viewBox="0 0 24 24" fill="#22c55e" stroke="#22c55e" stroke-width="2"
                  >
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                    <polyline points="22 4 12 14.01 9 11.01" fill="none" />
                  </svg>
                </div>
                <p class="text-xs text-[var(--color-text-muted)] leading-relaxed line-clamp-2">
                  {{ t.description }}
                </p>
              </div>
            </div>

            <!-- Meta row -->
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
                <span
                  class="font-semibold px-1.5 py-0.5 rounded"
                  :style="{ color: difficultyColor(t.difficulty), backgroundColor: difficultyBg(t.difficulty) }"
                >
                  {{ t.difficulty }}
                </span>
                <span>{{ t.stepCount }} steps</span>
                <span>~{{ t.estimatedMinutes }}m</span>
              </div>

              <!-- Step progress micro-bar -->
              <div v-if="getStepProgress(t) > 0 && !tutorial.isTutorialCompleted(t.id)" class="flex items-center gap-1.5">
                <div class="w-12 h-1 bg-[var(--color-border)] rounded-full overflow-hidden">
                  <div
                    class="h-full bg-[#2068FF] rounded-full"
                    :style="{ width: `${(getStepProgress(t) / t.stepCount) * 100}%` }"
                  />
                </div>
                <span class="text-[10px] text-[var(--color-text-muted)]">{{ getStepProgress(t) }}/{{ t.stepCount }}</span>
              </div>
            </div>

            <!-- Actions -->
            <div class="mt-3 pt-3 border-t border-[var(--color-border)] flex items-center justify-between">
              <button
                v-if="tutorial.isTutorialCompleted(t.id)"
                class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer"
                @click="tutorial.resetTutorialProgress(t.id)"
              >
                Restart
              </button>
              <span v-else />

              <button
                class="px-4 py-1.5 text-xs font-semibold rounded-lg cursor-pointer transition-colors"
                :class="tutorial.isTutorialCompleted(t.id)
                  ? 'text-[#2068FF] border border-[#2068FF]/30 hover:bg-[#2068FF]/5'
                  : 'text-white bg-[#2068FF] hover:bg-[#1a5ae0]'"
                @click="tutorial.startTutorial(t.id)"
              >
                {{ tutorial.isTutorialCompleted(t.id) ? 'Review' : getStepProgress(t) > 0 ? 'Continue' : 'Start' }}
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Empty state -->
    <div v-if="!tutorial.catalogLoading && filteredTutorials.length === 0" class="text-center py-16">
      <p class="text-sm text-[var(--color-text-muted)]">No tutorials found for this category.</p>
    </div>
  </div>
</template>

<style scoped>
.tutorial-card {
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 14px;
  padding: 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.tutorial-card:hover {
  border-color: #2068FF40;
  box-shadow: 0 2px 12px rgba(32, 104, 255, 0.06);
}
.tutorial-card--completed {
  border-color: rgba(34, 197, 94, 0.2);
}
.tutorial-card--completed:hover {
  border-color: rgba(34, 197, 94, 0.4);
  box-shadow: 0 2px 12px rgba(34, 197, 94, 0.06);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
