<script setup>
import { ref, computed, watch } from 'vue'
import { AppButton, AppCard, AppBadge } from '../common'

const emit = defineEmits(['start'])

const topic = ref('')
const format = ref('oxford')
const moderatorMode = ref('ai')
const selectedModerator = ref(null)
const rebuttals = ref(2)
const roundMinutes = ref(5)

const suggestedTopics = [
  'We should prioritize retention over acquisition',
  'Should we match competitor pricing?',
  'Is the current pipeline sufficient for Q4 target?',
  'Should we invest in PLG vs sales-led?',
  'AI-first support will replace traditional ticketing within 2 years',
  'We should expand into the enterprise segment before deepening SMB',
]

const formats = [
  {
    value: 'oxford',
    label: 'Oxford',
    description: 'Structured for/against teams with formal rounds',
    icon: '\u2694',
  },
  {
    value: 'panel',
    label: 'Panel',
    description: 'Moderated discussion with guided questions',
    icon: '\u{1F399}',
  },
  {
    value: 'roundtable',
    label: 'Roundtable',
    description: 'Free-form discussion among all participants',
    icon: '\u{1F465}',
  },
]

const defaultAgents = [
  { id: 'vp-support', name: 'VP of Support', role: 'Leadership' },
  { id: 'cx-director', name: 'CX Director', role: 'Leadership' },
  { id: 'it-leader', name: 'IT Leader', role: 'Technical' },
  { id: 'head-ops', name: 'Head of Operations', role: 'Operations' },
  { id: 'cfo', name: 'CFO', role: 'Finance' },
  { id: 'product-mgr', name: 'Product Manager', role: 'Product' },
  { id: 'support-mgr', name: 'Support Manager', role: 'Support' },
  { id: 'tech-eval', name: 'Technical Evaluator', role: 'Technical' },
  { id: 'champion', name: 'Champion', role: 'Advocate' },
  { id: 'end-user', name: 'End User', role: 'User' },
]

const forTeam = ref([])
const againstTeam = ref([])
const participants = ref([])

const isOxford = computed(() => format.value === 'oxford')

const unassignedAgents = computed(() => {
  if (isOxford.value) {
    const assigned = new Set([...forTeam.value, ...againstTeam.value])
    return defaultAgents.filter(a => !assigned.has(a.id))
  }
  const selected = new Set(participants.value)
  return defaultAgents.filter(a => !selected.has(a.id))
})

const availableModerators = computed(() => {
  if (isOxford.value) {
    const assigned = new Set([...forTeam.value, ...againstTeam.value])
    return defaultAgents.filter(a => !assigned.has(a.id))
  }
  return defaultAgents.filter(a => !participants.value.includes(a.id))
})

const canStart = computed(() => {
  if (!topic.value.trim()) return false
  if (isOxford.value) return forTeam.value.length > 0 && againstTeam.value.length > 0
  return participants.value.length >= 2
})

watch(format, () => {
  forTeam.value = []
  againstTeam.value = []
  participants.value = []
  selectedModerator.value = null
})

function selectTopic(t) {
  topic.value = t
}

function agentById(id) {
  return defaultAgents.find(a => a.id === id)
}

function assignTo(agentId, team) {
  removeFromAll(agentId)
  if (team === 'for') forTeam.value.push(agentId)
  else if (team === 'against') againstTeam.value.push(agentId)
  else if (team === 'participants') participants.value.push(agentId)
}

function removeFromAll(agentId) {
  forTeam.value = forTeam.value.filter(id => id !== agentId)
  againstTeam.value = againstTeam.value.filter(id => id !== agentId)
  participants.value = participants.value.filter(id => id !== agentId)
  if (selectedModerator.value === agentId) selectedModerator.value = null
}

function unassign(agentId) {
  removeFromAll(agentId)
}

// Drag & drop
const draggedAgent = ref(null)

function onDragStart(agentId) {
  draggedAgent.value = agentId
}

function onDrop(team) {
  if (!draggedAgent.value) return
  assignTo(draggedAgent.value, team)
  draggedAgent.value = null
}

function onDragOver(e) {
  e.preventDefault()
}

