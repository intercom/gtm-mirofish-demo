<script setup>
import { ref } from 'vue'
import { useLazyLoad } from '../../composables/useLazyLoad'

const props = defineProps({
  src: { type: String, required: true },
  alt: { type: String, default: '' },
  width: { type: [Number, String], default: undefined },
  height: { type: [Number, String], default: undefined },
  placeholderClass: { type: String, default: 'bg-black/5 animate-pulse' },
  rootMargin: { type: String, default: '200px' },
})

const containerRef = ref(null)
const loaded = ref(false)
const { isVisible } = useLazyLoad(containerRef, { rootMargin: props.rootMargin })

function onLoad() {
  loaded.value = true
}
</script>

<template>
  <div
    ref="containerRef"
    class="overflow-hidden"
    :style="{
      width: width ? `${width}px` : undefined,
      height: height ? `${height}px` : undefined,
    }"
  >
    <img
      v-if="isVisible"
      :src="src"
      :alt="alt"
      :width="width"
      :height="height"
      loading="lazy"
      decoding="async"
      class="transition-opacity duration-300"
      :class="loaded ? 'opacity-100' : 'opacity-0'"
      @load="onLoad"
    />
    <div
      v-if="!loaded"
      class="absolute inset-0 rounded"
      :class="placeholderClass"
    />
  </div>
</template>
