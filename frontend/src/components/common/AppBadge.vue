<script setup>
defineProps({
  variant: {
    type: String,
    default: 'neutral',
    validator: (v) => ['primary', 'success', 'warning', 'error', 'neutral'].includes(v),
  },
})
</script>

<template>
  <span
    :class="[
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold',
      {
        'bg-[var(--badge-secondary-bg)] text-[var(--color-primary)]': variant === 'primary',
        'bg-[var(--badge-success-bg-soft)] text-[var(--badge-success-text-soft)]': variant === 'success',
        'bg-[var(--badge-warning-bg-soft)] text-[var(--badge-warning-text-soft)]': variant === 'warning',
        'bg-[var(--badge-error-bg-soft)] text-[var(--badge-error-text-soft)]': variant === 'error',
        'bg-black/5 text-[var(--color-text-secondary)]': variant === 'neutral',
      },
    ]"
  >
    <slot />
  </span>
</template>
