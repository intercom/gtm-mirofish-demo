<script setup>
import { ref, watch } from 'vue'
import { useScenariosStore } from '../../stores/scenarios'

const props = defineProps({
  open: Boolean,
  scenarioId: String,
})

const emit = defineEmits(['close', 'launch'])

const store = useScenariosStore()
const loading = ref(false)
const scenario = ref(null)
const error = ref(null)

watch(
  () => [props.open, props.scenarioId],
  async ([isOpen, id]) => {
    if (!isOpen || !id) {
      scenario.value = null
      error.value = null
      return
    }
    loading.value = true
    error.value = null
    try {
      scenario.value = await store.fetchScenarioById(id)
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

const ICON_MAP = {
  mail: '\u{1F4E7}',
  'mail-open': '\u{1F4E7}',
  signal: '\u{1F4E1}',
  dollar: '\u{1F4B0}',
  'dollar-sign': '\u{1F4B0}',
  sparkle: '\u{2728}',
  sparkles: '\u{2728}',
}

function resolveIcon(icon) {
  if (!icon) return '\u{1F41F}'
  if (/\p{Emoji}/u.test(icon)) return icon
  return ICON_MAP[icon] || '\u{1F41F}'
}

const CATEGORY_STYLES = {
  pricing: { label: 'Pricing', classes: 'bg-[rgba(255,86,0,0.1)] text-[var(--color-fin-orange)]' },
  outbound: { label: 'Outbound', classes: 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]' },
  signals: { label: 'Signals', classes: 'bg-[rgba(170,0,255,0.1)] text-[#AA00FF]' },
  personalization: { label: 'Personalization', classes: 'bg-green-100 text-green-700' },
}

function categoryStyle(cat) {
  return CATEGORY_STYLES[cat] || { label: cat, classes: 'bg-black/5 text-[var(--color-text-secondary)]' }
}

const FIRMO_LABELS = {
  segments: 'Segments',
  contract_values: 'Contract Values',
  tenure: 'Tenure',
  industries: 'Industries',
  company_sizes: 'Company Sizes',
  regions: 'Regions',
}

function firmoLabel(key) {
  return FIRMO_LABELS[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function onOverlayClick(e) {
  if (e.target === e.currentTarget) emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="detail-modal">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
        @click="onOverlayClick"
      >
        <div
          class="bg-[var(--color-surface)] rounded-xl shadow-xl w-full max-w-2xl mx-4 max-h-[85vh] flex flex-col"
        >
          <!-- Header -->
          <div class="flex items-start justify-between px-6 py-5 border-b border-[var(--color-border)]">
            <div v-if="scenario" class="flex items-center gap-3 min-w-0">
              <span class="text-3xl shrink-0">{{ resolveIcon(scenario.icon) }}</span>
              <div class="min-w-0">
                <h2 class="text-lg font-semibold text-[var(--color-text)] truncate">
                  {{ scenario.name }}
                </h2>
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold mt-1',
                    categoryStyle(scenario.category).classes,
                  ]"
                >
                  {{ categoryStyle(scenario.category).label }}
                </span>
              </div>
            </div>
            <div v-else class="flex items-center gap-3">
              <div class="w-9 h-9 rounded bg-[var(--color-border)] animate-pulse shrink-0"></div>
              <div class="space-y-2">
                <div class="h-5 w-40 rounded bg-[var(--color-border)] animate-pulse"></div>
                <div class="h-4 w-20 rounded bg-[var(--color-border)] animate-pulse"></div>
              </div>
            </div>
            <button
              @click="emit('close')"
              class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] p-1 -mr-1 shrink-0 cursor-pointer"
              style="transition: var(--transition-fast)"
              aria-label="Close"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path
                  d="M15 5L5 15M5 5l10 10"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="px-6 py-5 overflow-y-auto flex-1">
            <!-- Loading -->
            <div v-if="loading" class="space-y-4">
              <div class="h-4 w-full rounded bg-[var(--color-border)] animate-pulse"></div>
              <div class="h-4 w-3/4 rounded bg-[var(--color-border)] animate-pulse"></div>
              <div class="grid grid-cols-2 gap-4 mt-6">
                <div class="h-28 rounded-lg bg-[var(--color-border)] animate-pulse"></div>
                <div class="h-28 rounded-lg bg-[var(--color-border)] animate-pulse"></div>
              </div>
            </div>

            <!-- Error -->
            <div v-else-if="error" class="text-center py-8">
              <p class="text-sm text-red-500">Failed to load scenario details</p>
              <p class="text-xs text-[var(--color-text-muted)] mt-1">{{ error }}</p>
            </div>

            <!-- Content -->
            <template v-else-if="scenario">
              <p class="text-sm text-[var(--color-text-secondary)] leading-relaxed mb-6">
                {{ scenario.description }}
              </p>

              <!-- Config Grid -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                <!-- Agent Config -->
                <div class="rounded-lg border border-[var(--color-border)] p-4">
                  <h3
                    class="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-3"
                  >
                    Agent Configuration
                  </h3>
                  <div class="flex items-baseline gap-2 mb-3">
                    <span class="text-2xl font-bold text-[var(--color-primary)]">
                      {{ scenario.agent_config?.count?.toLocaleString() }}
                    </span>
                    <span class="text-xs text-[var(--color-text-muted)]">agents</span>
                  </div>
                  <div class="flex flex-wrap gap-1.5">
                    <span
                      v-for="persona in scenario.agent_config?.persona_types"
                      :key="persona"
                      class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-[rgba(32,104,255,0.08)] text-[var(--color-primary)] border border-[rgba(32,104,255,0.15)]"
                    >
                      {{ persona }}
                    </span>
                  </div>
                </div>

                <!-- Simulation Config -->
                <div class="rounded-lg border border-[var(--color-border)] p-4">
                  <h3
                    class="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-3"
                  >
                    Simulation Parameters
                  </h3>
                  <div class="space-y-2.5">
                    <div class="flex justify-between text-sm">
                      <span class="text-[var(--color-text-secondary)]">Duration</span>
                      <span class="font-medium text-[var(--color-text)]">
                        {{ scenario.simulation_config?.total_hours }}h
                      </span>
                    </div>
                    <div class="flex justify-between text-sm">
                      <span class="text-[var(--color-text-secondary)]">Round Length</span>
                      <span class="font-medium text-[var(--color-text)]">
                        {{ scenario.simulation_config?.minutes_per_round }}min
                      </span>
                    </div>
                    <div class="flex justify-between text-sm">
                      <span class="text-[var(--color-text-secondary)]">Platform</span>
                      <span class="font-medium text-[var(--color-text)] capitalize">
                        {{ scenario.simulation_config?.platform_mode }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Firmographic Mix -->
              <div v-if="scenario.agent_config?.firmographic_mix" class="mb-6">
                <h3
                  class="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-3"
                >
                  Firmographic Mix
                </h3>
                <div class="space-y-3">
                  <div
                    v-for="(values, key) in scenario.agent_config.firmographic_mix"
                    :key="key"
                  >
                    <p class="text-xs text-[var(--color-text-muted)] mb-1.5">
                      {{ firmoLabel(key) }}
                    </p>
                    <div class="flex flex-wrap gap-1.5">
                      <span
                        v-for="val in values"
                        :key="val"
                        class="inline-flex items-center px-2 py-0.5 rounded text-xs bg-black/[0.04] text-[var(--color-text-secondary)] border border-[var(--color-border)]"
                      >
                        {{ val }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Expected Outputs -->
              <div v-if="scenario.expected_outputs?.length">
                <h3
                  class="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-3"
                >
                  Expected Outputs
                </h3>
                <ul class="space-y-2">
                  <li
                    v-for="(output, i) in scenario.expected_outputs"
                    :key="i"
                    class="flex items-start gap-2 text-sm text-[var(--color-text-secondary)]"
                  >
                    <svg
                      class="w-4 h-4 mt-0.5 text-[var(--color-primary)] shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      stroke-width="2"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    {{ output }}
                  </li>
                </ul>
              </div>
            </template>
          </div>

          <!-- Footer -->
          <div
            v-if="scenario && !loading"
            class="px-6 py-4 border-t border-[var(--color-border)] flex items-center justify-end gap-3"
          >
            <button
              @click="emit('close')"
              class="text-sm font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text)] px-4 py-2 rounded-lg cursor-pointer"
              style="transition: var(--transition-fast)"
            >
              Close
            </button>
            <button
              @click="emit('launch', scenarioId)"
              class="inline-flex items-center gap-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white text-sm font-semibold px-5 py-2.5 rounded-lg cursor-pointer"
              style="transition: var(--transition-fast)"
            >
              Configure & Run
              <svg
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.detail-modal-enter-active,
.detail-modal-leave-active {
  transition: opacity var(--transition-fast);
}
.detail-modal-enter-active > div,
.detail-modal-leave-active > div {
  transition: transform var(--transition-fast);
}
.detail-modal-enter-from,
.detail-modal-leave-to {
  opacity: 0;
}
.detail-modal-enter-from > div {
  transform: scale(0.96);
}
</style>
