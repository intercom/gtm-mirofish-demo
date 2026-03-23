<script setup>
import { ref } from 'vue'
import EmptyState from '../components/ui/EmptyState.vue'
import { useToast } from '../composables/useToast'
import { useRoute } from 'vue-router'
import { chatWithReport } from '../services/api.js'

const props = defineProps({ taskId: String })
const toast = useToast()
const route = useRoute()

const simulationId = ref(route.query.simulationId || props.taskId)
const messages = ref([])
const input = ref('')
const sending = ref(false)

async function send() {
  if (!input.value.trim() || sending.value) return

  const text = input.value.trim()
  input.value = ''
  messages.value.push({ role: 'user', content: text })
  sending.value = true

  try {
    const chatHistory = messages.value
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .slice(0, -1) // exclude the message we just pushed

    const res = await chatWithReport({
      simulationId: simulationId.value,
      message: text,
      chatHistory,
    })

    messages.value.push({
      role: 'assistant',
      content: res.data?.response || 'No response received.',
    })
  } catch (e) {
    messages.value.push({ role: 'error', content: 'Something went wrong — check your connection and try again. (' + e.message + ')' })
    toast.error(`Chat error: ${e.message}`)
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-120px)]">
    <!-- Messages -->
    <div class="flex-1 overflow-y-auto px-4 md:px-6 py-6 md:py-8">
      <div class="max-w-2xl mx-auto space-y-3 md:space-y-4">
        <EmptyState
          v-if="messages.length === 0"
          icon="💬"
          title="Chat with the Simulation"
          description="Ask follow-up questions about the simulated world and its predictions."
        />

        <TransitionGroup name="slide-up">
          <div v-for="(msg, i) in messages" :key="i"
            class="rounded-lg px-3 md:px-4 py-2.5 md:py-3 text-sm"
            :class="{
              'bg-[rgba(32,104,255,0.08)] ml-6 md:ml-12': msg.role === 'user',
              'bg-[#f5f3ee] mr-6 md:mr-12': msg.role === 'assistant',
              'bg-[rgba(255,86,0,0.08)] border border-[rgba(255,86,0,0.2)] mr-6 md:mr-12': msg.role === 'error',
            }">
            <div class="text-xs font-medium mb-1"
              :class="{
                'text-[#2068FF]': msg.role === 'user',
                'text-[#ff5600]': msg.role === 'assistant' || msg.role === 'error',
              }">
              {{ msg.role === 'user' ? 'You' : msg.role === 'error' ? 'Error' : 'MiroFish' }}
            </div>
            {{ msg.content }}
          </div>
        </TransitionGroup>

        <div v-if="sending" class="bg-[#f5f3ee] rounded-lg px-3 md:px-4 py-2.5 md:py-3 mr-6 md:mr-12">
          <div class="text-xs font-medium text-[#ff5600] mb-1">MiroFish</div>
          <span class="text-sm text-[#888]">Thinking...</span>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="border-t border-black/10 px-4 md:px-6 py-3 md:py-4">
      <div class="max-w-2xl mx-auto flex gap-2 md:gap-3">
        <input
          v-model="input"
          @keydown.enter.exact="send"
          placeholder="Ask about the simulation results..."
          class="flex-1 border border-black/10 rounded-lg px-3 md:px-4 py-2.5 text-sm focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
        />
        <button
          @click="send"
          :disabled="sending || !input.trim()"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] disabled:opacity-50 text-white px-4 md:px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  </div>
</template>
