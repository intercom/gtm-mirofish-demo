<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { teamApi } from '../../api/team'
import { useToast } from '../../composables/useToast'
import Badge from '../common/Badge.vue'

const props = defineProps({
  maxSlots: { type: Number, default: 8 },
  scenarioPersonas: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:team'])

const toast = useToast()

const allPersonas = ref([])
const teamSlots = ref([])
const filterRole = ref('')
const filterCategory = ref('')
const categories = ref([])
const loading = ref(false)
const autoGenerating = ref(false)
const savingTemplate = ref(false)
const templateName = ref('')
const showSaveForm = ref(false)
const draggedPersona = ref(null)
const dragOverSlot = ref(null)
const dragOverPool = ref(false)

const availablePersonas = computed(() => {
  const teamRoles = new Set(teamSlots.value.map((s) => s?.role))
  return allPersonas.value.filter((p) => {
    if (teamRoles.has(p.role)) return false
    if (filterCategory.value && p.category !== filterCategory.value) return false
    if (filterRole.value && !p.role.toLowerCase().includes(filterRole.value.toLowerCase()))
      return false
    return true
  })
})

const filledSlots = computed(() => teamSlots.value.filter(Boolean))

const roleCoverage = computed(() => {
  const required = ['sales', 'marketing', 'cs', 'product', 'finance']
  const filled = new Set(filledSlots.value.map((p) => p.category))
  return required.map((cat) => ({ category: cat, covered: filled.has(cat) }))
})

const coveredCount = computed(() => roleCoverage.value.filter((r) => r.covered).length)

const personalityDiversity = computed(() => {
  const personalities = filledSlots.value.map((p) => p.personality)
  if (personalities.length <= 1) return 0
  const unique = new Set(personalities).size
  return Math.round((unique / personalities.length) * 100)
})

const expertiseCoverage = computed(() => {
  const allPriorities = new Set()
  filledSlots.value.forEach((p) => {
    ;(p.priorities || []).forEach((pr) => allPriorities.add(pr))
  })
  return allPriorities.size
})

const warnings = computed(() => {
  const w = []
  const cats = new Set(filledSlots.value.map((p) => p.category))
  if (filledSlots.value.length > 0 && !cats.has('sales'))
    w.push({ type: 'warning', message: 'No sales perspective — deal insights will be limited' })
  if (filledSlots.value.length > 0 && !cats.has('marketing'))
    w.push({ type: 'info', message: 'No marketing perspective — campaign feedback may lack depth' })
  if (personalityDiversity.value > 0 && personalityDiversity.value < 40)
    w.push({
      type: 'warning',
      message: 'Low diversity — team has too many similar personality types',
    })
  if (filledSlots.value.length > 0 && filledSlots.value.length < 3)
    w.push({ type: 'info', message: 'Small team — consider adding more perspectives' })
  return w
})

watch(
  filledSlots,
  (team) => {
    emit('update:team', team.map((p) => p.role))
  },
  { deep: true },
)

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await teamApi.getPersonas()
    allPersonas.value = data.personas || []
    categories.value = data.categories || []
  } catch {
    // Fallback: build pool from scenarioPersonas prop
    allPersonas.value = props.scenarioPersonas.map((role, i) => ({
      id: `persona-${i}`,
      role,
      category: 'other',
      personality: 'balanced',
      seniority: 'manager',
      priorities: [],
      concerns: [],
      communication_style: '',
    }))
  } finally {
    loading.value = false
  }
  // Initialize empty slots
  teamSlots.value = new Array(props.maxSlots).fill(null)
})

function onDragStart(persona) {
  draggedPersona.value = persona
}

function onDragEnd() {
  draggedPersona.value = null
  dragOverSlot.value = null
  dragOverPool.value = false
}

function onSlotDragOver(e, idx) {
  e.preventDefault()
  dragOverSlot.value = idx
}

function onSlotDragLeave() {
  dragOverSlot.value = null
}

function onSlotDrop(idx) {
  if (!draggedPersona.value) return
  // If dragging from another slot, clear the old slot
  const oldIdx = teamSlots.value.findIndex(
    (s) => s && s.role === draggedPersona.value.role,
  )
  if (oldIdx !== -1) teamSlots.value[oldIdx] = null
  teamSlots.value[idx] = { ...draggedPersona.value }
  dragOverSlot.value = null
  draggedPersona.value = null
}

function onPoolDragOver(e) {
  e.preventDefault()
  dragOverPool.value = true
}

