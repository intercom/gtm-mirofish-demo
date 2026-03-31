<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const year = new Date().getFullYear()
</script>

<template>
  <footer class="border-t border-[var(--color-border)] px-4 md:px-6 py-3 md:py-4 text-center text-xs text-[var(--color-text-muted)]" role="contentinfo">
    <span>{{ t('footer.poweredBy') }} </span>
    <a
      href="https://github.com/666ghj/MiroFish"
      target="_blank"
      rel="noopener noreferrer"
      class="text-[var(--color-primary)] hover:underline"
    >MiroFish</a>
    <span class="hidden sm:inline"> — {{ t('footer.swarmEngine') }}</span>
    <span class="hidden sm:inline mx-2">|</span>
    <br class="sm:hidden" />
    <span>{{ t('footer.intercomGtm') }}</span>
    <span class="mx-2">|</span>
    <span>&copy; {{ year }}</span>
  </footer>
</template>
