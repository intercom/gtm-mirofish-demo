<script setup>
import { ref, onErrorCaptured, watch } from 'vue'
import { useRoute } from 'vue-router'

defineProps({
  title: { type: String, default: 'Something went wrong' },
  message: { type: String, default: 'An unexpected error occurred. Please try again.' },
})

const route = useRoute()
const error = ref(null)
const errorInfo = ref(null)

onErrorCaptured((err, _instance, info) => {
  error.value = err
  errorInfo.value = info
  console.error('[ErrorBoundary]', err, info)
  return false
})

watch(() => route.fullPath, () => {
  error.value = null
  errorInfo.value = null
})

function reset() {
  error.value = null
  errorInfo.value = null
}
</script>

<template>
  <slot v-if="!error" />
  <div v-else class="flex flex-col items-center justify-center py-16 px-4 text-center">
    <div class="w-14 h-14 rounded-full bg-red-50 dark:bg-red-500/10 flex items-center justify-center mb-4">
      <svg class="w-7 h-7 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
      </svg>
    </div>
    <h3 class="text-base font-semibold text-[var(--color-text)] mb-1">{{ title }}</h3>
    <p class="text-sm text-[var(--color-text-muted)] mb-6 max-w-sm">{{ message }}</p>

    <div v-if="import.meta.env.DEV" class="mb-6 max-w-lg w-full text-left">
      <details class="rounded-lg border border-red-200 dark:border-red-500/20 bg-red-50/50 dark:bg-red-500/5 overflow-hidden">
        <summary class="px-4 py-2 text-xs font-medium text-red-600 dark:text-red-400 cursor-pointer select-none">
          Error details (dev only)
        </summary>
        <pre class="px-4 py-3 text-xs text-red-700 dark:text-red-300 overflow-x-auto whitespace-pre-wrap break-words">{{ error?.stack || error?.message || String(error) }}</pre>
        <p v-if="errorInfo" class="px-4 pb-3 text-xs text-red-500 dark:text-red-400">
          Captured in: {{ errorInfo }}
        </p>
      </details>
    </div>

    <button
      @click="reset"
      class="inline-flex items-center gap-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
    >
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.992 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
      </svg>
      Try Again
    </button>
  </div>
</template>