function onPoolDragLeave() {
  dragOverPool.value = false
}

function onPoolDrop() {
  if (!draggedPersona.value) return
  // Remove from team
  const idx = teamSlots.value.findIndex(
    (s) => s && s.role === draggedPersona.value.role,
  )
  if (idx !== -1) teamSlots.value[idx] = null
  dragOverPool.value = false
  draggedPersona.value = null
}

function removeFromSlot(idx) {
  teamSlots.value[idx] = null
}

function addToFirstEmpty(persona) {
  const idx = teamSlots.value.findIndex((s) => s === null)
  if (idx === -1) {
    toast.error('All team slots are full')
    return
  }
  teamSlots.value[idx] = { ...persona }
}

async function autoGenerate() {
  autoGenerating.value = true
  try {
    const { data } = await teamApi.autoGenerate({
      team_size: teamSlots.value.filter((s) => s === null).length,
      existing_roles: filledSlots.value.map((p) => p.role),
    })
    const recommended = data.personas || []
    let slotIdx = 0
    for (const persona of recommended) {
      while (slotIdx < teamSlots.value.length && teamSlots.value[slotIdx] !== null) {
        slotIdx++
      }
      if (slotIdx >= teamSlots.value.length) break
      teamSlots.value[slotIdx] = {
        ...allPersonas.value.find((p) => p.role === persona.role) || persona,
      }
      slotIdx++
    }
    toast.success(`Added ${recommended.length} recommended personas`)
  } catch {
    // Fallback: fill with diverse selection from local pool
    const teamRoles = new Set(filledSlots.value.map((p) => p.role))
    const available = allPersonas.value.filter((p) => !teamRoles.has(p.role))
    let added = 0
    for (const p of available) {
      const idx = teamSlots.value.findIndex((s) => s === null)
      if (idx === -1) break
      teamSlots.value[idx] = { ...p }
      added++
    }
    if (added) toast.info(`Auto-filled ${added} slots from available pool`)
  } finally {
    autoGenerating.value = false
  }
}

function clearTeam() {
  teamSlots.value = new Array(props.maxSlots).fill(null)
}

async function saveTemplate() {
  if (!templateName.value.trim() || filledSlots.value.length === 0) return
  savingTemplate.value = true
  try {
    await teamApi.saveTemplate({
      name: templateName.value.trim(),
      roles: filledSlots.value.map((p) => p.role),
    })
    toast.success(`Template "${templateName.value}" saved`)
    templateName.value = ''
    showSaveForm.value = false
  } catch {
    toast.error('Failed to save template')
  } finally {
    savingTemplate.value = false
  }
}

const categoryLabel = {
  sales: 'Sales',
  marketing: 'Marketing',
  cs: 'CS',
  product: 'Product',
  finance: 'Finance',
  executive: 'Exec',
  operations: 'Ops',
  risk: 'Risk',
  other: 'Other',
}

const categoryBadgeVariant = {
  sales: 'orange',
  marketing: 'primary',
  cs: 'success',
  product: 'info',
  finance: 'warning',
  executive: 'error',
  operations: 'default',
  risk: 'error',
  other: 'default',
}
</script>

