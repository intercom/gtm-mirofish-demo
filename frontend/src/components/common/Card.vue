<script setup>
defineProps({
  padding: {
    type: Boolean,
    default: true,
  },
})
</script>

<template>
  <div
    class="bg-white border border-black/10 rounded-lg"
    :class="{ 'p-6': padding }"
  >
    <slot />
  </div>
</template>
