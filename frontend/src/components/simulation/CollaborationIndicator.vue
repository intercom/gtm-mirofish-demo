<script setup>
import { ref, computed, inject, watch, onUnmounted } from 'vue'

const polling = inject('polling')
const demoMode = inject('demoMode', ref(false))

const DISCUSSION_TOPICS = [
  'evaluating migration timelines',
  'comparing support platform costs',
  'analyzing AI resolution rates',
  'reviewing customer satisfaction data',
  'debating vendor switching risks',
  'discussing integration requirements',
  'assessing team readiness',
  'exploring automation capabilities',
]

const activeTopicIndex = ref(0)
let topicTimer = null

// Derive active agents from the most recent actions
const activeAgents = computed(() => {
  const actions = polling.recentActions.value
  if (!actions.length) return []

  const maxRound = Math.max(...actions.map(a => a.round_num))
  const recentWindow = Math.max(1, maxRound - 2)

  const agentMap = new Map()
  for (const action of actions) {
    if (action.round_num >= recentWindow && !agentMap.has(action.agent_name)) {
      const parts = action.agent_name?.split(', ') || []
      const firstName = (parts[0] || 'Agent').split(' ')[0]
      const roleParts = (parts[1] || '').split(' @ ')
      agentMap.set(action.agent_name, {
        name: firstName,
        fullName: action.agent_name,
        role: roleParts[0] || '',
        company: roleParts[1] || '',
        initials: firstName.charAt(0).toUpperCase(),
        platform: action.platform,
        actionType: action.action_type,
      })
    }
  }

  return Array.from(agentMap.values()).slice(0, 5)
})

const isActive = computed(() => {
  const rs = polling.runStatus.value?.runner_status
  if (rs === 'running' || rs === 'starting') return true
  // In demo/replay mode, show when actions exist but sim isn't finished
  if (demoMode.value && polling.recentActions.value.length > 0) return true
  return false
})

const currentTopic = computed(() => DISCUSSION_TOPICS[activeTopicIndex.value])

const agentColors = ['#2068FF', '#ff5600', '#AA00FF', '#059669', '#d97706']

function getAgentColor(index) {
  return agentColors[index % agentColors.length]
}

// Rotate discussion topics
function startTopicRotation() {
  stopTopicRotation()
  topicTimer = setInterval(() => {
    activeTopicIndex.value = (activeTopicIndex.value + 1) % DISCUSSION_TOPICS.length
  }, 4000)
}

function stopTopicRotation() {
  if (topicTimer) {
    clearInterval(topicTimer)
    topicTimer = null
  }
}

watch(isActive, (active) => {
  if (active) startTopicRotation()
  else stopTopicRotation()
}, { immediate: true })

onUnmounted(stopTopicRotation)
</script>

<template>
  <div
    v-if="activeAgents.length >= 2 && isActive"
    class="collab-indicator bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4"
  >
    <!-- Header -->
    <div class="flex items-center gap-2 mb-3">
      <span class="collab-pulse-dot" />
      <span class="text-xs font-semibold text-[var(--color-text)] uppercase tracking-wider">Live Collaboration</span>
    </div>

    <!-- Agent Bubbles -->
    <div class="flex items-center mb-3">
      <div class="flex -space-x-2">
        <div
          v-for="(agent, i) in activeAgents"
          :key="agent.fullName"
          class="collab-avatar"
          :style="{
            backgroundColor: getAgentColor(i),
            animationDelay: `${i * 0.15}s`,
            zIndex: activeAgents.length - i,
          }"
          :title="`${agent.name} — ${agent.role}${agent.company ? ' @ ' + agent.company : ''}`"
        >
          {{ agent.initials }}
        </div>
      </div>

      <!-- Connection lines (SVG) -->
      <svg
        v-if="activeAgents.length >= 2"
        class="collab-connections ml-2"
        width="40" height="32"
        viewBox="0 0 40 32"
      >
        <line x1="0" y1="10" x2="20" y2="16" stroke="var(--color-border)" stroke-width="1.5" stroke-dasharray="3 3" class="collab-line" />
        <line x1="0" y1="22" x2="20" y2="16" stroke="var(--color-border)" stroke-width="1.5" stroke-dasharray="3 3" class="collab-line" style="animation-delay: 0.5s" />
        <circle cx="22" cy="16" r="3" fill="var(--color-primary)" class="collab-node-pulse" />
      </svg>

      <!-- Typing indicator bubble -->
      <div class="collab-thought-bubble ml-1">
        <span class="collab-dot" />
        <span class="collab-dot" style="animation-delay: 0.2s" />
        <span class="collab-dot" style="animation-delay: 0.4s" />
      </div>
    </div>

    <!-- Status text -->
    <p class="text-xs text-[var(--color-text-secondary)]">
      <span class="font-medium text-[var(--color-text)]">{{ activeAgents.length }} agents</span>
      are currently {{ currentTopic }}
    </p>

    <!-- Active agent names -->
    <div class="flex flex-wrap gap-1.5 mt-2">
      <span
        v-for="(agent, i) in activeAgents"
        :key="agent.fullName"
        class="text-[10px] px-2 py-0.5 rounded-full font-medium"
        :style="{
          backgroundColor: getAgentColor(i) + '14',
          color: getAgentColor(i),
        }"
      >
        {{ agent.name }}
      </span>
    </div>
  </div>
</template>

<style scoped>
.collab-pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #059669;
  animation: collab-pulse 2s ease-in-out infinite;
}

@keyframes collab-pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(5, 150, 105, 0.4); }
  50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(5, 150, 105, 0); }
}

.collab-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 600;
  border: 2px solid var(--color-surface);
  animation: collab-bob 3s ease-in-out infinite;
  position: relative;
}

@keyframes collab-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.collab-thought-bubble {
  display: flex;
  align-items: center;
  gap: 3px;
  background: var(--color-tint);
  border-radius: 12px;
  padding: 6px 10px;
  position: relative;
}

.collab-thought-bubble::before {
  content: '';
  position: absolute;
  left: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-right: 6px solid var(--color-tint);
}

.collab-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background-color: var(--color-text-muted);
  animation: collab-typing 1.4s ease-in-out infinite;
}

@keyframes collab-typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

.collab-line {
  animation: collab-dash 2s linear infinite;
}

@keyframes collab-dash {
  to { stroke-dashoffset: -12; }
}

.collab-node-pulse {
  animation: collab-node-glow 2s ease-in-out infinite;
}

@keyframes collab-node-glow {
  0%, 100% { r: 3; opacity: 1; }
  50% { r: 4.5; opacity: 0.7; }
}

.collab-connections {
  flex-shrink: 0;
}
</style>