<template>
  <div class="space-y-4">
    <!-- Header row -->
    <div class="flex items-center justify-between">
      <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
        Team Composition
        <span class="normal-case tracking-normal text-[var(--color-text-muted)]">
          ({{ filledSlots.length }}/{{ maxSlots }})
        </span>
      </label>
      <div class="flex gap-2">
        <button
          v-if="filledSlots.length > 0 && !showSaveForm"
          @click="showSaveForm = true"
          class="px-2.5 py-1 text-[11px] rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] transition-colors"
        >
          Save Template
        </button>
        <button
          v-if="filledSlots.length > 0"
          @click="clearTeam"
          class="px-2.5 py-1 text-[11px] rounded-md border border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-red-400 hover:text-red-500 transition-colors"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Save Template Form -->
    <div
      v-if="showSaveForm"
      class="flex gap-2 items-center p-3 rounded-lg border border-[var(--color-primary)]/20 bg-[rgba(32,104,255,0.03)]"
    >
      <input
        v-model="templateName"
        placeholder="Template name..."
        class="flex-1 px-3 py-1.5 text-sm border border-[var(--color-border)] rounded-md bg-[var(--color-surface)] focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
        @keydown.enter="saveTemplate"
      />
      <button
        @click="saveTemplate"
        :disabled="!templateName.trim() || savingTemplate"
        class="px-3 py-1.5 text-xs font-medium rounded-md bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] disabled:opacity-50 transition-colors"
      >
        {{ savingTemplate ? 'Saving...' : 'Save' }}
      </button>
      <button
        @click="showSaveForm = false; templateName = ''"
        class="px-2 py-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
      >
        Cancel
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Left Panel: Persona Pool -->
      <div
        class="rounded-lg border transition-colors p-4"
        :class="dragOverPool
          ? 'border-[var(--color-primary)] bg-[rgba(32,104,255,0.03)]'
          : 'border-[var(--color-border)] bg-[var(--color-surface)]'"
        @dragover="onPoolDragOver"
        @dragleave="onPoolDragLeave"
        @drop="onPoolDrop"
      >
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider">
            Available Personas
          </span>
          <span class="text-[10px] text-[var(--color-text-muted)]">
            {{ availablePersonas.length }} available
          </span>
        </div>

        <!-- Filters -->
        <div class="flex gap-2 mb-3">
          <input
            v-model="filterRole"
            type="text"
            placeholder="Filter by role..."
            class="flex-1 px-2.5 py-1.5 text-xs border border-[var(--color-border)] rounded-md bg-[var(--color-surface)] focus:ring-1 focus:ring-[var(--color-primary)] focus:border-transparent"
          />
          <select
            v-model="filterCategory"
            class="px-2 py-1.5 text-xs border border-[var(--color-border)] rounded-md bg-[var(--color-surface)] text-[var(--color-text-secondary)]"
          >
            <option value="">All</option>
            <option v-for="cat in categories" :key="cat" :value="cat">
              {{ categoryLabel[cat] || cat }}
            </option>
          </select>
        </div>

        <!-- Persona Cards -->
        <div v-if="loading" class="text-center py-6 text-xs text-[var(--color-text-muted)]">
          Loading personas...
        </div>
        <div v-else class="space-y-1.5 max-h-[320px] overflow-y-auto pr-1">
          <div
            v-for="persona in availablePersonas"
            :key="persona.id"
            draggable="true"
            @dragstart="onDragStart(persona)"
            @dragend="onDragEnd"
            @dblclick="addToFirstEmpty(persona)"
            class="flex items-center gap-2.5 px-3 py-2 rounded-lg border cursor-grab active:cursor-grabbing transition-all select-none group"
            :class="draggedPersona?.role === persona.role
              ? 'border-[var(--color-primary)] bg-[rgba(32,104,255,0.05)] opacity-60'
              : 'border-[var(--color-border)] hover:border-[var(--color-primary)] hover:shadow-sm bg-[var(--card-bg)]'"
          >
            <!-- Drag handle -->
            <svg class="w-3.5 h-3.5 text-[var(--color-text-muted)] shrink-0 opacity-40 group-hover:opacity-100" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>

            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-[var(--color-text)] truncate">{{ persona.role }}</div>
              <div class="text-[10px] text-[var(--color-text-muted)] truncate">
                {{ persona.seniority }} · {{ persona.personality }}
              </div>
            </div>

            <Badge :variant="categoryBadgeVariant[persona.category] || 'default'" class="shrink-0">
              {{ categoryLabel[persona.category] || persona.category }}
            </Badge>
          </div>

          <div
            v-if="availablePersonas.length === 0 && !loading"
            class="text-center py-4 text-xs text-[var(--color-text-muted)]"
          >
            {{ filterRole || filterCategory ? 'No matching personas' : 'All personas assigned' }}
          </div>
        </div>
      </div>

      <!-- Right Panel: Team Slots -->
      <div class="space-y-3">
        <!-- Team Slots Grid -->
        <div class="grid grid-cols-2 gap-2">
          <div
            v-for="(slot, idx) in teamSlots"
            :key="idx"
            @dragover="onSlotDragOver($event, idx)"
            @dragleave="onSlotDragLeave"
            @drop="onSlotDrop(idx)"
            class="relative rounded-lg border-2 transition-all min-h-[72px] flex items-center"
            :class="[
              slot
                ? 'border-[var(--color-border)] bg-[var(--card-bg)] p-2.5'
                : dragOverSlot === idx
                  ? 'border-[var(--color-primary)] bg-[rgba(32,104,255,0.05)] border-solid'
                  : 'border-dashed border-[var(--color-border)] hover:border-[var(--color-text-muted)]',
            ]"
          >
            <!-- Filled slot -->
            <div
              v-if="slot"
              draggable="true"
              @dragstart="onDragStart(slot)"
              @dragend="onDragEnd"
              class="flex items-start gap-2 w-full cursor-grab active:cursor-grabbing"
            >
              <div class="flex-1 min-w-0">
                <div class="text-xs font-semibold text-[var(--color-text)] truncate">{{ slot.role }}</div>
                <Badge :variant="categoryBadgeVariant[slot.category] || 'default'" class="mt-1">
                  {{ categoryLabel[slot.category] || slot.category }}
                </Badge>
              </div>
              <button
                @click.stop="removeFromSlot(idx)"
                class="shrink-0 w-5 h-5 flex items-center justify-center rounded-full text-[var(--color-text-muted)] hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
              >
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Empty slot -->
            <div v-else class="w-full text-center">
              <div class="text-[10px] text-[var(--color-text-muted)]">
                {{ dragOverSlot === idx ? 'Drop here' : `Slot ${idx + 1}` }}
              </div>
            </div>
          </div>
        </div>

        <!-- Auto-generate button -->
        <button
          @click="autoGenerate"
          :disabled="autoGenerating || filledSlots.length >= maxSlots"
          class="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium rounded-lg border border-[var(--color-primary)]/30 text-[var(--color-primary)] hover:bg-[rgba(32,104,255,0.05)] disabled:opacity-40 transition-colors"
        >
          <svg class="w-3.5 h-3.5" :class="{ 'animate-spin': autoGenerating }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
          </svg>
          {{ autoGenerating ? 'Generating...' : 'Auto-fill empty slots' }}
        </button>

        <!-- Balance Indicators -->
        <div
          v-if="filledSlots.length > 0"
          class="rounded-lg border border-[var(--color-border)] bg-[var(--card-bg)] p-3 space-y-3"
        >
          <span class="text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
            Team Balance
          </span>

          <!-- Role Coverage -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-[11px] text-[var(--color-text-secondary)]">Role Coverage</span>
              <span class="text-[11px] font-medium" :class="coveredCount >= 4 ? 'text-green-600' : coveredCount >= 2 ? 'text-amber-500' : 'text-red-500'">
                {{ coveredCount }}/5
              </span>
            </div>
            <div class="flex gap-1">
              <div
                v-for="rc in roleCoverage"
                :key="rc.category"
                class="flex-1 h-1.5 rounded-full transition-colors"
                :class="rc.covered ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-border)]'"
                :title="`${categoryLabel[rc.category]}: ${rc.covered ? 'Covered' : 'Missing'}`"
              />
            </div>
            <div class="flex gap-1 mt-1">
              <span
                v-for="rc in roleCoverage"
                :key="rc.category"
                class="flex-1 text-center text-[9px]"
                :class="rc.covered ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-muted)]'"
              >
                {{ categoryLabel[rc.category] }}
              </span>
            </div>
          </div>

          <!-- Personality Diversity -->
          <div>
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-[11px] text-[var(--color-text-secondary)]">Personality Diversity</span>
              <span class="text-[11px] font-medium" :class="personalityDiversity >= 60 ? 'text-green-600' : personalityDiversity >= 40 ? 'text-amber-500' : 'text-red-500'">
                {{ personalityDiversity }}%
              </span>
            </div>
            <div class="w-full h-1.5 rounded-full bg-[var(--color-border)]">
              <div
                class="h-full rounded-full transition-all"
                :class="personalityDiversity >= 60 ? 'bg-green-500' : personalityDiversity >= 40 ? 'bg-amber-500' : 'bg-red-500'"
                :style="{ width: `${personalityDiversity}%` }"
              />
            </div>
          </div>

          <!-- Expertise Coverage -->
          <div>
            <div class="flex items-center justify-between">
              <span class="text-[11px] text-[var(--color-text-secondary)]">Expertise Areas</span>
              <span class="text-[11px] font-medium text-[var(--color-text)]">
                {{ expertiseCoverage }} topics
              </span>
            </div>
          </div>
        </div>

        <!-- Warnings -->
        <div v-if="warnings.length > 0" class="space-y-1.5">
          <div
            v-for="(w, i) in warnings"
            :key="i"
            class="flex items-start gap-2 px-3 py-2 rounded-lg text-xs"
            :class="w.type === 'warning'
              ? 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20'
              : 'bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20'"
          >
            <svg class="w-3.5 h-3.5 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path v-if="w.type === 'warning'" stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0zm-9-3.75h.008v.008H12V8.25z" />
            </svg>
            <span>{{ w.message }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
