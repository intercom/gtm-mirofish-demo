<script setup>
import { computed } from 'vue'

const props = defineProps({
  persona: { type: Object, required: true },
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'edit'])

const initials = computed(() => {
  const parts = (props.persona.name || '').split(' ')
  return parts.map((p) => p[0]).join('').toUpperCase().slice(0, 2)
})

const authorityBadge = computed(() => {
  const map = {
    final_approver: { label: 'Approver', cls: 'bg-[var(--color-fin-orange-tint)] text-[var(--color-fin-orange)]' },
    technical_veto: { label: 'Tech Veto', cls: 'bg-[var(--color-accent-tint)] text-[var(--color-accent)]' },
    influencer: { label: 'Influencer', cls: 'bg-[var(--color-primary-tint)] text-[var(--color-primary)]' },
  }
  return map[props.persona.decision_authority] || { label: props.persona.decision_authority, cls: 'bg-gray-100 text-gray-600' }
})

const sourceBadge = computed(() => {
  const map = {
    zep_graph: { label: 'Graph', cls: 'bg-[var(--color-success-light)] text-[var(--color-success)]' },
    template: { label: 'Template', cls: 'bg-[var(--color-warning-light)] text-[var(--color-warning)]' },
    custom: { label: 'Custom', cls: 'bg-[var(--color-primary-tint)] text-[var(--color-primary)]' },
  }
  return map[props.persona.source] || { label: props.persona.source, cls: 'bg-gray-100 text-gray-600' }
})
</script>

<template>
  <div
    class="group rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 transition-shadow hover:shadow-md cursor-pointer"
    :class="{ 'p-3': compact }"
    @click="emit('select', persona)"
  >
    <!-- Header -->
    <div class="flex items-start gap-3 mb-3">
      <div
        class="flex-shrink-0 w-10 h-10 rounded-full bg-[var(--color-primary)] text-white flex items-center justify-center text-sm font-semibold"
      >
        {{ initials }}
      </div>
      <div class="flex-1 min-w-0">
        <h3 class="font-semibold text-sm text-[var(--color-text)] truncate">{{ persona.name }}</h3>
        <p class="text-xs text-[var(--color-text-secondary)] truncate">{{ persona.title }}</p>
        <p v-if="!compact" class="text-xs text-[var(--color-text-muted)]">{{ persona.department }}</p>
      </div>
      <button
        class="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-[var(--color-primary-light)]"
        title="Edit persona"
        @click.stop="emit('edit', persona)"
      >
        <svg class="w-3.5 h-3.5 text-[var(--color-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
        </svg>
      </button>
    </div>

    <!-- Badges -->
    <div class="flex flex-wrap gap-1.5 mb-3">
      <span :class="authorityBadge.cls" class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium">
        {{ authorityBadge.label }}
      </span>
      <span :class="sourceBadge.cls" class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium">
        {{ sourceBadge.label }}
      </span>
      <span v-if="persona.mbti" class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-600">
        {{ persona.mbti }}
      </span>
    </div>

    <!-- Traits (compact mode stops here) -->
    <template v-if="!compact">
      <!-- Personality Traits -->
      <div v-if="persona.personality_traits?.length" class="mb-2.5">
        <p class="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1">Traits</p>
        <div class="flex flex-wrap gap-1">
          <span
            v-for="trait in persona.personality_traits"
            :key="trait"
            class="px-1.5 py-0.5 rounded text-[10px] bg-[var(--color-bg-alt)] text-[var(--color-text-secondary)]"
          >
            {{ trait }}
          </span>
        </div>
      </div>

      <!-- Goals -->
      <div v-if="persona.goals?.length" class="mb-2.5">
        <p class="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1">Goals</p>
        <ul class="space-y-0.5">
          <li v-for="goal in persona.goals.slice(0, 3)" :key="goal" class="text-xs text-[var(--color-text-secondary)] flex items-start gap-1.5">
            <span class="text-[var(--color-primary)] mt-0.5 text-[10px]">&#x25B8;</span>
            <span>{{ goal }}</span>
          </li>
        </ul>
      </div>

      <!-- Known Facts -->
      <div v-if="persona.known_facts?.length">
        <p class="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1">Known Facts</p>
        <ul class="space-y-0.5">
          <li v-for="fact in persona.known_facts.slice(0, 3)" :key="fact" class="text-xs text-[var(--color-text-secondary)] flex items-start gap-1.5">
            <span class="text-[var(--color-success)] mt-0.5 text-[10px]">&#x25CF;</span>
            <span>{{ fact }}</span>
          </li>
        </ul>
      </div>

      <!-- Firmographic footer -->
      <div v-if="persona.firmographic?.industry" class="mt-3 pt-2.5 border-t border-[var(--color-border)] flex items-center gap-2 text-[10px] text-[var(--color-text-muted)]">
        <span>{{ persona.firmographic.industry }}</span>
        <span v-if="persona.firmographic.company_size">·</span>
        <span v-if="persona.firmographic.company_size">{{ persona.firmographic.company_size }} emp</span>
        <span v-if="persona.firmographic.region">·</span>
        <span v-if="persona.firmographic.region">{{ persona.firmographic.region }}</span>
      </div>
    </template>
  </div>
</template>
