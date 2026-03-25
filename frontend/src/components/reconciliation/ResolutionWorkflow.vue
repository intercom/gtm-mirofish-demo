<script setup>
import { ref, computed } from 'vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import AppBadge from '../common/AppBadge.vue'
import AppButton from '../common/AppButton.vue'

const props = defineProps({
  discrepancy: {
    type: Object,
    default: null,
  },
  open: {
    type: Boolean,
    default: false,
  },
  resolving: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'resolve'])

const resolutionType = ref('auto')
const manualValue = ref('')
const notes = ref('')
const showConfirm = ref(false)

const resolutionOptions = [
  {
    value: 'auto',
    label: 'Auto-resolve',
    description: 'Within tolerance threshold — accept closest value',
    icon: '⚡',
  },
  {
    value: 'manual',
    label: 'Manual correction',
    description: 'Enter the correct value manually',
    icon: '✏️',
  },
  {
    value: 'escalate',
    label: 'Escalate to Finance',
    description: 'Flag for finance team review',
    icon: '🔔',
  },
  {
    value: 'timing',
    label: 'Timing lag',
    description: 'Will resolve on next sync cycle',
    icon: '⏱️',
  },
]

const sourceValues = computed(() => {
  if (!props.discrepancy) return []
  return [
    { name: 'Salesforce', value: props.discrepancy.salesforce_value, color: '#2068FF' },
    { name: 'Billing', value: props.discrepancy.billing_value, color: '#ff5600' },
    { name: 'Snowflake', value: props.discrepancy.snowflake_value, color: '#AA00FF' },
  ]
})

const maxDifference = computed(() => {
  if (!props.discrepancy) return 0
  const vals = sourceValues.value.map((s) => s.value ?? 0)
  return Math.max(...vals) - Math.min(...vals)
})

const severityVariant = computed(() => {
  if (maxDifference.value > 1000) return 'error'
  if (maxDifference.value > 100) return 'warning'
  return 'success'
})

const severityLabel = computed(() => {
  if (maxDifference.value > 1000) return 'Critical'
  if (maxDifference.value > 100) return 'Medium'
  return 'Low'
})

const canResolve = computed(() => {
  if (resolutionType.value === 'manual' && !manualValue.value.trim()) return false
  return true
})

const resolutionHistory = computed(() => {
  return props.discrepancy?.resolution_history ?? []
})

function requestResolve() {
  showConfirm.value = true
}

function confirmResolve() {
  emit('resolve', {
    discrepancy_id: props.discrepancy?.id,
    type: resolutionType.value,
    manual_value: resolutionType.value === 'manual' ? parseFloat(manualValue.value) : null,
    notes: notes.value.trim() || null,
  })
  resetForm()
}

function resetForm() {
  resolutionType.value = 'auto'
  manualValue.value = ''
  notes.value = ''
  showConfirm.value = false
}

function close() {
  resetForm()
  emit('close')
}

