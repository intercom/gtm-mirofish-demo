<script setup>
defineProps({
  account: {
    type: Object,
    required: true,
    validator: (v) => v && typeof v.name === 'string',
  },
})

defineEmits(['click'])

import { useLocale } from '../../composables/useLocale'

const { formatCurrency: fmtCurrency, formatDate: fmtDate } = useLocale()

const tierColors = {
  Essential: 'bg-black/5 text-[--color-text-secondary]',
  Advanced: 'bg-[rgba(32,104,255,0.1)] text-[--color-primary]',
  Expert: 'bg-[rgba(170,0,255,0.1)] text-[--color-accent]',
}

function formatCurrency(value) {
  if (value == null) return '—'
  return fmtCurrency(value, 'USD', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function healthColor(score) {
  if (score < 30) return 'bg-[--color-error]'
  if (score <= 70) return 'bg-[--color-warning]'
  return 'bg-[--color-success]'
}

function healthTrackColor(score) {
  if (score < 30) return 'bg-[--color-error-light]'
  if (score <= 70) return 'bg-[--color-warning-light]'
  return 'bg-[--color-success-light]'
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return fmtDate(dateStr, { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<template>
  <div
    class="account-card bg-[--card-bg] border border-[--color-border] rounded-lg p-5 cursor-pointer transition-all duration-300"
    @click="$emit('click', account)"
  >
    <!-- Header: Name + Badges -->
    <div class="flex items-start justify-between gap-3 mb-3">
      <h3 class="text-base font-semibold text-[--color-text] leading-tight truncate">
        {{ account.name }}
      </h3>
      <div class="flex items-center gap-1.5 shrink-0">
        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-black/5 text-[--color-text-secondary]">
          {{ account.industry }}
        </span>
        <span
          :class="[
            'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold',
            tierColors[account.tier] || tierColors.Essential,
          ]"
        >
          {{ account.tier }}
        </span>
      </div>
    </div>

    <!-- ARR + Health Score -->
    <div class="flex items-center justify-between gap-4 mb-3">
      <div>
        <div class="text-xs text-[--color-text-muted] mb-0.5">ARR</div>
        <div class="text-lg font-bold text-[--color-text]">{{ formatCurrency(account.arr) }}</div>
      </div>
      <div class="flex-1 max-w-[140px]">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs text-[--color-text-muted]">Health</span>
          <span class="text-xs font-semibold text-[--color-text]">{{ account.health_score }}</span>
        </div>
        <div :class="['h-1.5 rounded-full overflow-hidden', healthTrackColor(account.health_score)]">
          <div
            :class="['h-full rounded-full transition-all duration-500', healthColor(account.health_score)]"
            :style="{ width: `${Math.min(100, Math.max(0, account.health_score))}%` }"
          />
        </div>
      </div>
    </div>

    <!-- Footer: Owner + Renewal -->
    <div class="flex items-center justify-between text-xs text-[--color-text-muted] pt-3 border-t border-[--color-border]">
      <span v-if="account.owner">{{ account.owner }}</span>
      <span v-if="account.renewal_date">Renews {{ formatDate(account.renewal_date) }}</span>
    </div>
  </div>
</template>

<style scoped>
.account-card {
  box-shadow: var(--card-shadow);
}
.account-card:hover {
  box-shadow: var(--card-shadow-hover);
  border-color: var(--color-border-strong);
}
</style>
