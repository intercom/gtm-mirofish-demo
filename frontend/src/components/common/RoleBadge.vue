<script setup>
import { computed } from 'vue'

const props = defineProps({
  role: {
    type: String,
    required: true,
    validator: (v) => ['admin', 'editor', 'viewer', 'guest'].includes(v),
  },
  size: {
    type: String,
    default: 'sm',
    validator: (v) => ['xs', 'sm'].includes(v),
  },
})

const roleConfig = {
  admin: { label: 'Admin', classes: 'bg-[var(--color-primary)] text-white' },
  editor: { label: 'Editor', classes: 'bg-[var(--color-success-light)] text-[var(--color-success)]' },
  viewer: { label: 'Viewer', classes: 'bg-black/5 text-[var(--color-text-secondary)] dark:bg-white/10' },
  guest: { label: 'Guest', classes: 'bg-[var(--color-fin-orange-tint)] text-[var(--color-fin-orange)]' },
}

const config = computed(() => roleConfig[props.role])

const sizeClasses = computed(() =>
  props.size === 'xs' ? 'px-1.5 py-px text-[10px]' : 'px-2 py-0.5 text-xs'
)
</script>

<template>
  <span
    :class="[
      'inline-flex items-center rounded-full font-semibold leading-tight',
      sizeClasses,
      config.classes,
    ]"
  >{{ config.label }}</span>
</template>
