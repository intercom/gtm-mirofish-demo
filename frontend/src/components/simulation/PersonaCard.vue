<script setup>
defineProps({
  name: { type: String, required: true },
  removable: { type: Boolean, default: false },
})

defineEmits(['remove'])
</script>

<template>
  <div
    class="persona-card flex items-center gap-2 px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] cursor-grab select-none transition-all duration-150 hover:shadow-[var(--shadow)] hover:border-[var(--color-primary)]"
  >
    <div
      class="w-7 h-7 rounded-full bg-[var(--color-primary-light)] text-[var(--color-primary)] flex items-center justify-center text-xs font-semibold shrink-0"
    >
      {{ name.charAt(0).toUpperCase() }}
    </div>
    <span class="text-sm text-[var(--color-text)] truncate flex-1">{{ name }}</span>
    <button
      v-if="removable"
      @click.stop="$emit('remove')"
      class="w-5 h-5 flex items-center justify-center rounded-full text-[var(--color-text-muted)] hover:text-[var(--color-error)] hover:bg-[var(--color-error-light)] transition-colors shrink-0"
      title="Remove from team"
    >
      <svg class="w-3 h-3" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M2 2l8 8M10 2l-8 8" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.persona-card.dragging {
  opacity: 0.4;
  border-style: dashed;
}
</style>
