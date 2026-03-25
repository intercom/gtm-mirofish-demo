<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'ghost'].includes(v),
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
  disabled: Boolean,
  loading: Boolean,
})

defineEmits(['click'])
</script>

<template>
  <button
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
    :class="[
      'inline-flex items-center justify-center font-semibold transition-colors cursor-pointer',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      {
        'text-xs px-3 py-1.5 rounded-md': size === 'sm',
        'text-sm px-5 py-2.5 rounded-lg': size === 'md',
        'text-sm px-8 py-3 rounded-lg': size === 'lg',
      },
      {
        'bg-[--color-primary] hover:bg-[--color-primary-hover] text-white': variant === 'primary',
        'bg-transparent border border-[--color-primary-border] text-[--color-primary] hover:bg-[--color-primary-light]': variant === 'secondary',
        'bg-transparent text-[--color-text-secondary] hover:text-[--color-text] hover:bg-black/5': variant === 'ghost',
      },
    ]"
    @click="$emit('click', $event)"
  >
    <svg
      v-if="loading"
      class="animate-spin -ml-1 mr-2 h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <slot />
  </button>
</template>
