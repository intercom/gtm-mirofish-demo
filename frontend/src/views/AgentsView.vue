<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAgentsStore } from '../stores/agents'
import { useToast } from '../composables/useToast'
import ConfirmDialog from '../components/ui/ConfirmDialog.vue'

const { t } = useI18n()
const store = useAgentsStore()
const toast = useToast()

const searchQuery = ref('')
const filterDepartment = ref('all')
const filterSection = ref('all')

const showDeleteDialog = ref(false)
const pendingDeleteAgent = ref(null)

const sectionOptions = computed(() => [
  { value: 'all', label: t('agents.allAgents') },
  { value: 'custom', label: t('agents.myAgents') },
  { value: 'templates', label: t('agents.templates') },
])

onMounted(() => {
  store.fetchAgents()
})

const allAgents = computed(() => {
  const custom = store.agents.map(a => ({ ...a, _section: 'custom' }))
  const templates = store.templates.map(t => ({ ...t, _section: 'templates' }))
  return [...custom, ...templates]
})

const filteredAgents = computed(() => {
  let result = [...allAgents.value]

  if (filterSection.value !== 'all') {
    result = result.filter(a => a._section === filterSection.value)
  }

  if (filterDepartment.value !== 'all') {
    result = result.filter(a => a.department === filterDepartment.value)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter(a =>
      (a.name || '').toLowerCase().includes(q) ||
      (a.role || '').toLowerCase().includes(q) ||
      (a.department || '').toLowerCase().includes(q) ||
      (a.expertise_areas || []).some(e => e.toLowerCase().includes(q)),
    )
  }

  return result
})

const customCount = computed(() => store.agents.length)
const templateCount = computed(() => store.templates.length)

function agentInitial(name) {
  return (name || '?')[0].toUpperCase()
}

function personalitySummary(personality) {
  if (!personality) return 'Balanced'
  const traits = [
    { key: 'analytical', label: 'Analytical' },
    { key: 'creative', label: 'Creative' },
    { key: 'assertive', label: 'Assertive' },
    { key: 'empathetic', label: 'Empathetic' },
    { key: 'risk_tolerant', label: 'Risk-Tolerant' },
  ]
  const top = traits
    .filter(t => (personality[t.key] || 0) >= 70)
    .map(t => t.label)
  return top.length > 0 ? top.join(', ') : 'Balanced'
}

function styleLabel(style) {
  const labels = {
    formal: 'Formal',
    casual: 'Casual',
    data_driven: 'Data-Driven',
    storytelling: 'Storytelling',
    diplomatic: 'Diplomatic',
  }
  return labels[style] || style || 'Default'
}

function cloneAgent(agent) {
  const cloned = store.cloneAgent(agent.id)
  if (cloned) {
    toast.success(`Cloned "${agent.name}" as "${cloned.name}"`)
  }
}

function deleteAgent(agent) {
  pendingDeleteAgent.value = agent
  showDeleteDialog.value = true
}

function confirmDelete() {
  if (pendingDeleteAgent.value) {
    store.removeAgent(pendingDeleteAgent.value.id)
    toast.success(`Deleted "${pendingDeleteAgent.value.name}"`)
    pendingDeleteAgent.value = null
  }
  showDeleteDialog.value = false
}

function addFromTemplate(template) {
  const cloned = store.cloneAgent(template.id)
  if (cloned) {
    toast.success(`Added "${cloned.name}" to your agents`)
  }
}

