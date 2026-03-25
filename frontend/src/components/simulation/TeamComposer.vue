<script setup>
import { computed, ref } from 'vue'
import PersonaCard from './PersonaCard.vue'
import { useDragAndDrop } from '../../composables/useDragAndDrop'

const props = defineProps({
  availablePersonas: { type: Array, required: true },
  modelValue: { type: Array, required: true },
  maxTeamSize: { type: Number, default: 10 },
})

const emit = defineEmits(['update:modelValue'])

const {
  draggedItem,
  dragSource,
  dragOverTarget,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDragLeave,
  onDrop,
} = useDragAndDrop()

const filterText = ref('')

const poolPersonas = computed(() => {
  const selected = new Set(props.modelValue)
  const pool = props.availablePersonas.filter((p) => !selected.has(p))
  if (!filterText.value) return pool
  const q = filterText.value.toLowerCase()
  return pool.filter((p) => p.toLowerCase().includes(q))
})

const teamFull = computed(() => props.modelValue.length >= props.maxTeamSize)

const isDraggingFromPool = computed(
  () => draggedItem.value != null && dragSource.value === 'pool',
)

const isDraggingFromTeam = computed(
  () => draggedItem.value != null && dragSource.value === 'team',
)

const rejectAnim = ref(false)

function handleDrop(item, source, target) {
  if (target === 'team' && source === 'pool') {
    if (teamFull.value) {
      rejectAnim.value = true
      setTimeout(() => (rejectAnim.value = false), 400)
      return
    }
    if (!props.modelValue.includes(item)) {
      emit('update:modelValue', [...props.modelValue, item])
    }
  } else if (target === 'pool' && source === 'team') {
    removeFromTeam(item)
  }
}

function removeFromTeam(persona) {
  emit(
    'update:modelValue',
    props.modelValue.filter((p) => p !== persona),
  )
}

function handleTeamReorder(dragIndex, dropIndex) {
  if (dragIndex === dropIndex) return
  const list = [...props.modelValue]
  const [moved] = list.splice(dragIndex, 1)
  list.splice(dropIndex, 0, moved)
  emit('update:modelValue', list)
}

const reorderDragIndex = ref(null)
const reorderOverIndex = ref(null)

function onTeamItemDragStart(index, event) {
  reorderDragIndex.value = index
  onDragStart(props.modelValue[index], 'team', event)
}

function onTeamItemDragOver(index, event) {
  event.preventDefault()
  reorderOverIndex.value = index
}

function onTeamItemDrop(index, event) {
  event.preventDefault()
  event.stopPropagation()
  if (dragSource.value === 'team' && reorderDragIndex.value != null) {
    handleTeamReorder(reorderDragIndex.value, index)
  } else if (dragSource.value === 'pool') {
    handleDrop(draggedItem.value, 'pool', 'team')
  }
  reorderDragIndex.value = null
  reorderOverIndex.value = null
}

function onTeamItemDragEnd(event) {
  reorderDragIndex.value = null
  reorderOverIndex.value = null
  onDragEnd(event)
}

function addToTeam(persona) {
  if (teamFull.value || props.modelValue.includes(persona)) return
  emit('update:modelValue', [...props.modelValue, persona])
}
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    <!-- Available Pool -->
    <div>
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
          Available ({{ poolPersonas.length }})
        </span>
      </div>
      <input
        v-model="filterText"
        type="text"
        placeholder="Filter personas..."
        class="w-full mb-2 px-3 py-1.5 text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
      />
      <div
        class="pool-zone space-y-1.5 min-h-[120px] max-h-[280px] overflow-y-auto rounded-lg border-2 border-dashed p-2 transition-colors duration-200"
        :class="
          isDraggingFromTeam && dragOverTarget === 'pool'
            ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
            : isDraggingFromTeam
              ? 'border-[var(--color-primary)]/40 bg-[var(--color-primary-lighter)]'
              : 'border-[var(--color-border)] bg-transparent'
        "
        @dragover="onDragOver('pool', $event)"
        @dragleave="onDragLeave('pool')"
        @drop="onDrop('pool', handleDrop, $event)"
      >
        <PersonaCard
          v-for="persona in poolPersonas"
          :key="persona"
          :name="persona"
          draggable="true"
          @dragstart="onDragStart(persona, 'pool', $event)"
          @dragend="onDragEnd"
          @dblclick="addToTeam(persona)"
        />
        <p
          v-if="poolPersonas.length === 0"
          class="text-xs text-[var(--color-text-muted)] text-center py-4"
        >
          {{ filterText ? 'No matches' : 'All personas assigned' }}
        </p>
      </div>
    </div>

    <!-- Team Slots -->
    <div>
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
          Team ({{ modelValue.length }}/{{ maxTeamSize }})
        </span>
        <span
          v-if="teamFull"
          class="text-[10px] font-medium text-[var(--color-warning)] bg-[var(--color-warning-light)] px-2 py-0.5 rounded-full"
        >
          Full
        </span>
      </div>
      <div
        class="team-zone space-y-1.5 min-h-[120px] max-h-[280px] overflow-y-auto rounded-lg border-2 border-dashed p-2 transition-colors duration-200"
        :class="[
          isDraggingFromPool && dragOverTarget === 'team' && !teamFull
            ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
            : isDraggingFromPool && !teamFull
              ? 'border-[var(--color-primary)]/40 bg-[var(--color-primary-lighter)] team-zone--pulse'
              : 'border-[var(--color-border)] bg-transparent',
          rejectAnim && 'team-zone--reject',
        ]"
        @dragover="onDragOver('team', $event)"
        @dragleave="onDragLeave('team')"
        @drop="onDrop('team', handleDrop, $event)"
      >
        <PersonaCard
          v-for="(persona, index) in modelValue"
          :key="persona"
          :name="persona"
          removable
          draggable="true"
          :class="{
            'border-t-2 border-t-[var(--color-primary)]':
              reorderOverIndex === index && reorderDragIndex !== index,
          }"
          @remove="removeFromTeam(persona)"
          @dragstart="onTeamItemDragStart(index, $event)"
          @dragover="onTeamItemDragOver(index, $event)"
          @drop="onTeamItemDrop(index, $event)"
          @dragend="onTeamItemDragEnd"
        />
        <p
          v-if="modelValue.length === 0"
          class="text-xs text-[var(--color-text-muted)] text-center py-6"
        >
          Drag personas here or double-click to add
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes pulse-border {
  0%,
  100% {
    border-color: rgba(32, 104, 255, 0.2);
  }
  50% {
    border-color: rgba(32, 104, 255, 0.6);
  }
}

.team-zone--pulse {
  animation: pulse-border 1.2s ease-in-out infinite;
}

@keyframes reject-shake {
  0%,
  100% {
    transform: translateX(0);
  }
  20% {
    transform: translateX(-6px);
  }
  40% {
    transform: translateX(6px);
  }
  60% {
    transform: translateX(-4px);
  }
  80% {
    transform: translateX(4px);
  }
}

.team-zone--reject {
  animation: reject-shake 0.4s ease-in-out;
  border-color: var(--color-error) !important;
  background-color: var(--color-error-light) !important;
}
</style>
