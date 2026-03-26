<script setup>
import OrgInfoFlow from '../components/visualization/OrgInfoFlow.vue'
</script>

<template>
  <div class="org-chart-view">
    <OrgInfoFlow />
  </div>
</template>

<style scoped>
.org-chart-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px;
  height: calc(100vh - 120px);
}
</style>