function relativeTime(dateStr) {
  if (!dateStr) return ''
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) {
    const m = Math.floor(diff / 60)
    return `${m} min${m === 1 ? '' : 's'} ago`
  }
  if (diff < 86400) {
    const h = Math.floor(diff / 3600)
    return `${h} hour${h === 1 ? '' : 's'} ago`
  }
  const d = Math.floor(diff / 86400)
  return `${d} day${d === 1 ? '' : 's'} ago`
}
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-2">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">{{ t('agents.title') }}</h1>
        <p class="text-sm text-[var(--color-text-muted)] mt-1">{{ t('agents.subtitle') }}</p>
      </div>
      <button
        class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        @click="addFromTemplate(store.templates[0])"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        {{ t('agents.createNew') }}
      </button>
    </div>

    <!-- Summary Stats -->
    <div class="grid grid-cols-3 gap-3 mb-6 mt-6">
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="text-xs text-[var(--color-text-muted)]">{{ t('agents.myAgents') }}</div>
        <div class="text-lg font-semibold text-[var(--color-text)]">{{ customCount }}</div>
      </div>
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="text-xs text-[var(--color-text-muted)]">{{ t('agents.templates') }}</div>
        <div class="text-lg font-semibold text-[var(--color-text)]">{{ templateCount }}</div>
      </div>
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="text-xs text-[var(--color-text-muted)]">{{ t('agents.departments') }}</div>
        <div class="text-lg font-semibold text-[var(--color-text)]">{{ store.allDepartments.length }}</div>
      </div>
    </div>

    <!-- Search / Filter Bar -->
    <div class="flex flex-col sm:flex-row gap-3 mb-6">
      <div class="flex-1 relative">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="t('agents.searchPlaceholder')"
          class="w-full pl-9 pr-3 py-2 text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
        />
      </div>
      <div class="flex gap-2">
        <select
          v-model="filterSection"
          class="text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
        >
          <option v-for="opt in sectionOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <select
          v-model="filterDepartment"
          class="text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
        >
          <option value="all">{{ t('agents.allDepartments') }}</option>
          <option v-for="dept in store.allDepartments" :key="dept" :value="dept">
            {{ dept }}
          </option>
        </select>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="filteredAgents.length === 0 && !searchQuery && filterDepartment === 'all' && filterSection === 'custom'" class="text-center py-16 md:py-24">
      <div class="w-16 h-16 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mx-auto mb-5">
        <svg class="w-7 h-7 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
        </svg>
      </div>
      <h2 class="text-base font-semibold text-[var(--color-text)] mb-2">{{ t('agents.noCustomAgents') }}</h2>
      <p class="text-sm text-[var(--color-text-secondary)] mb-6 max-w-sm mx-auto">
        {{ t('agents.noCustomAgentsHint') }}
      </p>
      <button
        class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
        @click="filterSection = 'templates'"
      >
        {{ t('agents.browseTemplates') }}
      </button>
    </div>

    <!-- No filter results -->
    <div v-else-if="filteredAgents.length === 0" class="text-center py-12">
      <p class="text-sm text-[var(--color-text-muted)]">{{ t('agents.noMatchingAgents') }}</p>
      <button
        @click="searchQuery = ''; filterDepartment = 'all'; filterSection = 'all'"
        class="text-sm text-[#2068FF] hover:underline mt-2"
      >
        {{ t('common.clearFilters') }}
      </button>
    </div>

    <!-- Agent cards grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="agent in filteredAgents"
        :key="agent.id"
        class="border border-[var(--color-border)] bg-[var(--color-surface)] rounded-lg p-5 transition-shadow hover:shadow-[var(--shadow-md)]"
      >
        <!-- Card header -->
        <div class="flex items-start gap-3 mb-3">
          <div
            class="w-11 h-11 rounded-full flex items-center justify-center text-white text-base font-semibold shrink-0"
            :style="{ backgroundColor: agent.avatar_color || '#2068FF' }"
          >
            {{ agentInitial(agent.name) }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-0.5">
              <h3 class="text-sm font-semibold text-[var(--color-text)] leading-snug truncate">{{ agent.name }}</h3>
              <span
                v-if="agent.is_template || agent._section === 'templates'"
                class="inline-flex items-center text-[10px] font-medium px-1.5 py-0.5 rounded-full border bg-[rgba(32,104,255,0.08)] text-[#2068FF] border-[#2068FF]/20 shrink-0"
              >
                {{ t('common.template') }}
              </span>
            </div>
            <p class="text-xs text-[var(--color-text-muted)] truncate">
              {{ agent.role }}
              <span v-if="agent.department" class="mx-1">&middot;</span>
              <span v-if="agent.department">{{ agent.department }}</span>
            </p>
          </div>
          <!-- Actions -->
          <div class="flex items-center gap-1 ml-1 shrink-0">
            <button
              @click="cloneAgent(agent)"
              class="p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[#2068FF] hover:bg-[rgba(32,104,255,0.08)] transition-colors"
              :title="agent._section === 'templates' ? t('agents.useTemplate') : t('agents.cloneAgent')"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 0 1-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 0 1 1.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 0 0-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 0 1-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H9.75" />
              </svg>
            </button>
            <button
              v-if="agent._section === 'custom'"
              @click="deleteAgent(agent)"
              class="p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-red-500 hover:bg-red-500/10 transition-colors"
              :title="t('agents.deleteAgent')"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Backstory snippet -->
        <p v-if="agent.backstory" class="text-xs text-[var(--color-text-secondary)] mb-3 line-clamp-2">
          {{ agent.backstory }}
        </p>

        <!-- Personality summary -->
        <div class="flex items-center gap-2 mb-3">
          <span class="text-[10px] font-medium text-[var(--color-text-muted)] uppercase tracking-wider">{{ t('agents.personality') }}</span>
          <span class="text-xs text-[var(--color-text-secondary)]">{{ personalitySummary(agent.personality) }}</span>
        </div>

        <!-- Personality mini-bars -->
        <div v-if="agent.personality" class="grid grid-cols-5 gap-1.5 mb-3">
          <div v-for="(trait, key) in { A: 'analytical', C: 'creative', S: 'assertive', E: 'empathetic', R: 'risk_tolerant' }" :key="key">
            <div class="text-[9px] text-[var(--color-text-muted)] text-center mb-0.5">{{ key }}</div>
            <div class="h-1 rounded-full bg-[var(--color-border)] overflow-hidden">
              <div
                class="h-full rounded-full transition-all"
                :style="{ width: (agent.personality[trait] || 0) + '%', backgroundColor: agent.avatar_color || '#2068FF' }"
              />
            </div>
          </div>
        </div>

        <!-- Expertise tags -->
        <div v-if="agent.expertise_areas?.length" class="flex flex-wrap gap-1.5 mb-3">
          <span
            v-for="area in agent.expertise_areas.slice(0, 3)"
            :key="area"
            class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[var(--color-tint)] text-[var(--color-text-secondary)]"
          >
            {{ area }}
          </span>
          <span
            v-if="agent.expertise_areas.length > 3"
            class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[var(--color-tint)] text-[var(--color-text-muted)]"
          >
            +{{ agent.expertise_areas.length - 3 }}
          </span>
        </div>

        <!-- Footer: style + date -->
        <div class="flex items-center justify-between text-[10px] text-[var(--color-text-muted)] pt-2 border-t border-[var(--color-border)]">
          <span>{{ styleLabel(agent.communication_style) }}</span>
          <span v-if="agent.created_at && agent._section === 'custom'">{{ relativeTime(agent.created_at) }}</span>
          <button
            v-if="agent._section === 'templates'"
            @click="addFromTemplate(agent)"
            class="text-[10px] font-medium text-[#2068FF] hover:underline"
          >
            {{ t('agents.useTemplate') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete confirmation -->
    <ConfirmDialog
      v-model="showDeleteDialog"
      :title="t('agents.deleteAgent')"
      :message="`Are you sure you want to delete &quot;${pendingDeleteAgent?.name || ''}&quot;? This cannot be undone.`"
      :confirmLabel="t('common.delete')"
      :destructive="true"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
