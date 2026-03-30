<script setup>
import AppBadge from './AppBadge.vue'
</script>

<template>
  <AppBadge v-bind="$attrs">
    <slot />
  </AppBadge>
</template>
