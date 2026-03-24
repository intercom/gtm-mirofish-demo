<script setup>
defineProps({
  taskId: { type: String, required: true },
  activePhase: { type: String, required: true },
})

const phases = [
  { key: 'graph', label: 'Graph', route: (id) => `/workspace/${id}?tab=graph` },
  { key: 'simulation', label: 'Simulation', route: (id) => `/workspace/${id}?tab=simulation` },
  { key: 'report', label: 'Report', route: (id) => `/report/${id}` },
]
</script>

<template>
  <nav class="phase-nav border-b border-[var(--color-border)] mb-6">
    <div class="flex items-center gap-6">
      <router-link
        v-for="phase in phases"
        :key="phase.key"
        :to="phase.route(taskId)"
        class="phase-tab flex items-center gap-2 py-3 text-sm font-medium border-b-2 transition-all duration-300 no-underline"
        :class="activePhase === phase.key
          ? 'border-[var(--color-primary)] text-[var(--color-primary)] dark:text-white'
          : 'border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] dark:text-[var(--color-text-on-dark-muted)] dark:hover:text-[var(--color-text-on-dark-secondary)]'"
      >
        <!-- Graph icon -->
        <svg v-if="phase.key === 'graph'" class="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="4" cy="4" r="2" />
          <circle cx="12" cy="4" r="2" />
          <circle cx="8" cy="13" r="2" />
          <line x1="5.5" y1="5.5" x2="7" y2="11" />
          <line x1="10.5" y1="5.5" x2="9" y2="11" />
          <line x1="6" y1="4" x2="10" y2="4" />
        </svg>
        <!-- Simulation icon -->
        <svg v-else-if="phase.key === 'simulation'" class="w-4 h-4" viewBox="0 0 16 16" fill="currentColor">
          <path d="M4 2.5v11l9-5.5z" />
        </svg>
        <!-- Report icon -->
        <svg v-else-if="phase.key === 'report'" class="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="1.5" width="10" height="13" rx="1" />
          <line x1="5.5" y1="5" x2="10.5" y2="5" />
          <line x1="5.5" y1="7.5" x2="10.5" y2="7.5" />
          <line x1="5.5" y1="10" x2="8.5" y2="10" />
        </svg>
        <span>{{ phase.label }}</span>
      </router-link>
    </div>
  </nav>
</template>
