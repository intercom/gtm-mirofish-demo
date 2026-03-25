<script setup>
import { computed } from 'vue'
import Badge from '../common/Badge.vue'
import Card from '../common/Card.vue'

const props = defineProps({
  quote: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['approve', 'reject', 'edit'])

const STATUS_VARIANTS = {
  Draft: 'neutral',
  Review: 'warning',
  Approved: 'success',
  Rejected: 'error',
}

const statusVariant = computed(() => STATUS_VARIANTS[props.quote.status] ?? 'neutral')

const canApprove = computed(() => props.quote.status === 'Review')
const canReject = computed(() => props.quote.status === 'Review')
const canEdit = computed(() => ['Draft', 'Review'].includes(props.quote.status))

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value ?? 0)
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const isExpired = computed(() => {
  if (!props.quote.expiry_date) return false
  return new Date(props.quote.expiry_date) < new Date()
})
</script>

<template>
  <Card>
    <!-- Header -->
    <div class="flex flex-wrap items-start justify-between gap-4 mb-6">
      <div>
        <div class="flex items-center gap-3 mb-1">
          <h2 class="text-xl font-semibold text-[var(--color-text)]">
            {{ quote.quote_number }}
          </h2>
          <Badge :variant="statusVariant">{{ quote.status }}</Badge>
        </div>
        <p class="text-sm text-[var(--color-text-secondary)]">
          {{ quote.account_name }}
        </p>
      </div>
      <div class="text-right text-sm text-[var(--color-text-secondary)]">
        <p>Created: {{ formatDate(quote.created_at) }}</p>
        <p :class="{ 'text-[var(--color-error)]': isExpired }">
          Expires: {{ formatDate(quote.expiry_date) }}
        </p>
      </div>
    </div>

    <!-- Line Items Table -->
    <div class="overflow-x-auto -mx-6">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-y border-[var(--color-border)]">
            <th class="text-left font-semibold text-[var(--color-text-secondary)] px-6 py-3">
              Product
            </th>
            <th class="text-right font-semibold text-[var(--color-text-secondary)] px-6 py-3">
              Qty
            </th>
            <th class="text-right font-semibold text-[var(--color-text-secondary)] px-6 py-3">
              List Price
            </th>
            <th class="text-right font-semibold text-[var(--color-text-secondary)] px-6 py-3">
              Discount
            </th>
            <th class="text-right font-semibold text-[var(--color-text-secondary)] px-6 py-3">
              Net Price
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, idx) in quote.line_items"
            :key="idx"
            :class="idx % 2 === 1 ? 'bg-[var(--color-tint)]' : ''"
          >
            <td class="px-6 py-3 text-[var(--color-text)]">{{ item.product }}</td>
            <td class="px-6 py-3 text-right text-[var(--color-text)]">{{ item.quantity }}</td>
            <td class="px-6 py-3 text-right text-[var(--color-text)]">{{ formatCurrency(item.list_price) }}</td>
            <td class="px-6 py-3 text-right text-[var(--color-text-secondary)]">{{ item.discount_percent }}%</td>
            <td class="px-6 py-3 text-right font-medium text-[var(--color-text)]">{{ formatCurrency(item.net_price) }}</td>
          </tr>
          <tr v-if="!quote.line_items?.length">
            <td colspan="5" class="px-6 py-8 text-center text-[var(--color-text-muted)]">
              No line items
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Totals -->
    <div class="flex justify-end mt-4 border-t border-[var(--color-border)] pt-4">
      <div class="w-64 space-y-2 text-sm">
        <div class="flex justify-between text-[var(--color-text-secondary)]">
          <span>Subtotal</span>
          <span>{{ formatCurrency(quote.subtotal) }}</span>
        </div>
        <div class="flex justify-between text-[var(--color-text-secondary)]">
          <span>Total Discount</span>
          <span class="text-[var(--color-error)]">-{{ formatCurrency(quote.total_discount) }}</span>
        </div>
        <div class="flex justify-between pt-2 border-t border-[var(--color-border)] text-lg font-bold text-[var(--color-text)]">
          <span>Total</span>
          <span>{{ formatCurrency(quote.total_price) }}</span>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div
      v-if="canApprove || canReject || canEdit"
      class="flex justify-end gap-3 mt-6 pt-4 border-t border-[var(--color-border)]"
    >
      <button
        v-if="canReject"
        class="px-4 py-2 text-sm font-semibold rounded-lg cursor-pointer text-white bg-[var(--color-error)] hover:opacity-90"
        style="transition: var(--transition-fast)"
        @click="emit('reject', quote.id)"
      >
        Reject
      </button>
      <button
        v-if="canEdit"
        class="px-4 py-2 text-sm font-semibold rounded-lg cursor-pointer text-white bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)]"
        style="transition: var(--transition-fast)"
        @click="emit('edit', quote.id)"
      >
        Edit
      </button>
      <button
        v-if="canApprove"
        class="px-4 py-2 text-sm font-semibold rounded-lg cursor-pointer text-white bg-[var(--color-success)] hover:opacity-90"
        style="transition: var(--transition-fast)"
        @click="emit('approve', quote.id)"
      >
        Approve
      </button>
    </div>
  </Card>
</template>
