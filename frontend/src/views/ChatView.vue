<script setup>
import { ref, nextTick } from 'vue'
import { chatWithReport } from '../api.js'

const props = defineProps({ simulationId: String })
const messages = ref([])
const input = ref('')
const sending = ref(false)
const messagesContainer = ref(null)

async function send() {
  if (!input.value.trim() || sending.value) return

  const text = input.value.trim()
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  sending.value = true
  scrollToBottom()

  try {
    const chatHistory = messages.value
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .slice(0, -1) // exclude current message since it's sent as `message`
      .map(m => ({ role: m.role, content: m.content }))

    const result = await chatWithReport(props.simulationId, text, chatHistory)
    const response = result.data?.response || 'No response received.'
    messages.value.push({ role: 'assistant', content: response })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: 'Error: ' + e.message })
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-120px)]">
    <!-- Messages -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto px-6 py-8">
      <div class="max-w-2xl mx-auto space-y-4">
        <div v-if="messages.length === 0" class="text-center py-20">
          <div class="text-5xl mb-4">💬</div>
          <h2 class="text-xl font-semibold text-[#050505] mb-2">Chat with the Simulation</h2>
          <p class="text-sm text-[#888]">Ask follow-up questions about the simulated world and its predictions.</p>
        </div>

        <div v-for="(msg, i) in messages" :key="i"
          class="rounded-lg px-4 py-3 text-sm"
          :class="msg.role === 'user'
            ? 'bg-[rgba(32,104,255,0.08)] ml-12'
            : 'bg-[#f5f5f5] mr-12'">
          <div class="text-xs font-medium mb-1"
            :class="msg.role === 'user' ? 'text-[#2068FF]' : 'text-[#ff5600]'">
            {{ msg.role === 'user' ? 'You' : 'MiroFish' }}
          </div>
          <div class="whitespace-pre-wrap">{{ msg.content }}</div>
        </div>

        <div v-if="sending" class="bg-[#f5f5f5] rounded-lg px-4 py-3 mr-12">
          <div class="text-xs font-medium text-[#ff5600] mb-1">MiroFish</div>
          <span class="text-sm text-[#888]">Thinking...</span>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="border-t border-black/10 px-6 py-4">
      <div class="max-w-2xl mx-auto flex gap-3">
        <input
          v-model="input"
          @keydown.enter.exact="send"
          placeholder="Ask about the simulation results..."
          class="flex-1 border border-black/10 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
        />
        <button
          @click="send"
          :disabled="sending || !input.trim()"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] disabled:opacity-50 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  </div>
</template>
