<script setup>
defineProps({
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'primary', 'success', 'warning', 'error', 'info', 'orange'].includes(v),
  },
})
</script>

<template>
  <span
    class="inline-flex items-center rounded-full font-medium"
    style="padding: var(--badge-padding-y) var(--badge-padding-x); font-size: var(--badge-font-size)"
    :class="{
      'bg-black/5 text-[var(--color-text-secondary)]': variant === 'default',
      'bg-[var(--badge-primary-bg)] text-[var(--badge-primary-text)]': variant === 'primary',
      'bg-[var(--badge-success-bg-soft)] text-[var(--badge-success-text-soft)]': variant === 'success',
      'bg-[var(--badge-warning-bg-soft)] text-[var(--badge-warning-text-soft)]': variant === 'warning',
      'bg-[var(--badge-error-bg-soft)] text-[var(--badge-error-text-soft)]': variant === 'error',
      'bg-[var(--badge-secondary-bg)] text-[var(--badge-secondary-text)]': variant === 'info',
      'bg-[var(--badge-orange-bg-soft)] text-[var(--badge-orange-text-soft)]': variant === 'orange',
    }"
  >
    <slot />
  </span>
</template>
