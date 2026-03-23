<script setup>
import { ref, nextTick } from 'vue'

const props = defineProps({ taskId: String })
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
    messages.value.push({ role: 'error', content: e.message || 'Something went wrong. Please try again.' })
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
        <div v-if="messages.length === 0" class="text-center py-20">
          <div class="text-5xl mb-4">💬</div>
          <h2 class="text-xl font-semibold text-[#050505] mb-2">Chat with the Simulation</h2>
          <p class="text-sm text-[#888]">Ask follow-up questions about the simulated world and its predictions.</p>
        </div>

        <div v-for="(msg, i) in messages" :key="i"
          class="rounded-lg px-4 py-3 text-sm"
          :class="{
            'bg-[rgba(32,104,255,0.08)] ml-12': msg.role === 'user',
            'bg-[#f5f3ee] mr-12': msg.role === 'assistant',
            'bg-[rgba(255,86,0,0.06)] border border-[#ff5600]/20 mr-12': msg.role === 'error',
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

        <div v-if="sending" class="bg-[#f5f3ee] rounded-lg px-4 py-3 mr-12">
          <div class="text-xs font-medium text-[#ff5600] mb-1">MiroFish</div>
          <span class="flex items-center gap-2 text-sm text-[#888]">
            <span class="w-3.5 h-3.5 border-[1.5px] border-[#ff5600] border-t-transparent rounded-full animate-spin"></span>
            Thinking...
          </span>
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
