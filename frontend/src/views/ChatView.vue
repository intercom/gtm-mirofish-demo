<script setup>
import { ref, nextTick, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'

const props = defineProps({ taskId: String })

const messages = ref([])
const input = ref('')
const sending = ref(false)
const messagesEnd = ref(null)
const simulationStatus = ref(null)
let statusPollTimer = null

const TOOL_LABELS = {
  insight_forge: 'Insight Forge',
  panorama_search: 'Panorama Search',
  quick_search: 'Quick Search',
  interview_agents: 'Interview Agents',
}

const statusLabel = computed(() => {
  if (!simulationStatus.value) return null
  const s = simulationStatus.value.runner_status
  if (s === 'running') return { text: 'Running', class: 'bg-green-100 text-green-700' }
  if (s === 'completed' || s === 'complete') return { text: 'Complete', class: 'bg-[rgba(32,104,255,0.1)] text-[#2068FF]' }
  if (s === 'paused') return { text: 'Paused', class: 'bg-yellow-100 text-yellow-700' }
  return { text: s, class: 'bg-gray-100 text-gray-600' }
})

const chatHistory = computed(() =>
  messages.value
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map((m) => ({ role: m.role, content: m.content }))
)

async function scrollToBottom() {
  await nextTick()
  messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
}

async function fetchSimulationStatus() {
  try {
    const { data } = await axios.get(`/api/simulation/${props.taskId}/run-status`)
    if (data.success) {
      simulationStatus.value = data.data
    }
  } catch {
    // Silently ignore — context indicator is non-critical
  }
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return

  input.value = ''
  messages.value.push({ role: 'user', content: text })
  scrollToBottom()

  sending.value = true
  try {
    const { data } = await axios.post('/api/report/chat', {
      simulation_id: props.taskId,
      message: text,
      chat_history: chatHistory.value.slice(0, -1),
    })

    if (data.success) {
      messages.value.push({
        role: 'assistant',
        content: data.data.response,
        toolCalls: data.data.tool_calls || [],
        sources: data.data.sources || [],
      })
    } else {
      messages.value.push({
        role: 'assistant',
        content: data.error || 'Something went wrong.',
        isError: true,
      })
    }
  } catch (e) {
    const msg = e.response?.data?.error || e.message
    messages.value.push({ role: 'assistant', content: `Error: ${msg}`, isError: true })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function formatToolName(name) {
  return TOOL_LABELS[name] || name
}

onMounted(() => {
  fetchSimulationStatus()
  statusPollTimer = setInterval(fetchSimulationStatus, 15000)
})

onUnmounted(() => {
  clearInterval(statusPollTimer)
})
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-120px)]">
    <!-- Context indicator -->
    <div class="border-b border-black/10 px-6 py-3 flex items-center justify-between bg-white">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-full bg-[#ff5600] flex items-center justify-center text-white text-sm font-bold">M</div>
        <div>
          <div class="text-sm font-semibold text-[#050505]">MiroFish Chat</div>
          <div class="text-xs text-[#888]">Simulation {{ taskId }}</div>
        </div>
      </div>
      <span
        v-if="statusLabel"
        class="px-3 py-1 rounded-full text-xs font-semibold"
        :class="statusLabel.class"
      >
        {{ statusLabel.text }}
      </span>
    </div>

    <!-- Messages -->
    <div class="flex-1 overflow-y-auto px-6 py-6">
      <div class="max-w-2xl mx-auto space-y-4">
        <!-- Empty state -->
        <div v-if="messages.length === 0 && !sending" class="text-center py-20">
          <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center">
            <svg class="w-8 h-8 text-[#2068FF]" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 0 1 .865-.501 48.2 48.2 0 0 0 3.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.4 48.4 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" />
            </svg>
          </div>
          <h2 class="text-xl font-semibold text-[#050505] mb-2">Chat with the Simulation</h2>
          <p class="text-sm text-[#888] max-w-sm mx-auto">
            Ask follow-up questions about the simulated world, agent behaviors, and predictions.
          </p>
        </div>

        <!-- Message bubbles -->
        <div v-for="(msg, i) in messages" :key="i">
          <!-- User message -->
          <div v-if="msg.role === 'user'" class="flex justify-end">
            <div class="bg-[#2068FF] text-white rounded-2xl rounded-br-md px-4 py-3 max-w-[80%] text-sm">
              {{ msg.content }}
            </div>
          </div>

          <!-- Assistant message -->
          <div v-else class="flex justify-start">
            <div class="max-w-[80%]">
              <!-- Tool calls (collapsible) -->
              <div v-if="msg.toolCalls?.length" class="mb-2 space-y-1">
                <details v-for="(tc, j) in msg.toolCalls" :key="j" class="group">
                  <summary class="flex items-center gap-2 cursor-pointer text-xs text-[#888] hover:text-[#555] py-1 select-none">
                    <svg class="w-3.5 h-3.5 text-[#A0F] shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M11.42 15.17 17.25 21A2.652 2.652 0 0 0 21 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 1 1-3.586-3.586l6.837-5.63m5.108-.233c.55-.164 1.163-.188 1.743-.14a4.5 4.5 0 0 0 4.486-6.336l-3.276 3.277a3.004 3.004 0 0 1-2.25-2.25l3.276-3.276a4.5 4.5 0 0 0-6.336 4.486c.049.58.025 1.193-.14 1.743" />
                    </svg>
                    <span>{{ formatToolName(tc.name) }}</span>
                    <svg class="w-3 h-3 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                    </svg>
                  </summary>
                  <div class="ml-5 mt-1 text-xs text-[#888] bg-[#f5f5f5] rounded-lg px-3 py-2 font-mono">
                    <div v-if="tc.parameters?.query">
                      <span class="text-[#555]">query:</span> {{ tc.parameters.query }}
                    </div>
                    <div v-for="(val, key) in tc.parameters" :key="key">
                      <template v-if="key !== 'query'">
                        <span class="text-[#555]">{{ key }}:</span> {{ val }}
                      </template>
                    </div>
                  </div>
                </details>
              </div>

              <div
                class="rounded-2xl rounded-bl-md px-4 py-3 text-sm whitespace-pre-wrap"
                :class="msg.isError ? 'bg-red-50 text-red-700' : 'bg-[#f5f5f5] text-[#050505]'"
              >
                <div class="text-xs font-medium text-[#ff5600] mb-1">MiroFish</div>
                {{ msg.content }}
              </div>
            </div>
          </div>
        </div>

        <!-- Thinking indicator -->
        <div v-if="sending" class="flex justify-start">
          <div class="bg-[#f5f5f5] rounded-2xl rounded-bl-md px-4 py-3 max-w-[80%]">
            <div class="text-xs font-medium text-[#ff5600] mb-1">MiroFish</div>
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-[#888] animate-bounce [animation-delay:0ms]"></span>
              <span class="w-2 h-2 rounded-full bg-[#888] animate-bounce [animation-delay:150ms]"></span>
              <span class="w-2 h-2 rounded-full bg-[#888] animate-bounce [animation-delay:300ms]"></span>
            </div>
          </div>
        </div>

        <div ref="messagesEnd" />
      </div>
    </div>

    <!-- Input -->
    <div class="border-t border-black/10 px-6 py-4 bg-white">
      <div class="max-w-2xl mx-auto flex gap-3">
        <input
          v-model="input"
          @keydown.enter.exact="send"
          :disabled="sending"
          placeholder="Ask about the simulation results..."
          class="flex-1 border border-black/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#2068FF] focus:border-transparent disabled:opacity-50"
        />
        <button
          @click="send"
          :disabled="sending || !input.trim()"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] disabled:opacity-40 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-colors flex items-center gap-2"
        >
          <span>Send</span>
          <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
