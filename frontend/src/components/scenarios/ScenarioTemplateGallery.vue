<script setup>
import { ref, onMounted } from 'vue'
import { useScenariosStore } from '../../stores/scenarios'
import ShimmerCard from '../ui/ShimmerCard.vue'
import AppBadge from '../common/AppBadge.vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'light',
    validator: (v) => ['light', 'dark'].includes(v),
  },
  showCustomCard: {
    type: Boolean,
    default: true,
  },
  heroFirst: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['select'])

const store = useScenariosStore()
const showCards = ref(false)

const ICON_MAP = {
  mail: '📧',
  signal: '📡',
  dollar: '💰',
  sparkle: '✨',
}

const CATEGORY_VARIANTS = {
  outbound: 'primary',
  pricing: 'warning',
  signal: 'success',
  personalization: 'primary',
}

function resolveIcon(icon) {
  if (!icon) return '🐟'
  if (/\p{Emoji}/u.test(icon)) return icon
  return ICON_MAP[icon] || '🐟'
}

function categoryVariant(category) {
  return CATEGORY_VARIANTS[category] || 'neutral'
}

function onStaggerBeforeEnter(el) {
  el.style.opacity = 0
  el.style.transform = 'translateY(12px)'
}

function onStaggerEnter(el, done) {
  const delay = el.dataset.index * 80
  setTimeout(() => {
    el.style.transition = 'opacity var(--transition-base), transform var(--transition-base)'
    el.style.opacity = 1
    el.style.transform = 'translateY(0)'
    el.addEventListener('transitionend', done, { once: true })
  }, delay)
}

onMounted(async () => {
  await store.fetchScenarios()
  showCards.value = true
})
</script>

<template>
  <!-- Loading -->
  <div v-if="store.loading" class="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
    <ShimmerCard v-for="n in 4" :key="n" :lines="3" />
  </div>

  <!-- Error -->
  <div v-else-if="store.error" class="text-center py-8">
    <div
      class="w-14 h-14 rounded-full flex items-center justify-center mx-auto mb-4"
      :class="variant === 'dark' ? 'bg-red-500/20' : 'bg-red-50'"
    >
      <svg
        class="w-7 h-7"
        :class="variant === 'dark' ? 'text-red-400' : 'text-red-500'"
        fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
      </svg>
    </div>
    <h3
      class="text-base font-semibold mb-1"
      :class="variant === 'dark' ? 'text-white' : 'text-[var(--color-text)]'"
    >
      Failed to load scenarios
    </h3>
    <p
      class="text-sm mb-4"
      :class="variant === 'dark' ? 'text-white/50' : 'text-[var(--color-text-muted)]'"
    >
      {{ store.error }}
    </p>
    <button
      @click="store.fetchScenarios(true)"
      class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
    >
      Try Again
    </button>
  </div>

  <!-- Empty -->
  <div v-else-if="!store.hasScenarios" class="text-center py-8">
    <div class="w-16 h-16 rounded-full bg-[rgba(32,104,255,0.15)] flex items-center justify-center mx-auto mb-4">
      <span class="text-3xl">🐟</span>
    </div>
    <h3
      class="text-base font-semibold mb-1"
      :class="variant === 'dark' ? 'text-white' : 'text-[var(--color-text)]'"
    >
      No scenarios available
    </h3>
    <p
      class="text-sm"
      :class="variant === 'dark' ? 'text-white/50' : 'text-[var(--color-text-muted)]'"
    >
      Check back soon — scenarios are being configured.
    </p>
  </div>

  <!-- Gallery Grid -->
  <TransitionGroup
    v-else
    tag="div"
    class="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4"
    :css="false"
    @before-enter="onStaggerBeforeEnter"
    @enter="onStaggerEnter"
  >
    <button
      v-for="(scenario, i) in showCards ? store.scenarios : []"
      :key="scenario.id"
      :data-index="i"
      @click="emit('select', scenario.id)"
      class="text-left rounded-lg transition-all duration-300 cursor-pointer border group"
      :class="[
        heroFirst && i === 0
          ? variant === 'dark'
            ? 'md:col-span-2 p-6 bg-[rgba(32,104,255,0.15)] border-[rgba(32,104,255,0.3)] hover:bg-[rgba(32,104,255,0.25)]'
            : 'md:col-span-2 p-6 border-[var(--color-primary)] bg-[rgba(32,104,255,0.04)] hover:bg-[rgba(32,104,255,0.08)]'
          : variant === 'dark'
            ? 'p-5 bg-white/5 border-white/10 hover:bg-white/10'
            : 'p-5 border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)] hover:shadow-[var(--shadow)]',
      ]"
    >
      <div class="flex items-start gap-3">
        <span :class="heroFirst && i === 0 ? 'text-3xl' : 'text-2xl'">
          {{ resolveIcon(scenario.icon) }}
        </span>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <h3
              :class="[
                heroFirst && i === 0 ? 'text-base' : 'text-sm',
                'font-semibold truncate',
                variant === 'dark' ? 'text-white' : 'text-[var(--color-text)]',
              ]"
            >
              {{ scenario.name }}
            </h3>
            <AppBadge
              v-if="scenario.category && variant === 'light'"
              :variant="categoryVariant(scenario.category)"
            >
              {{ scenario.category }}
            </AppBadge>
          </div>
          <p
            :class="[
              heroFirst && i === 0 ? 'text-sm mt-1' : 'text-xs mt-0.5',
              variant === 'dark' ? 'text-white/50' : 'text-[var(--color-text-muted)]',
            ]"
          >
            {{ scenario.description }}
          </p>
        </div>
        <svg
          class="w-4 h-4 shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity"
          :class="variant === 'dark' ? 'text-white/40' : 'text-[var(--color-text-muted)]'"
          fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
      </div>
    </button>

    <!-- Custom Simulation Card -->
    <button
      v-if="showCustomCard && showCards && store.hasScenarios"
      key="custom"
      :data-index="store.scenarios.length"
      @click="emit('select', 'custom')"
      class="text-left rounded-lg transition-all duration-300 cursor-pointer border border-dashed group"
      :class="variant === 'dark'
        ? 'p-5 border-white/20 hover:bg-white/10 hover:border-white/30'
        : 'p-5 border-[var(--color-border)] hover:border-[var(--color-primary)] hover:shadow-[var(--shadow)]'"
    >
      <div class="flex items-start gap-3">
        <span class="text-2xl">
          <svg
            class="w-6 h-6 transition-colors"
            :class="variant === 'dark'
              ? 'text-white/50 group-hover:text-[#2068FF]'
              : 'text-[var(--color-text-muted)] group-hover:text-[#2068FF]'"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
        </span>
        <div>
          <h3
            class="text-sm font-semibold transition-colors"
            :class="variant === 'dark'
              ? 'text-white/80 group-hover:text-white'
              : 'text-[var(--color-text-secondary)] group-hover:text-[var(--color-text)]'"
          >
            Custom Simulation
          </h3>
          <p
            class="text-xs mt-1"
            :class="variant === 'dark' ? 'text-white/40' : 'text-[var(--color-text-muted)]'"
          >
            Bring your own seed document and configure from scratch.
          </p>
        </div>
      </div>
    </button>
  </TransitionGroup>
</template>
