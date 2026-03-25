<script setup>
defineProps({
  crumbs: {
    type: Array,
    required: true,
    // Each item: { label: string, to?: string }
  },
})
</script>

<template>
  <nav v-if="crumbs.length" aria-label="Breadcrumb" class="px-4 md:px-6 pt-3">
    <ol class="flex items-center gap-1 text-xs text-[var(--color-text-muted)] list-none m-0 p-0">
      <li v-for="(crumb, i) in crumbs" :key="i" class="flex items-center gap-1">
        <span v-if="i > 0" class="select-none">/</span>
        <router-link
          v-if="crumb.to && i < crumbs.length - 1"
          :to="crumb.to"
          class="text-[var(--color-text-muted)] hover:text-[var(--color-primary)] no-underline transition-colors"
        >{{ crumb.label }}</router-link>
        <span
          v-else
          :class="i === crumbs.length - 1 ? 'text-[var(--color-text)]' : ''"
        >{{ crumb.label }}</span>
      </li>
    </ol>
  </nav>
</template>
