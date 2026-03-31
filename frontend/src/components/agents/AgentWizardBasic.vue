<script setup>
import { computed, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['update:modelValue', 'valid'])

const DEPARTMENTS = [
  'Sales',
  'Marketing',
  'CS',
  'Product',
  'Finance',
  'Engineering',
  'Executive',
]

const ROLE_SUGGESTIONS = [
  'Account Executive',
  'SDR',
  'Customer Success Manager',
  'Product Marketing Manager',
  'VP of Sales',
  'CX Director',
  'Solutions Engineer',
  'Revenue Operations Manager',
]

const AVATAR_COLORS = [
  '#2068FF',
  '#ff5600',
  '#AA00FF',
  '#059669',
  '#D97706',
  '#DC2626',
  '#7C3AED',
  '#0891B2',
]

const TEMPLATES = [
  {
    id: 'sdr',
    label: 'Sales Dev Rep',
    name: 'Alex Chen',
    role: 'Sales Development Representative',
    department: 'Sales',
    backstory: 'Energetic early-career rep who thrives on outbound prospecting. Relies heavily on data signals and sequences to book meetings, always looking for the next competitive edge.',
    avatarColor: '#2068FF',
  },
  {
    id: 'ae',
    label: 'Account Executive',
    name: 'Jordan Rivera',
    role: 'Account Executive',
    department: 'Sales',
    backstory: 'Mid-market closer with deep consultative selling experience. Builds champion networks inside target accounts and navigates complex procurement cycles with patience.',
    avatarColor: '#059669',
  },
  {
    id: 'csm',
    label: 'CS Manager',
    name: 'Taylor Morgan',
    role: 'Customer Success Manager',
    department: 'CS',
    backstory: 'Relationship-driven CSM who focuses on expansion revenue and health scores. Passionate about turning detractors into advocates through proactive engagement.',
    avatarColor: '#ff5600',
  },
  {
    id: 'pmm',
    label: 'Product Marketer',
    name: 'Sam Patel',
    role: 'Product Marketing Manager',
    department: 'Marketing',
    backstory: 'Strategic product marketer skilled at competitive positioning and launch campaigns. Bridges the gap between product roadmap and revenue team enablement.',
    avatarColor: '#AA00FF',
  },
  {
    id: 'vp-sales',
    label: 'VP of Sales',
    name: 'Morgan Hayes',
    role: 'VP of Sales',
    department: 'Executive',
    backstory: 'Seasoned sales leader focused on pipeline discipline and forecast accuracy. Built teams from 5 to 50 reps and knows when to invest in tooling vs. training.',
    avatarColor: '#DC2626',
  },
  {
    id: 'cx-director',
    label: 'CX Director',
    name: 'Casey Kim',
    role: 'Director of Customer Experience',
    department: 'CS',
    backstory: 'Holistic CX leader who unifies support, success, and community under one strategy. Advocates for AI-first resolution while preserving the human touch for high-value interactions.',
    avatarColor: '#0891B2',
  },
]

function update(field, value) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

function applyTemplate(template) {
  emit('update:modelValue', {
    ...props.modelValue,
    name: template.name,
    role: template.role,
    department: template.department,
    backstory: template.backstory,
    avatarColor: template.avatarColor,
  })
}

const initials = computed(() => {
  const name = props.modelValue.name?.trim()
  if (!name) return '?'
  const parts = name.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return name[0].toUpperCase()
})

const isValid = computed(() => {
  const v = props.modelValue
  return !!(v.name?.trim() && v.role?.trim())
})

watch(isValid, (val) => emit('valid', val), { immediate: true })

const backstoryLength = computed(() => props.modelValue.backstory?.length || 0)

const showRoleSuggestions = computed(() => {
  const role = props.modelValue.role?.trim().toLowerCase() || ''
  if (!role || role.length < 2) return []
  return ROLE_SUGGESTIONS.filter(
    (s) => s.toLowerCase().includes(role) && s.toLowerCase() !== role,
  )
})
</script>

