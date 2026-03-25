<script setup>
const year = new Date().getFullYear()
</script>

<template>
  <footer class="border-t border-[var(--color-border)] px-4 md:px-6 py-3 md:py-4 text-center text-xs text-[var(--color-text-muted)]" role="contentinfo">
    <span>Powered by </span>
    <a
      href="https://github.com/666ghj/MiroFish"
      target="_blank"
      rel="noopener noreferrer"
      class="text-[var(--color-primary)] hover:underline"
    >MiroFish</a>
    <span class="hidden sm:inline"> — Swarm Intelligence Engine</span>
    <span class="hidden sm:inline mx-2">|</span>
    <br class="sm:hidden" />
    <span>Intercom GTM Systems</span>
    <span class="mx-2">|</span>
    <span>&copy; {{ year }}</span>
  </footer>
</template>
