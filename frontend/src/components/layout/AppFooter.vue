<script setup>
const year = new Date().getFullYear()
</script>

<template>
  <footer class="border-t border-black/10 px-6 py-4 text-center text-xs text-[var(--color-text-muted)]">
    <span>Powered by </span>
    <a
      href="https://github.com/666ghj/MiroFish"
      target="_blank"
      rel="noopener noreferrer"
      class="text-[var(--color-primary)] hover:underline"
    >MiroFish</a>
    <span> — Swarm Intelligence Engine</span>
    <span class="mx-2">|</span>
    <span>Intercom GTM Systems</span>
    <span class="mx-2">|</span>
    <span>&copy; {{ year }}</span>
  </footer>
</template>
