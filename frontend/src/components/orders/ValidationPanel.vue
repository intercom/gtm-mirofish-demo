<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  checks: {
    type: Array,
    default: () => [],
    validator: (v) =>
      v.every(
        (c) =>
          c.field &&
          ['pass', 'fail', 'warning'].includes(c.status) &&
          c.message &&
          c.category
      ),
  },
})

const expanded = ref(new Set())

const categories = ['Product Validation', 'Pricing Validation', 'Contract Validation', 'Compliance']

const groupedChecks = computed(() => {
  const groups = {}
  for (const cat of categories) {
    const items = props.checks.filter((c) => c.category === cat)
    if (items.length) groups[cat] = items
  }
  // Include any checks with categories not in the predefined list
  for (const check of props.checks) {
    if (!categories.includes(check.category)) {
      if (!groups[check.category]) groups[check.category] = []
      groups[check.category].push(check)
    }
  }
  return groups
})

const issueCount = computed(() =>
  props.checks.filter((c) => c.status === 'fail' || c.status === 'warning').length
)

const failCount = computed(() =>
  props.checks.filter((c) => c.status === 'fail').length
)

const allPassed = computed(() => issueCount.value === 0 && props.checks.length > 0)

function toggleExpanded(checkId) {
  if (expanded.value.has(checkId)) {
    expanded.value.delete(checkId)
  } else {
    expanded.value.add(checkId)
  }
}

function checkKey(check, index) {
  return `${check.category}-${check.field}-${index}`
}
</script>

<template>
  <div class="bg-[--color-surface] border border-[--color-border] rounded-lg overflow-hidden">
    <!-- Overall Status Header -->
    <div
      :class="[
        'px-5 py-4 flex items-center gap-3 border-b border-[--color-border]',
        allPassed ? 'bg-[--color-success-light]' : 'bg-[--color-error-light]',
      ]"
    >
      <!-- Status icon -->
      <div
        :class="[
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          allPassed ? 'bg-[--color-success] text-white' : 'bg-[--color-error] text-white',
        ]"
      >
        <svg v-if="allPassed" class="w-4 h-4" viewBox="0 0 16 16" fill="none">
          <path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <svg v-else class="w-4 h-4" viewBox="0 0 16 16" fill="none">
          <path d="M8 4.5V8.5M8 11V11.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
      </div>
      <div>
        <p v-if="allPassed" class="text-sm font-semibold text-[--color-success]">
          All Checks Passed
        </p>
        <template v-else>
          <p class="text-sm font-semibold" :class="failCount > 0 ? 'text-[--color-error]' : 'text-[--color-warning]'">
            {{ issueCount }} {{ issueCount === 1 ? 'Issue' : 'Issues' }} Found
          </p>
          <p class="text-xs text-[--color-text-secondary] mt-0.5">
            {{ failCount }} failed, {{ issueCount - failCount }} warnings
          </p>
        </template>
      </div>
      <p v-if="checks.length" class="ml-auto text-xs text-[--color-text-muted]">
        {{ checks.length }} checks run
      </p>
    </div>

    <!-- Empty state -->
    <div v-if="!checks.length" class="px-5 py-8 text-center text-[--color-text-muted] text-sm">
      No validation checks to display.
    </div>

    <!-- Grouped checks -->
    <div v-for="(items, category) in groupedChecks" :key="category" class="border-b border-[--color-border] last:border-b-0">
      <!-- Category header -->
      <div class="px-5 py-2.5 bg-[--color-tint]">
        <h3 class="text-xs font-semibold uppercase tracking-wide text-[--color-text-secondary]">
          {{ category }}
        </h3>
      </div>

      <!-- Check rows -->
      <ul class="divide-y divide-[--color-border]">
        <li v-for="(check, idx) in items" :key="checkKey(check, idx)">
          <button
            v-if="check.status !== 'pass' && check.remediation"
            class="w-full px-5 py-3 flex items-start gap-3 text-left hover:bg-[--color-tint] transition-colors cursor-pointer"
            @click="toggleExpanded(checkKey(check, idx))"
          >
            <span class="flex-shrink-0 mt-0.5">
              <!-- Fail icon -->
              <svg v-if="check.status === 'fail'" class="w-4 h-4 text-[--color-error]" viewBox="0 0 16 16" fill="none">
                <path d="M4.5 4.5L11.5 11.5M11.5 4.5L4.5 11.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
              </svg>
              <!-- Warning icon -->
              <svg v-else class="w-4 h-4 text-[--color-warning]" viewBox="0 0 16 16" fill="none">
                <path d="M8 2L14.5 13H1.5L8 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
                <path d="M8 7V9.5M8 11.5V12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
              </svg>
            </span>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-[--color-text]">{{ check.field }}</span>
                <span
                  :class="[
                    'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase',
                    check.status === 'fail' ? 'bg-[--color-error-light] text-[--color-error]' : 'bg-[--color-warning-light] text-[--color-warning]',
                  ]"
                >
                  {{ check.status }}
                </span>
              </div>
              <p class="text-xs text-[--color-text-secondary] mt-0.5">{{ check.message }}</p>
            </div>
            <svg
              :class="[
                'w-4 h-4 text-[--color-text-muted] flex-shrink-0 mt-1 transition-transform duration-150',
                expanded.has(checkKey(check, idx)) && 'rotate-180',
              ]"
              viewBox="0 0 16 16"
              fill="none"
            >
              <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>

          <!-- Non-expandable row (pass, or fail/warning without remediation) -->
          <div
            v-else
            class="px-5 py-3 flex items-start gap-3"
          >
            <span class="flex-shrink-0 mt-0.5">
              <!-- Pass icon -->
              <svg v-if="check.status === 'pass'" class="w-4 h-4 text-[--color-success]" viewBox="0 0 16 16" fill="none">
                <path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <!-- Fail icon -->
              <svg v-else-if="check.status === 'fail'" class="w-4 h-4 text-[--color-error]" viewBox="0 0 16 16" fill="none">
                <path d="M4.5 4.5L11.5 11.5M11.5 4.5L4.5 11.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
              </svg>
              <!-- Warning icon -->
              <svg v-else class="w-4 h-4 text-[--color-warning]" viewBox="0 0 16 16" fill="none">
                <path d="M8 2L14.5 13H1.5L8 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
                <path d="M8 7V9.5M8 11.5V12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
              </svg>
            </span>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-[--color-text]">{{ check.field }}</span>
                <span
                  :class="[
                    'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase',
                    {
                      'bg-[--color-success-light] text-[--color-success]': check.status === 'pass',
                      'bg-[--color-error-light] text-[--color-error]': check.status === 'fail',
                      'bg-[--color-warning-light] text-[--color-warning]': check.status === 'warning',
                    },
                  ]"
                >
                  {{ check.status }}
                </span>
              </div>
              <p class="text-xs text-[--color-text-secondary] mt-0.5">{{ check.message }}</p>
            </div>
          </div>

          <!-- Expandable remediation section -->
          <Transition name="expand">
            <div
              v-if="check.remediation && expanded.has(checkKey(check, idx))"
              class="px-5 pb-3 pl-12"
            >
              <div class="rounded-md bg-[--color-tint] px-3 py-2.5 text-xs text-[--color-text-secondary] leading-relaxed">
                <p class="font-semibold text-[--color-text] mb-1">Remediation</p>
                {{ check.remediation }}
              </div>
            </div>
          </Transition>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.15s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 200px;
}
</style>
