<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  /** Agent name/identifier */
  agentName: { type: String, default: '' },
  /** The clean message (action summary) */
  message: { type: String, default: '' },
  /** Reasoning trace object with keys: thought, observation, inference, decision, justification */
  trace: {
    type: Object,
    default: () => ({}),
  },
  /** Start in transparent mode */
  defaultTransparent: { type: Boolean, default: false },
})

defineEmits(['toggle-view'])

const transparent = ref(props.defaultTransparent)

const sections = computed(() => {
  const t = props.trace
  return [
    { key: 'thought', label: 'Thought', icon: '\uD83D\uDCA1', content: t.thought, italic: true },
    { key: 'observation', label: 'Observation', icon: '\uD83D\uDC41\uFE0F', content: t.observation },
    { key: 'inference', label: 'Inference', icon: '\uD83E\uDDE0', content: t.inference },
    { key: 'decision', label: 'Decision', icon: '\u2714\uFE0F', content: t.decision },
    { key: 'justification', label: 'Justification', icon: '\uD83D\uDCCB', content: t.justification },
  ].filter(s => s.content)
})

const hasTrace = computed(() => sections.value.length > 0)

// Track which sections are expanded (all open by default)
const expandedSections = ref(new Set(['thought', 'observation', 'inference', 'decision', 'justification']))

function toggleSection(key) {
  if (expandedSections.value.has(key)) {
    expandedSections.value.delete(key)
  } else {
    expandedSections.value.add(key)
  }
}

function toggleView() {
  transparent.value = !transparent.value
}

// Extract assumptions from text — lines starting with "Assumption:" or "[assumption]"
function extractAssumptions(text) {
  if (!text) return { clean: text, assumptions: [] }
  const lines = text.split('\n')
  const assumptions = []
  const clean = []
  for (const line of lines) {
    if (/^\s*(\[assumption\]|assumption:)/i.test(line)) {
      assumptions.push(line.replace(/^\s*(\[assumption\]|assumption:)\s*/i, ''))
    } else {
      clean.push(line)
    }
  }
  return { clean: clean.join('\n'), assumptions }
}

// Confidence from trace metadata (0-1 scale)
function getConfidence(key) {
  const conf = props.trace.confidence
  if (!conf) return null
  if (typeof conf === 'number') return conf
  if (typeof conf === 'object') return conf[key] ?? null
  return null
}

function confidenceLabel(value) {
  if (value >= 0.8) return 'High'
  if (value >= 0.5) return 'Medium'
  return 'Low'
}

function confidenceColor(value) {
  if (value >= 0.8) return 'text-[var(--color-success)]'
  if (value >= 0.5) return 'text-[var(--color-warning)]'
  return 'text-[var(--color-error)]'
}
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)]">
      <div class="flex items-center gap-2 min-w-0">
        <span v-if="agentName" class="text-sm font-medium text-[var(--color-text)] truncate">
          {{ agentName }}
        </span>
      </div>
      <button
        v-if="hasTrace"
        class="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors shrink-0"
        :class="transparent
          ? 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]'
          : 'bg-[var(--color-tint)] text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
        @click="toggleView"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <template v-if="transparent">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
            <circle cx="12" cy="12" r="3" />
          </template>
          <template v-else>
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
            <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
            <line x1="1" y1="1" x2="23" y2="23" />
          </template>
        </svg>
        {{ transparent ? 'Transparent' : 'Clean' }}
      </button>
    </div>

    <!-- Clean view: just the message -->
    <div v-if="!transparent" class="px-4 py-3">
      <p class="text-sm text-[var(--color-text)]">{{ message }}</p>
    </div>

    <!-- Transparent view: full reasoning trace -->
    <div v-else class="divide-y divide-[var(--color-border)]">
      <!-- Original message context -->
      <div v-if="message" class="px-4 py-3 bg-[var(--color-tint)]">
        <p class="text-xs text-[var(--color-text-muted)] mb-1">Message</p>
        <p class="text-sm text-[var(--color-text)]">{{ message }}</p>
      </div>

      <!-- Reasoning sections -->
      <div v-for="section in sections" :key="section.key">
        <button
          class="w-full flex items-center gap-2.5 px-4 py-2.5 text-left hover:bg-[var(--color-tint)] transition-colors"
          @click="toggleSection(section.key)"
        >
          <span class="text-base shrink-0">{{ section.icon }}</span>
          <span class="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)] flex-1">
            {{ section.label }}
          </span>

          <!-- Confidence indicator -->
          <span
            v-if="getConfidence(section.key) !== null"
            class="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-[var(--color-tint)]"
            :class="confidenceColor(getConfidence(section.key))"
          >
            {{ confidenceLabel(getConfidence(section.key)) }}
            {{ Math.round(getConfidence(section.key) * 100) }}%
          </span>

          <!-- Expand/collapse chevron -->
          <svg
            width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            class="shrink-0 text-[var(--color-text-muted)] transition-transform duration-200"
            :class="expandedSections.has(section.key) ? 'rotate-180' : ''"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>

        <!-- Section content (collapsible) -->
        <Transition name="section">
          <div v-show="expandedSections.has(section.key)" class="px-4 pb-3 pl-11">
            <p
              class="text-sm text-[var(--color-text-secondary)] whitespace-pre-line"
              :class="section.italic ? 'italic' : ''"
            >
              {{ extractAssumptions(section.content).clean }}
            </p>

            <!-- Assumptions callout -->
            <div
              v-for="(assumption, idx) in extractAssumptions(section.content).assumptions"
              :key="idx"
              class="flex items-start gap-1.5 mt-2 px-2.5 py-1.5 rounded-md bg-[rgba(245,158,11,0.08)] border border-[rgba(245,158,11,0.2)]"
            >
              <svg
                width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-warning)"
                stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                class="shrink-0 mt-0.5"
              >
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <span class="text-xs text-[var(--color-warning)]">{{ assumption }}</span>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Empty state when no trace sections -->
      <div v-if="!sections.length" class="px-4 py-6 text-center">
        <p class="text-sm text-[var(--color-text-muted)]">No reasoning trace available</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-enter-active,
.section-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.section-enter-from,
.section-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.section-enter-to,
.section-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