function startDebate() {
  if (!canStart.value) return

  const agentList = isOxford.value
    ? [...forTeam.value, ...againstTeam.value]
    : participants.value

  emit('start', {
    topic: topic.value.trim(),
    format: format.value,
    agents: agentList.map(id => agentById(id)),
    forTeam: isOxford.value ? forTeam.value.map(id => agentById(id)) : [],
    againstTeam: isOxford.value ? againstTeam.value.map(id => agentById(id)) : [],
    moderator: moderatorMode.value === 'ai' ? { id: 'ai', name: 'AI Moderator', role: 'Moderator' } : agentById(selectedModerator.value),
    rounds: rebuttals.value,
    roundMinutes: roundMinutes.value,
  })
}

function initials(name) {
  return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
}
</script>

<template>
  <div class="space-y-6">
    <!-- Topic -->
    <AppCard>
      <template #header>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Debate Topic</h3>
      </template>

      <input
        v-model="topic"
        type="text"
        placeholder="Enter a debate proposition, e.g. 'We should prioritize retention over acquisition'"
        class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-colors"
      />

      <div class="mt-4">
        <p class="text-xs text-[var(--color-text-muted)] mb-2">Suggested topics</p>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="t in suggestedTopics"
            :key="t"
            @click="selectTopic(t)"
            class="px-3 py-1.5 text-xs rounded-full border transition-colors cursor-pointer"
            :class="topic === t
              ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
              : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
          >
            {{ t }}
          </button>
        </div>
      </div>
    </AppCard>

    <!-- Format -->
    <AppCard>
      <template #header>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Debate Format</h3>
      </template>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          v-for="f in formats"
          :key="f.value"
          @click="format = f.value"
          class="text-left p-4 rounded-lg border transition-all cursor-pointer"
          :class="format === f.value
            ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
            : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-primary)]'"
        >
          <div class="flex items-center gap-2 mb-1.5">
            <span class="text-lg">{{ f.icon }}</span>
            <span class="text-sm font-semibold text-[var(--color-text)]">{{ f.label }}</span>
          </div>
          <p class="text-xs text-[var(--color-text-muted)] leading-relaxed">{{ f.description }}</p>
        </button>
      </div>
    </AppCard>

    <!-- Agent Assignment -->
    <AppCard>
      <template #header>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">
          {{ isOxford ? 'Team Assignment' : 'Participants' }}
        </h3>
      </template>

      <!-- Oxford: For / Against columns -->
      <div v-if="isOxford" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- For Team -->
          <div
            class="rounded-lg border-2 border-dashed p-4 min-h-[120px] transition-colors"
            :class="draggedAgent ? 'border-[var(--color-primary)] bg-[rgba(32,104,255,0.03)]' : 'border-[var(--color-border)]'"
            @dragover="onDragOver"
            @drop="onDrop('for')"
          >
            <div class="flex items-center gap-2 mb-3">
              <AppBadge variant="primary">FOR</AppBadge>
              <span class="text-xs text-[var(--color-text-muted)]">{{ forTeam.length }} agent{{ forTeam.length !== 1 ? 's' : '' }}</span>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="id in forTeam"
                :key="id"
                class="inline-flex items-center gap-1.5 pl-1 pr-2 py-1 rounded-full bg-[rgba(32,104,255,0.1)] text-xs text-[var(--color-primary)]"
              >
                <span class="w-5 h-5 rounded-full bg-[var(--color-primary)] text-white text-[10px] flex items-center justify-center font-semibold">
                  {{ initials(agentById(id).name) }}
                </span>
                {{ agentById(id).name }}
                <button @click="unassign(id)" class="ml-0.5 hover:text-red-500 cursor-pointer">&times;</button>
              </span>
            </div>
            <p v-if="forTeam.length === 0" class="text-xs text-[var(--color-text-muted)] italic">
              Drag agents here or click + below
            </p>
          </div>

          <!-- Against Team -->
          <div
            class="rounded-lg border-2 border-dashed p-4 min-h-[120px] transition-colors"
            :class="draggedAgent ? 'border-[var(--color-fin-orange)] bg-[rgba(255,86,0,0.03)]' : 'border-[var(--color-border)]'"
            @dragover="onDragOver"
            @drop="onDrop('against')"
          >
            <div class="flex items-center gap-2 mb-3">
              <AppBadge variant="warning">AGAINST</AppBadge>
              <span class="text-xs text-[var(--color-text-muted)]">{{ againstTeam.length }} agent{{ againstTeam.length !== 1 ? 's' : '' }}</span>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="id in againstTeam"
                :key="id"
                class="inline-flex items-center gap-1.5 pl-1 pr-2 py-1 rounded-full bg-[rgba(255,86,0,0.1)] text-xs text-[var(--color-fin-orange)]"
              >
                <span class="w-5 h-5 rounded-full bg-[var(--color-fin-orange)] text-white text-[10px] flex items-center justify-center font-semibold">
                  {{ initials(agentById(id).name) }}
                </span>
                {{ agentById(id).name }}
                <button @click="unassign(id)" class="ml-0.5 hover:text-red-500 cursor-pointer">&times;</button>
              </span>
            </div>
            <p v-if="againstTeam.length === 0" class="text-xs text-[var(--color-text-muted)] italic">
              Drag agents here or click + below
            </p>
          </div>
        </div>
      </div>

      <!-- Panel / Roundtable: simple participant list -->
      <div
        v-else
        class="rounded-lg border-2 border-dashed p-4 min-h-[120px] transition-colors"
        :class="draggedAgent ? 'border-[var(--color-primary)] bg-[rgba(32,104,255,0.03)]' : 'border-[var(--color-border)]'"
        @dragover="onDragOver"
        @drop="onDrop('participants')"
      >
        <div class="flex items-center gap-2 mb-3">
          <span class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Participants</span>
          <span class="text-xs text-[var(--color-text-muted)]">{{ participants.length }} selected</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="id in participants"
            :key="id"
            class="inline-flex items-center gap-1.5 pl-1 pr-2 py-1 rounded-full bg-[rgba(32,104,255,0.1)] text-xs text-[var(--color-primary)]"
          >
            <span class="w-5 h-5 rounded-full bg-[var(--color-primary)] text-white text-[10px] flex items-center justify-center font-semibold">
              {{ initials(agentById(id).name) }}
            </span>
            {{ agentById(id).name }}
            <button @click="unassign(id)" class="ml-0.5 hover:text-red-500 cursor-pointer">&times;</button>
          </span>
        </div>
        <p v-if="participants.length === 0" class="text-xs text-[var(--color-text-muted)] italic">
          Drag agents here or click + below
        </p>
      </div>

      <!-- Available agents pool -->
      <div v-if="unassignedAgents.length > 0" class="mt-4">
        <p class="text-xs text-[var(--color-text-muted)] mb-2">Available agents</p>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="agent in unassignedAgents"
            :key="agent.id"
            draggable="true"
            @dragstart="onDragStart(agent.id)"
            class="group inline-flex items-center gap-1.5 pl-1 pr-1 py-1 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] text-xs text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] cursor-grab active:cursor-grabbing transition-colors"
          >
            <span class="w-5 h-5 rounded-full bg-[var(--color-tint)] text-[var(--color-text-muted)] text-[10px] flex items-center justify-center font-semibold">
              {{ initials(agent.name) }}
            </span>
            <span>{{ agent.name }}</span>
            <!-- Quick-assign buttons -->
            <template v-if="isOxford">
              <button
                @click.stop="assignTo(agent.id, 'for')"
                class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)] hover:bg-[var(--color-primary)] hover:text-white transition-colors cursor-pointer"
                title="Assign to For team"
              >F</button>
              <button
                @click.stop="assignTo(agent.id, 'against')"
                class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-[rgba(255,86,0,0.1)] text-[var(--color-fin-orange)] hover:bg-[var(--color-fin-orange)] hover:text-white transition-colors cursor-pointer"
                title="Assign to Against team"
              >A</button>
            </template>
            <button
              v-else
              @click.stop="assignTo(agent.id, 'participants')"
              class="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)] hover:bg-[var(--color-primary)] hover:text-white transition-colors cursor-pointer"
              title="Add to participants"
            >+</button>
          </div>
        </div>
      </div>
    </AppCard>

    <!-- Moderator + Rounds -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Moderator -->
      <AppCard>
        <template #header>
          <h3 class="text-sm font-semibold text-[var(--color-text)]">Moderator</h3>
        </template>

        <div class="flex gap-2 mb-3">
          <button
            @click="moderatorMode = 'ai'; selectedModerator = null"
            class="flex-1 py-2 text-xs font-medium rounded-lg border transition-colors cursor-pointer"
            :class="moderatorMode === 'ai'
              ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
              : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
          >
            AI Moderator
          </button>
          <button
            @click="moderatorMode = 'agent'"
            class="flex-1 py-2 text-xs font-medium rounded-lg border transition-colors cursor-pointer"
            :class="moderatorMode === 'agent'
              ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
              : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
          >
            Select Agent
          </button>
          <button
            @click="moderatorMode = 'none'; selectedModerator = null"
            class="flex-1 py-2 text-xs font-medium rounded-lg border transition-colors cursor-pointer"
            :class="moderatorMode === 'none'
              ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
              : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
          >
            No Moderator
          </button>
        </div>

        <div v-if="moderatorMode === 'ai'" class="flex items-center gap-2 p-3 rounded-lg bg-[rgba(32,104,255,0.05)] border border-[var(--color-primary)]/10">
          <span class="w-8 h-8 rounded-full bg-[var(--color-primary)] text-white text-xs flex items-center justify-center font-semibold">AI</span>
          <div>
            <p class="text-sm font-medium text-[var(--color-text)]">AI Moderator</p>
            <p class="text-xs text-[var(--color-text-muted)]">LLM-powered moderation with balanced questioning</p>
          </div>
        </div>

        <div v-else-if="moderatorMode === 'agent'">
          <div v-if="availableModerators.length === 0" class="text-xs text-[var(--color-text-muted)] italic">
            All agents are assigned to teams. Unassign one to use as moderator.
          </div>
          <div v-else class="flex flex-wrap gap-2">
            <button
              v-for="agent in availableModerators"
              :key="agent.id"
              @click="selectedModerator = selectedModerator === agent.id ? null : agent.id"
              class="inline-flex items-center gap-1.5 pl-1 pr-2.5 py-1 rounded-full border transition-colors text-xs cursor-pointer"
              :class="selectedModerator === agent.id
                ? 'border-[var(--color-primary)] bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]'
                : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]'"
            >
              <span class="w-5 h-5 rounded-full bg-[var(--color-tint)] text-[var(--color-text-muted)] text-[10px] flex items-center justify-center font-semibold">
                {{ initials(agent.name) }}
              </span>
              {{ agent.name }}
            </button>
          </div>
        </div>

        <p v-else class="text-xs text-[var(--color-text-muted)]">
          No moderator — agents will debate freely.
        </p>
      </AppCard>

      <!-- Round Configuration -->
      <AppCard>
        <template #header>
          <h3 class="text-sm font-semibold text-[var(--color-text)]">Round Configuration</h3>
        </template>

        <div class="space-y-4">
          <div>
            <label class="block text-xs text-[var(--color-text-muted)] mb-2">Rebuttal Rounds</label>
            <div class="flex gap-2">
              <button
                v-for="n in [1, 2, 3, 4]"
                :key="n"
                @click="rebuttals = n"
                class="flex-1 px-3 py-2 text-xs rounded-lg border transition-colors cursor-pointer"
                :class="rebuttals === n
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
              >
                {{ n }}
              </button>
            </div>
          </div>

          <div>
            <label class="block text-xs text-[var(--color-text-muted)] mb-2">Minutes per Round</label>
            <div class="flex gap-2">
              <button
                v-for="m in [3, 5, 10, 15]"
                :key="m"
                @click="roundMinutes = m"
                class="flex-1 px-3 py-2 text-xs rounded-lg border transition-colors cursor-pointer"
                :class="roundMinutes === m
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] border-[var(--color-border)] hover:border-[var(--color-primary)]'"
              >
                {{ m }}m
              </button>
            </div>
          </div>

          <div class="p-3 rounded-lg bg-[var(--color-tint)]">
            <p class="text-xs text-[var(--color-text-muted)]">
              Estimated duration:
              <span class="font-semibold text-[var(--color-text)]">
                {{ (rebuttals + 2) * roundMinutes }}min
              </span>
              <span class="text-[var(--color-text-muted)]">
                (opening + {{ rebuttals }} rebuttal{{ rebuttals !== 1 ? 's' : '' }} + closing)
              </span>
            </p>
          </div>
        </div>
      </AppCard>
    </div>

    <!-- Start button -->
    <div class="flex justify-end">
      <AppButton
        :disabled="!canStart"
        size="lg"
        @click="startDebate"
      >
        Start Debate
      </AppButton>
    </div>
  </div>
</template>
