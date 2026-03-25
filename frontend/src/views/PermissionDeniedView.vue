<script setup>
import { useAuthStore } from '../stores/auth'
import RoleBadge from '../components/common/RoleBadge.vue'

const auth = useAuthStore()
</script>

<template>
  <div class="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
    <div class="w-16 h-16 rounded-full bg-[var(--color-fin-orange-tint)] flex items-center justify-center mb-4">
      <svg class="w-8 h-8 text-[var(--color-fin-orange)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    </div>
    <h1 class="text-xl font-semibold text-[var(--color-text)] mb-2">Access Restricted</h1>
    <p class="text-sm text-[var(--color-text-muted)] mb-4 max-w-sm">
      You don't have permission to view this page. Contact an administrator to request access.
    </p>
    <div class="flex items-center gap-2 text-xs text-[var(--color-text-muted)] mb-6">
      <span>Your role:</span>
      <RoleBadge :role="auth.userRole" size="xs" />
    </div>
    <router-link
      to="/"
      class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors no-underline"
    >
      Go to Home
    </router-link>
  </div>
</template>