<template>
  <div class="space-y-6">
    <!-- Template Selector -->
    <div>
      <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-3">
        Start from a template
      </label>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
        <button
          v-for="t in TEMPLATES"
          :key="t.id"
          @click="applyTemplate(t)"
          class="text-left p-3 rounded-lg border transition-all group cursor-pointer"
          :class="
            modelValue.name === t.name && modelValue.role === t.role
              ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
              : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)] hover:shadow-sm'
          "
        >
          <!-- Mini avatar -->
          <div
            class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-semibold mb-2"
            :style="{ backgroundColor: t.avatarColor }"
          >
            {{ t.name.split(' ').map((p) => p[0]).join('') }}
          </div>
          <span class="block text-sm font-semibold text-[var(--color-text)] leading-tight">{{ t.label }}</span>
          <span class="block text-[11px] text-[var(--color-text-muted)] mt-0.5 leading-snug">{{ t.department }}</span>
        </button>
      </div>
    </div>

    <hr class="border-[var(--color-border)]" />

    <!-- Avatar Preview + Color Picker -->
    <div class="flex items-start gap-5">
      <div class="shrink-0">
        <div
          class="w-16 h-16 rounded-full flex items-center justify-center text-white text-xl font-bold transition-colors"
          :style="{ backgroundColor: modelValue.avatarColor || AVATAR_COLORS[0] }"
        >
          {{ initials }}
        </div>
      </div>
      <div class="flex-1 min-w-0">
        <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
          Avatar Color
        </label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="color in AVATAR_COLORS"
            :key="color"
            @click="update('avatarColor', color)"
            class="w-7 h-7 rounded-full transition-all cursor-pointer"
            :class="modelValue.avatarColor === color ? 'ring-2 ring-offset-2 ring-[var(--color-primary)] scale-110' : 'hover:scale-110'"
            :style="{ backgroundColor: color }"
            :aria-label="`Select color ${color}`"
          />
        </div>
      </div>
    </div>

    <!-- Name -->
    <div>
      <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">
        Name <span class="text-red-500">*</span>
      </label>
      <input
        type="text"
        :value="modelValue.name"
        @input="update('name', $event.target.value)"
        placeholder="e.g. Alex Chen"
        class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-colors"
      />
    </div>

    <!-- Role / Title -->
    <div class="relative">
      <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">
        Role / Title <span class="text-red-500">*</span>
      </label>
      <input
        type="text"
        :value="modelValue.role"
        @input="update('role', $event.target.value)"
        placeholder="e.g. Account Executive"
        class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-colors"
      />
      <!-- Role suggestions dropdown -->
      <div
        v-if="showRoleSuggestions.length"
        class="absolute z-10 left-0 right-0 mt-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg shadow-lg overflow-hidden"
      >
        <button
          v-for="suggestion in showRoleSuggestions"
          :key="suggestion"
          @click="update('role', suggestion)"
          class="w-full text-left px-3 py-2 text-sm text-[var(--color-text)] hover:bg-[var(--color-primary-light)] transition-colors cursor-pointer"
        >
          {{ suggestion }}
        </button>
      </div>
    </div>

    <!-- Department -->
    <div>
      <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Department</label>
      <select
        :value="modelValue.department"
        @change="update('department', $event.target.value)"
        class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-colors"
      >
        <option value="" disabled>Select department</option>
        <option v-for="dept in DEPARTMENTS" :key="dept" :value="dept">{{ dept }}</option>
      </select>
    </div>

    <!-- Backstory -->
    <div>
      <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">
        Backstory
        <span class="font-normal text-[var(--color-text-muted)]">(optional)</span>
      </label>
      <textarea
        :value="modelValue.backstory"
        @input="update('backstory', $event.target.value)"
        placeholder="A brief background for this agent — what drives them, their experience, perspective..."
        rows="3"
        maxlength="500"
        class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-colors resize-y"
      />
      <p class="text-[11px] text-[var(--color-text-muted)] mt-1 text-right">
        {{ backstoryLength }} / 500
      </p>
    </div>
  </div>
</template>
