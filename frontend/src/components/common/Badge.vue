<script setup>
defineProps({
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'success', 'warning', 'error', 'info'].includes(v),
  },
})
</script>

<template>
  <span
    class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium"
    :class="{
      'bg-[var(--color-tint)] text-[var(--color-text-secondary)]': variant === 'default',
      'bg-green-100 text-green-700': variant === 'success',
      'bg-yellow-100 text-yellow-700': variant === 'warning',
      'bg-red-100 text-red-700': variant === 'error',
      'bg-blue-100 text-blue-700': variant === 'info',
    }"
  >
    <slot />
  </span>
</template>
