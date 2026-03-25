<script setup>
import SkeletonBlock from './SkeletonBlock.vue'
</script>

<template>
  <div>
    <!-- Back link -->
    <SkeletonBlock height="14px" width="120px" class="mb-4" />

    <!-- Title + description -->
    <SkeletonBlock height="28px" width="260px" class="mb-2" />
    <SkeletonBlock height="14px" width="380px" class="mb-8" />

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left column: textarea + persona pills -->
      <div class="lg:col-span-2 space-y-6">
        <div>
          <SkeletonBlock height="10px" width="100px" class="mb-2" />
          <SkeletonBlock height="280px" width="100%" rounded="lg" />
        </div>
        <div>
          <SkeletonBlock height="10px" width="110px" class="mb-3" />
          <div class="flex flex-wrap gap-2">
            <SkeletonBlock v-for="i in 6" :key="i" height="28px" :width="`${60 + (i * 15) % 40}px`" rounded="full" />
          </div>
        </div>
        <div>
          <SkeletonBlock height="10px" width="90px" class="mb-3" />
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
            <SkeletonBlock v-for="i in 3" :key="i" height="36px" rounded="lg" />
          </div>
        </div>
      </div>

      <!-- Right column: config panel -->
      <div class="space-y-6">
        <div>
          <SkeletonBlock height="10px" width="90px" class="mb-2" />
          <SkeletonBlock height="8px" width="100%" rounded="full" />
          <SkeletonBlock height="32px" width="50px" rounded="md" class="mx-auto mt-2" />
        </div>
        <div>
          <SkeletonBlock height="10px" width="70px" class="mb-2" />
          <div class="flex gap-2">
            <SkeletonBlock v-for="i in 3" :key="i" height="36px" rounded="lg" />
          </div>
        </div>
        <div>
          <SkeletonBlock height="10px" width="65px" class="mb-2" />
          <div class="flex gap-2">
            <SkeletonBlock v-for="i in 3" :key="i" height="36px" rounded="lg" />
          </div>
        </div>
        <SkeletonBlock height="44px" width="100%" rounded="lg" class="mt-4" />
      </div>
    </div>
  </div>
</template>
