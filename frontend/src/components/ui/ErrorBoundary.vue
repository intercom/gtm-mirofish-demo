<script setup>
import { ref, onErrorCaptured, watch } from 'vue'
import { useRoute } from 'vue-router'
import ErrorState from './ErrorState.vue'

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

function retry() {
  error.value = null
  errorInfo.value = null
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
