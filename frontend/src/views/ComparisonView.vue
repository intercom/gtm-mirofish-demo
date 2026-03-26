<script setup>
import SimulationComparison from '../components/simulation/SimulationComparison.vue'
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <div class="flex items-center justify-between mb-6 md:mb-8">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">Compare Simulations</h1>
        <p class="text-sm text-[var(--color-text-muted)] mt-1">Side-by-side comparison of simulation runs</p>
      </div>
      <router-link
        to="/simulations"
        class="text-sm font-medium text-[var(--color-text-muted)] hover:text-[#2068FF] transition-colors no-underline"
      >
        &larr; All Simulations
      </router-link>
    </div>
    <SimulationComparison />
  </div>
</template>
