<script setup>
const props = defineProps({
  step: { type: Object, required: true },
  isActive: { type: Boolean, default: false },
})
</script>

<template>
  <div
    class="rounded-xl border transition-all duration-300"
    :class="isActive
      ? 'border-[var(--color-primary)] bg-[var(--color-surface)] shadow-lg'
      : 'border-[var(--color-border)] bg-[var(--color-surface)] opacity-60'"
  >
    <!-- Step header -->
    <div class="px-5 py-4 border-b border-[var(--color-border)]">
      <div class="flex items-center gap-3">
        <span
          class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
          :class="isActive
            ? 'bg-[#2068FF] text-white'
            : 'bg-[var(--color-tint)] text-[var(--color-text-muted)]'"
        >
          {{ step.step }}
        </span>
        <h3 class="text-base font-semibold text-[var(--color-text)]">{{ step.title }}</h3>
      </div>
    </div>

    <!-- Step body -->
    <div class="px-5 py-4 space-y-4">
      <p class="text-sm text-[var(--color-text-secondary)] leading-relaxed">{{ step.description }}</p>

      <!-- Detail text (overview step) -->
      <p v-if="step.detail" class="text-sm text-[var(--color-text)] leading-relaxed">
        {{ step.detail }}
      </p>

      <!-- Seed document preview -->
      <div v-if="step.key === 'seed_document'" class="space-y-3">
        <div class="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
          <span class="px-2 py-0.5 rounded bg-[var(--color-tint)]">{{ step.word_count }} words</span>
        </div>
        <div class="bg-[var(--color-tint)] rounded-lg p-3 max-h-48 overflow-y-auto">
          <pre class="text-xs text-[var(--color-text-secondary)] whitespace-pre-wrap font-[inherit] leading-relaxed">{{ step.seed_text }}</pre>
        </div>
      </div>

      <!-- Agent population -->
      <div v-if="step.key === 'agent_population'" class="space-y-4">
        <div class="text-center py-2">
          <span class="text-3xl font-bold text-[#2068FF]">{{ step.agent_count }}</span>
          <span class="text-sm text-[var(--color-text-muted)] ml-1.5">agents</span>
        </div>

        <div v-if="step.personas?.length">
          <span class="text-xs uppercase tracking-wider text-[var(--color-text-muted)] block mb-2">Persona types</span>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="persona in step.personas"
              :key="persona"
              class="px-2.5 py-1 text-xs rounded-full bg-[rgba(32,104,255,0.1)] text-[#2068FF] font-medium"
            >
              {{ persona }}
            </span>
          </div>
        </div>

        <div v-if="step.industries?.length">
          <span class="text-xs uppercase tracking-wider text-[var(--color-text-muted)] block mb-2">Industries</span>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="industry in step.industries"
              :key="industry"
              class="px-2.5 py-1 text-xs rounded-full bg-[rgba(255,86,0,0.1)] text-[#ff5600] font-medium"
            >
              {{ industry }}
            </span>
          </div>
        </div>

        <div v-if="step.company_sizes?.length || step.regions?.length" class="grid grid-cols-2 gap-3">
          <div v-if="step.company_sizes?.length">
            <span class="text-xs uppercase tracking-wider text-[var(--color-text-muted)] block mb-2">Company sizes</span>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="size in step.company_sizes"
                :key="size"
                class="px-2 py-0.5 text-xs rounded bg-[var(--color-tint)] text-[var(--color-text-secondary)]"
              >
                {{ size }}
              </span>
            </div>
          </div>
          <div v-if="step.regions?.length">
            <span class="text-xs uppercase tracking-wider text-[var(--color-text-muted)] block mb-2">Regions</span>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="region in step.regions"
                :key="region"
                class="px-2 py-0.5 text-xs rounded bg-[var(--color-tint)] text-[var(--color-text-secondary)]"
              >
                {{ region }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Simulation config -->
      <div v-if="step.key === 'simulation_config'" class="grid grid-cols-3 gap-3">
        <div class="text-center p-3 rounded-lg bg-[var(--color-tint)]">
          <div class="text-xl font-bold text-[#2068FF]">{{ step.duration_hours }}h</div>
          <div class="text-[10px] text-[var(--color-text-muted)] mt-0.5">Duration</div>
        </div>
        <div class="text-center p-3 rounded-lg bg-[var(--color-tint)]">
          <div class="text-xl font-bold text-[#ff5600]">{{ step.total_rounds }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)] mt-0.5">Rounds</div>
        </div>
        <div class="text-center p-3 rounded-lg bg-[var(--color-tint)]">
          <div class="text-xl font-bold text-[#AA00FF]">{{ step.minutes_per_round }}m</div>
          <div class="text-[10px] text-[var(--color-text-muted)] mt-0.5">Per round</div>
        </div>
      </div>

      <!-- Expected outcomes -->
      <div v-if="step.key === 'expected_outcomes' && step.outcomes?.length">
        <ul class="space-y-2">
          <li
            v-for="(outcome, i) in step.outcomes"
            :key="i"
            class="flex items-start gap-2.5 text-sm text-[var(--color-text)]"
          >
            <svg class="w-4 h-4 text-[#009900] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            {{ outcome }}
          </li>
        </ul>
      </div>

      <!-- Tip -->
      <div v-if="step.tip" class="flex gap-2.5 p-3 rounded-lg bg-[rgba(32,104,255,0.05)] border border-[#2068FF]/10">
        <svg class="w-4 h-4 text-[#2068FF] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
        </svg>
        <p class="text-xs text-[#2068FF]/80 leading-relaxed">{{ step.tip }}</p>
      </div>
    </div>
  </div>
</template>