function formatCurrency(val) {
  if (val == null) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <Teleport to="body">
    <Transition name="slideover-backdrop">
      <div
        v-if="open"
        class="fixed inset-0 z-40 bg-black/40"
        @click="close"
      />
    </Transition>

    <Transition name="slideover">
      <aside
        v-if="open && discrepancy"
        class="fixed inset-y-0 right-0 z-50 w-full max-w-xl flex flex-col bg-[var(--color-surface)] shadow-2xl"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
          <div>
            <h2 class="text-lg font-semibold text-[var(--color-text)]">Resolve Discrepancy</h2>
            <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
              {{ discrepancy.account_name ?? discrepancy.id }}
            </p>
          </div>
          <button
            class="p-1.5 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-black/5 transition-colors cursor-pointer"
            aria-label="Close"
            @click="close"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Scrollable body -->
        <div class="flex-1 overflow-y-auto px-6 py-5 space-y-6">

          <!-- Severity + Account -->
          <div class="flex items-center gap-3">
            <AppBadge :variant="severityVariant">{{ severityLabel }}</AppBadge>
            <span class="text-sm text-[var(--color-text-secondary)]">
              Difference: <strong class="text-[var(--color-text)]">{{ formatCurrency(maxDifference) }}</strong>
            </span>
          </div>

          <!-- Source values comparison -->
          <div class="rounded-lg border border-[var(--color-border)] overflow-hidden">
            <div class="px-4 py-2.5 bg-black/[0.02] border-b border-[var(--color-border)]">
              <span class="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide">Source Values</span>
            </div>
            <div class="divide-y divide-[var(--color-border)]">
              <div
                v-for="source in sourceValues"
                :key="source.name"
                class="flex items-center justify-between px-4 py-3"
              >
                <div class="flex items-center gap-2">
                  <span class="w-2.5 h-2.5 rounded-full shrink-0" :style="{ backgroundColor: source.color }" />
                  <span class="text-sm text-[var(--color-text)]">{{ source.name }}</span>
                </div>
                <span class="text-sm font-semibold tabular-nums text-[var(--color-text)]">
                  {{ formatCurrency(source.value) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Resolution type picker -->
          <div>
            <label class="block text-xs font-semibold text-[var(--color-text)] mb-2">Resolution Method</label>
            <div class="grid gap-2">
              <label
                v-for="option in resolutionOptions"
                :key="option.value"
                :class="[
                  'flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors',
                  resolutionType === option.value
                    ? 'border-[var(--color-primary)] bg-[rgba(32,104,255,0.04)]'
                    : 'border-[var(--color-border)] hover:border-[var(--color-primary-hover)]',
                ]"
              >
                <input
                  v-model="resolutionType"
                  type="radio"
                  :value="option.value"
                  class="mt-0.5 accent-[var(--color-primary)]"
                />
                <div class="flex-1 min-w-0">
                  <span class="text-sm font-medium text-[var(--color-text)]">
                    {{ option.icon }} {{ option.label }}
                  </span>
                  <p class="text-xs text-[var(--color-text-muted)] mt-0.5">{{ option.description }}</p>
                </div>
              </label>
            </div>
          </div>

          <!-- Manual value input (shown only for manual resolution) -->
          <Transition name="expand">
            <div v-if="resolutionType === 'manual'">
              <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Correct Value ($)</label>
              <input
                v-model="manualValue"
                type="number"
                step="0.01"
                placeholder="Enter correct MRR amount"
                class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-colors"
              />
            </div>
          </Transition>

          <!-- Notes -->
          <div>
            <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Resolution Notes</label>
            <textarea
              v-model="notes"
              rows="3"
              placeholder="Explain the resolution (optional)"
              class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-colors resize-y"
            />
          </div>

          <!-- Resolution history -->
          <div v-if="resolutionHistory.length">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide">Resolution History</span>
              <AppBadge variant="neutral">{{ resolutionHistory.length }}</AppBadge>
            </div>
            <div class="space-y-2">
              <div
                v-for="(entry, idx) in resolutionHistory"
                :key="idx"
                class="rounded-lg border border-[var(--color-border)] px-3 py-2.5"
              >
                <div class="flex items-center justify-between">
                  <span class="text-xs font-medium text-[var(--color-text)]">{{ entry.type }}</span>
                  <span class="text-xs text-[var(--color-text-muted)]">{{ formatDate(entry.resolved_at) }}</span>
                </div>
                <p v-if="entry.notes" class="text-xs text-[var(--color-text-secondary)] mt-1">{{ entry.notes }}</p>
                <p v-if="entry.resolved_by" class="text-xs text-[var(--color-text-muted)] mt-0.5">
                  by {{ entry.resolved_by }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer actions -->
        <div class="flex items-center justify-end gap-3 px-6 py-4 border-t border-[var(--color-border)]">
          <AppButton variant="ghost" size="sm" @click="close">Cancel</AppButton>
          <AppButton
            size="sm"
            :disabled="!canResolve"
            :loading="resolving"
            @click="requestResolve"
          >
            Resolve
          </AppButton>
        </div>
      </aside>
    </Transition>
  </Teleport>

  <!-- Confirm dialog -->
  <ConfirmDialog
    v-model="showConfirm"
    title="Confirm Resolution"
    :message="`Mark this discrepancy as resolved via '${resolutionOptions.find(o => o.value === resolutionType)?.label}'?`"
    confirm-label="Resolve"
    @confirm="confirmResolve"
  />
</template>

<style scoped>
/* Slide-over panel animation */
.slideover-enter-active,
.slideover-leave-active {
  transition: transform 0.3s ease;
}
.slideover-enter-from,
.slideover-leave-to {
  transform: translateX(100%);
}

/* Backdrop fade */
.slideover-backdrop-enter-active,
.slideover-backdrop-leave-active {
  transition: opacity 0.2s ease;
}
.slideover-backdrop-enter-from,
.slideover-backdrop-leave-to {
  opacity: 0;
}

/* Expand transition for manual value input */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}
.expand-enter-to,
.expand-leave-from {
  max-height: 120px;
}
</style>
