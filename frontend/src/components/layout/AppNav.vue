<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <nav class="bg-[#050505] border-b border-white/10 px-6 py-3 flex items-center justify-between">
    <div class="flex items-center gap-6">
      <!-- Intercom Logo -->
      <router-link to="/" class="flex items-center gap-2 text-white no-underline">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <rect width="28" height="28" rx="6" fill="#2068FF"/>
          <path d="M7 10.5C7 10.2239 7.22386 10 7.5 10H8.5C8.77614 10 9 10.2239 9 10.5V17.5C9 17.7761 8.77614 18 8.5 18H7.5C7.22386 18 7 17.7761 7 17.5V10.5Z" fill="white"/>
          <path d="M10.5 8.5C10.5 8.22386 10.7239 8 11 8H12C12.2761 8 12.5 8.22386 12.5 8.5V19.5C12.5 19.7761 12.2761 20 12 20H11C10.7239 20 10.5 19.7761 10.5 19.5V8.5Z" fill="white"/>
          <path d="M15.5 8.5C15.5 8.22386 15.7239 8 16 8H17C17.2761 8 17.5 8.22386 17.5 8.5V19.5C17.5 19.7761 17.2761 20 17 20H16C15.7239 20 15.5 19.7761 15.5 19.5V8.5Z" fill="white"/>
          <path d="M19 10.5C19 10.2239 19.2239 10 19.5 10H20.5C20.7761 10 21 10.2239 21 10.5V17.5C21 17.7761 20.7761 18 20.5 18H19.5C19.2239 18 19 17.7761 19 17.5V10.5Z" fill="white"/>
          <path d="M8 20.5C9.5 22 11.5 23 14 23C16.5 23 18.5 22 20 20.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span class="text-sm font-semibold tracking-tight">MiroFish</span>
        <span class="text-xs text-white/40 ml-1">GTM Demo</span>
      </router-link>

      <div class="hidden md:flex items-center gap-4">
        <router-link to="/" class="text-sm text-white/60 hover:text-white transition-colors no-underline">Home</router-link>
        <router-link to="/settings" class="text-sm text-white/60 hover:text-white transition-colors no-underline">Settings</router-link>
      </div>
    </div>

    <div class="flex items-center gap-3">
      <div class="hidden sm:flex items-center gap-2 text-xs text-white/40">
        <span class="w-2 h-2 rounded-full bg-green-500"></span>
        Connected
      </div>
    </div>
  </nav>
</template>
