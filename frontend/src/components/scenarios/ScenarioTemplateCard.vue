<script setup>
const props = defineProps({
  scenario: {
    type: Object,
    required: true,
  },
  hero: {
    type: Boolean,
    default: false,
  },
  variant: {
    type: String,
    default: 'dark',
    validator: (v) => ['dark', 'light'].includes(v),
  },
})

defineEmits(['select'])

const ICON_MAP = {
  mail: '\u{1F4E7}',
  signal: '\u{1F4E1}',
  dollar: '\u{1F4B0}',
  sparkle: '\u2728',
}

const CATEGORY_COLORS = {
  outbound: '#2068FF',
  signals: '#ff5600',
  pricing: '#AA00FF',
  personalization: '#009900',
}

function resolveIcon(icon) {
  if (!icon) return '\u{1F41F}'
  if (/\p{Emoji}/u.test(icon)) return icon
  return ICON_MAP[icon] || '\u{1F41F}'
}

function categoryColor(category) {
  return CATEGORY_COLORS[category] || '#2068FF'
}

function formatCategory(category) {
  if (!category) return 'General'
  return category.charAt(0).toUpperCase() + category.slice(1)
}
</script>

<template>
  <button
    class="text-left rounded-lg transition-all duration-300 cursor-pointer border group w-full"
    :class="[
      hero ? 'p-6' : 'p-5',
      variant === 'dark'
        ? hero
          ? 'bg-[rgba(32,104,255,0.15)] border-[rgba(32,104,255,0.3)] hover:bg-[rgba(32,104,255,0.25)]'
          : 'bg-white/5 border-white/10 hover:bg-white/10'
        : 'bg-[var(--color-surface)] border-[var(--color-border)] hover:border-[var(--color-primary)] hover:shadow-md',
    ]"
    @click="$emit('select', scenario.id)"
  >
    <div class="flex items-start gap-3">
      <span
        class="shrink-0 flex items-center justify-center rounded-lg"
        :class="[
          hero ? 'w-10 h-10 text-2xl' : 'w-8 h-8 text-xl',
          variant === 'dark' ? 'bg-white/10' : 'bg-black/5',
        ]"
      >
        {{ resolveIcon(scenario.icon) }}
      </span>

      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <h3
            :class="[
              'font-semibold leading-snug',
              hero ? 'text-base' : 'text-sm',
              variant === 'dark' ? 'text-white' : 'text-[var(--color-text)]',
            ]"
          >
            {{ scenario.name }}
          </h3>
          <span
            v-if="scenario.category"
            class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide"
            :style="{
              backgroundColor: categoryColor(scenario.category) + '1A',
              color: variant === 'dark' ? categoryColor(scenario.category) : categoryColor(scenario.category),
            }"
          >
            {{ formatCategory(scenario.category) }}
          </span>
        </div>

        <p
          class="mt-1 line-clamp-2"
          :class="[
            hero ? 'text-sm' : 'text-xs',
            variant === 'dark' ? 'text-white/50' : 'text-[var(--color-text-secondary)]',
          ]"
        >
          {{ scenario.description }}
        </p>

        <!-- Stats row — only shown when agent_config is available -->
        <div
          v-if="scenario.agent_config || scenario.simulation_config"
          class="flex items-center gap-3 mt-3 flex-wrap"
        >
          <span
            v-if="scenario.agent_config?.count"
            class="inline-flex items-center gap-1 text-[11px] font-medium"
            :class="variant === 'dark' ? 'text-white/40' : 'text-[var(--color-text-muted)]'"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128H9m6 0a5.972 5.972 0 0 0-.786-3.07M9 19.128A9.38 9.38 0 0 1 6.375 19.5a9.337 9.337 0 0 1-4.121-.952 4.125 4.125 0 0 1 7.533-2.493M9 19.128v-.003c0-1.113.285-2.16.786-3.07M9 19.128H15m-6 0a5.972 5.972 0 0 1 .786-3.07m0 0a5.97 5.97 0 0 1 2.214-2.684 5.972 5.972 0 0 1 2.214 2.684" />
            </svg>
            {{ scenario.agent_config.count }} agents
          </span>

          <span
            v-if="scenario.simulation_config?.total_hours"
            class="inline-flex items-center gap-1 text-[11px] font-medium"
            :class="variant === 'dark' ? 'text-white/40' : 'text-[var(--color-text-muted)]'"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
            </svg>
            {{ scenario.simulation_config.total_hours }}h
          </span>

          <span
            v-if="scenario.agent_config?.persona_types?.length"
            class="inline-flex items-center gap-1 text-[11px] font-medium"
            :class="variant === 'dark' ? 'text-white/40' : 'text-[var(--color-text-muted)]'"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 0 0 3 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 0 0 5.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 0 0 9.568 3Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6Z" />
            </svg>
            {{ scenario.agent_config.persona_types.length }} personas
          </span>
        </div>
      </div>

      <!-- Arrow indicator -->
      <svg
        class="w-4 h-4 shrink-0 mt-1 transition-transform duration-200 group-hover:translate-x-0.5"
        :class="variant === 'dark' ? 'text-white/20 group-hover:text-white/40' : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-primary)]'"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
      </svg>
    </div>
  </button>
</template>
