<script setup>
import ReportWizard from '../components/report/ReportWizard.vue'
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <div class="mb-6">
      <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]" style="letter-spacing: -0.64px">
        Generate Report
      </h1>
      <p class="text-sm text-[var(--color-text-muted)] mt-1">
        Create a predictive analysis report from your simulation data.
      </p>
    </div>
    <ReportWizard />
  </div>
</template>
