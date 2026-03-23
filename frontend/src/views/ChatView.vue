<script setup>
import { ref, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import EmptyState from '../components/ui/EmptyState.vue'
import StatusIndicator from '../components/common/StatusIndicator.vue'
import { chatApi } from '../api/chat'
import { useSimulationStore } from '../stores/simulation'
import { useToast } from '../composables/useToast'

const props = defineProps({ taskId: String })
const route = useRoute()
const simulation = useSimulationStore()
const toast = useToast()

const messages = ref([])
const input = ref('')
const sending = ref(false)
const messagesEnd = ref(null)

const simulationId = computed(() => simulation.simulationTaskId || props.taskId)

const chatHistory = computed(() =>
  messages.value
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map(({ role, content }) => ({ role, content })),
)

async function scrollToBottom() {
  await nextTick()
  messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
}

async function send() {
  if (!input.value.trim() || sending.value) return

  const text = input.value.trim()
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  scrollToBottom()
  sending.value = true

  try {
    const { data: res } = await chatApi.send({
      simulation_id: simulationId.value,
      message: text,
      chat_history: chatHistory.value.slice(0, -1),
    })

    if (res.success) {
      messages.value.push({
        role: 'assistant',
        content: res.data.response,
        toolCalls: res.data.tool_calls || [],
        sources: res.data.sources || [],
      })
    } else {
      throw new Error(res.error || 'Unknown error')
    }
  } catch (e) {
    messages.value.push({
      role: 'error',
      content: `Something went wrong — ${e.message}`,
    })
    toast.error(`Chat error: ${e.message}`)
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function toolIcon(name) {
  const icons = {
    insight_forge: '🔍',
    panorama_search: '🌐',
    entity_lookup: '📋',
    timeline_query: '📅',
    sentiment_analysis: '💬',
    network_analysis: '🔗',
  }
  return icons[name] || '⚙️'
}

function formatToolName(name) {
  return name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-120px)]">
    <!-- Context Bar -->
    <div
      class="flex items-center justify-between px-6 py-3 border-b border-[var(--color-border)] bg-[var(--color-surface)]"
    >
      <div class="flex items-center gap-3">
        <h1 class="text-base font-semibold text-[var(--color-text)]">Chat with Simulation</h1>
        <StatusIndicator :status="simulation.status === 'complete' ? 'complete' : simulation.isActive ? 'running' : 'idle'">
          <span class="text-[var(--color-text-secondary)]">
            {{ simulation.status === 'complete' ? 'Simulation complete' : simulation.isActive ? 'Simulation running' : 'Idle' }}
          </span>
        </StatusIndicator>
      </div>
      <div class="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <span v-if="simulationId">ID: {{ simulationId }}</span>
        <span v-if="messages.length">&middot; {{ messages.filter((m) => m.role === 'user').length }} messages</span>
      </div>
    </div>

    <!-- Messages -->
    <div class="flex-1 overflow-y-auto px-4 md:px-6 py-6">
      <div class="max-w-2xl mx-auto space-y-4">
        <EmptyState
          v-if="messages.length === 0 && !sending"
          icon="💬"
          title="Chat with the Simulation"
          description="Ask follow-up questions about the simulated world and its predictions."
        />

        <TransitionGroup name="slide-up">
          <div v-for="(msg, i) in messages" :key="i">
            <!-- User message -->
            <div v-if="msg.role === 'user'" class="flex justify-end mb-4">
              <div class="max-w-[80%] bg-[#2068FF] text-white rounded-2xl rounded-br-md px-4 py-3 text-sm">
                {{ msg.content }}
              </div>
            </div>

            <!-- Assistant message -->
            <div v-else-if="msg.role === 'assistant'" class="flex justify-start mb-4">
              <div class="max-w-[80%]">
                <div
                  class="bg-[var(--color-bg-alt)] text-[var(--color-text)] rounded-2xl rounded-bl-md px-4 py-3 text-sm leading-relaxed"
                >
                  <div class="text-xs font-medium text-[var(--color-fin-orange)] mb-1">MiroFish</div>
                  <div class="whitespace-pre-wrap">{{ msg.content }}</div>
                </div>

                <!-- Tool Calls -->
                <div v-if="msg.toolCalls?.length" class="mt-2 space-y-1">
                  <details
                    v-for="(tool, ti) in msg.toolCalls"
                    :key="ti"
                    class="group border border-[var(--color-border)] rounded-lg overflow-hidden"
                  >
                    <summary
                      class="flex items-center gap-2 px-3 py-2 text-xs font-medium text-[var(--color-text-secondary)] cursor-pointer hover:bg-[var(--color-primary-lighter)] select-none"
                    >
                      <span>{{ toolIcon(tool.name || tool.tool) }}</span>
                      <span>{{ formatToolName(tool.name || tool.tool || 'Tool Call') }}</span>
                      <span class="ml-auto text-[var(--color-text-muted)] group-open:rotate-90 transition-transform">▶</span>
                    </summary>
                    <div class="px-3 py-2 text-xs bg-[var(--color-bg)] border-t border-[var(--color-border)]">
                      <pre
                        v-if="tool.arguments || tool.input"
                        class="font-mono text-[var(--color-text-muted)] whitespace-pre-wrap break-all"
                      >{{ JSON.stringify(tool.arguments || tool.input, null, 2) }}</pre>
                      <div v-if="tool.result || tool.output" class="mt-2 pt-2 border-t border-[var(--color-border)]">
                        <div class="font-medium text-[var(--color-text-secondary)] mb-1">Result</div>
                        <pre class="font-mono text-[var(--color-text-muted)] whitespace-pre-wrap break-all">{{
                          typeof (tool.result || tool.output) === 'string'
                            ? (tool.result || tool.output)
                            : JSON.stringify(tool.result || tool.output, null, 2)
                        }}</pre>
                      </div>
                    </div>
                  </details>
                </div>

                <!-- Sources -->
                <div v-if="msg.sources?.length" class="mt-2 flex flex-wrap gap-1">
                  <span
                    v-for="(src, si) in msg.sources"
                    :key="si"
                    class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-[var(--color-primary-light)] text-[var(--color-primary)]"
                  >
                    📎 {{ typeof src === 'string' ? src : src.title || src.name || `Source ${si + 1}` }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Error message -->
            <div v-else-if="msg.role === 'error'" class="flex justify-start mb-4">
              <div
                class="max-w-[80%] bg-[var(--color-error-light)] border border-[rgba(239,68,68,0.2)] text-[var(--color-text)] rounded-2xl rounded-bl-md px-4 py-3 text-sm"
              >
                <div class="text-xs font-medium text-[var(--color-error)] mb-1">Error</div>
                {{ msg.content }}
              </div>
            </div>
          </div>
        </TransitionGroup>

        <!-- Typing indicator -->
        <div v-if="sending" class="flex justify-start mb-4">
          <div class="bg-[var(--color-bg-alt)] rounded-2xl rounded-bl-md px-4 py-3">
            <div class="text-xs font-medium text-[var(--color-fin-orange)] mb-1">MiroFish</div>
            <div class="flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-[var(--color-text-muted)] animate-bounce [animation-delay:0ms]" />
              <span class="w-2 h-2 rounded-full bg-[var(--color-text-muted)] animate-bounce [animation-delay:150ms]" />
              <span class="w-2 h-2 rounded-full bg-[var(--color-text-muted)] animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        </div>

        <div ref="messagesEnd" />
      </div>
    </div>

    <!-- Input -->
    <div class="border-t border-[var(--color-border)] bg-[var(--color-surface)] px-4 md:px-6 py-4">
      <div class="max-w-2xl mx-auto flex gap-3">
        <input
          v-model="input"
          @keydown.enter.exact="send"
          :disabled="sending"
          placeholder="Ask about the simulation results..."
          class="flex-1 bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-4 py-2.5 text-sm text-[var(--input-text)] placeholder:text-[var(--input-placeholder)] focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent disabled:opacity-60 transition-[border-color,box-shadow]"
        />
        <button
          @click="send"
          :disabled="sending || !input.trim()"
          class="bg-[var(--btn-primary-bg)] hover:bg-[var(--btn-primary-bg-hover)] active:bg-[var(--btn-primary-bg-active)] disabled:opacity-50 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          {{ sending ? 'Sending...' : 'Send' }}
        </button>
      </div>
    </div>
  </div>
</template>
