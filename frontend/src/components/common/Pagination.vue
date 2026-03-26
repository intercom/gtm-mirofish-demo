<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentPage: { type: Number, required: true },
  totalPages: { type: Number, required: true },
  total: { type: Number, default: 0 },
  /** Maximum number of page buttons to show (odd number recommended) */
  maxVisible: { type: Number, default: 5 },
})

const emit = defineEmits(['update:currentPage'])

const pages = computed(() => {
  const { currentPage, totalPages, maxVisible } = props
  if (totalPages <= maxVisible) {
    return Array.from({ length: totalPages }, (_, i) => i + 1)
  }

  const half = Math.floor(maxVisible / 2)
  let start = Math.max(1, currentPage - half)
  let end = start + maxVisible - 1

  if (end > totalPages) {
    end = totalPages
    start = Math.max(1, end - maxVisible + 1)
  }

  const result = []
  for (let i = start; i <= end; i++) {
    result.push(i)
  }
  return result
})

function goTo(page) {
  if (page >= 1 && page <= props.totalPages && page !== props.currentPage) {
    emit('update:currentPage', page)
  }
}
</script>

<template>
  <div v-if="totalPages > 1" class="flex items-center justify-between gap-4 py-3">
    <span class="text-xs text-[var(--color-text-muted)]">
      {{ total }} item{{ total === 1 ? '' : 's' }}
    </span>

    <div class="flex items-center gap-1">
      <!-- Prev -->
      <button
        :disabled="currentPage <= 1"
        class="pagination-btn"
        @click="goTo(currentPage - 1)"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
        </svg>
      </button>

      <!-- First + ellipsis -->
      <template v-if="pages[0] > 1">
        <button class="pagination-btn" @click="goTo(1)">1</button>
        <span v-if="pages[0] > 2" class="px-1 text-xs text-[var(--color-text-muted)]">&hellip;</span>
      </template>

      <!-- Page numbers -->
      <button
        v-for="page in pages"
        :key="page"
        class="pagination-btn"
        :class="{ active: page === currentPage }"
        @click="goTo(page)"
      >
        {{ page }}
      </button>

      <!-- Last + ellipsis -->
      <template v-if="pages[pages.length - 1] < totalPages">
        <span v-if="pages[pages.length - 1] < totalPages - 1" class="px-1 text-xs text-[var(--color-text-muted)]">&hellip;</span>
        <button class="pagination-btn" @click="goTo(totalPages)">{{ totalPages }}</button>
      </template>

      <!-- Next -->
      <button
        :disabled="currentPage >= totalPages"
        class="pagination-btn"
        @click="goTo(currentPage + 1)"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.pagination-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  padding: 0 0.375rem;
  border-radius: var(--radius, 0.5rem);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-fast, 150ms) ease;
}
.pagination-btn:hover:not(:disabled):not(.active) {
  border-color: #2068FF;
  color: #2068FF;
  background: rgba(32, 104, 255, 0.06);
}
.pagination-btn.active {
  background: #2068FF;
  border-color: #2068FF;
  color: #fff;
}
.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
