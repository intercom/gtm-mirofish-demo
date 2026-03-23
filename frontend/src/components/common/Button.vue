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
  type: {
    type: String,
    default: 'button',
  },
})

defineEmits(['click'])
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
    class="inline-flex items-center justify-center font-semibold transition-colors rounded-lg cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
    :class="[
      {
        'bg-[#2068FF] hover:bg-[#1a5ae0] text-white': variant === 'primary',
        'bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text)] hover:bg-black/5': variant === 'secondary',
        'text-[var(--color-text-secondary)] hover:bg-black/5': variant === 'ghost',
      },
      {
        'px-3 py-1.5 text-xs gap-1.5': size === 'sm',
        'px-4 py-2 text-sm gap-2': size === 'md',
        'px-6 py-3 text-base gap-2': size === 'lg',
      },
    ]"
  >
    <svg
      v-if="loading"
      class="animate-spin"
      :class="size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <slot />
  </button>
</template>
