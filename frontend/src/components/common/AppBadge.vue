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
        'bg-[rgba(32,104,255,0.1)] text-[--color-primary]': variant === 'primary',
        'bg-green-100 text-green-700': variant === 'success',
        'bg-[rgba(255,86,0,0.1)] text-[--color-fin-orange]': variant === 'warning',
        'bg-red-100 text-red-700': variant === 'error',
        'bg-black/5 text-[--color-text-secondary]': variant === 'neutral',
      },
    ]"
  >
    <slot />
  </span>
</template>
