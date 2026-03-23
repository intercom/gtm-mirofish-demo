<script setup>
import { ref } from 'vue'
import { useToastStore } from '../stores/toast.js'
import EmptyState from '../components/ui/EmptyState.vue'

const props = defineProps({ taskId: String })
const toast = useToastStore()

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
    // TODO: Call /api/chat with message
    messages.value.push({
      role: 'assistant',
      content: 'Chat integration pending — connect to MiroFish backend /api/chat endpoint.',
    })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: 'Sorry, something went wrong. Please try again.' })
    toast.error('Failed to send message: ' + e.message)
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-120px)]">
    <!-- Messages -->
    <div class="flex-1 overflow-y-auto px-6 py-8">
      <div class="max-w-2xl mx-auto space-y-4">
        <EmptyState
          v-if="messages.length === 0"
          icon="💬"
          title="Chat with the Simulation"
          description="Ask follow-up questions about the simulated world and its predictions."
        />

        <div v-for="(msg, i) in messages" :key="i"
          class="rounded-lg px-4 py-3 text-sm"
          :class="msg.role === 'user'
            ? 'bg-[rgba(32,104,255,0.08)] ml-12'
            : 'bg-[#f5f5f5] mr-12'">
          <div class="text-xs font-medium mb-1"
            :class="msg.role === 'user' ? 'text-[#2068FF]' : 'text-[#ff5600]'">
            {{ msg.role === 'user' ? 'You' : 'MiroFish' }}
          </div>
          {{ msg.content }}
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
