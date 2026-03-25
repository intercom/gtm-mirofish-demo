<script setup>
import { ref, onErrorCaptured } from 'vue'
import ErrorState from './ErrorState.vue'

defineProps({
  title: { type: String, default: 'Something went wrong' },
  message: { type: String, default: 'An unexpected error occurred. Please try again.' },
})

const error = ref(null)

onErrorCaptured((err) => {
  error.value = err
  console.error('[ErrorBoundary]', err)
  return false
})

function retry() {
  error.value = null
}
</script>

<template>
  <slot v-if="!error" />
  <ErrorState
    v-else
    :title="title"
    :message="message"
    @retry="retry"
  />
</template>
