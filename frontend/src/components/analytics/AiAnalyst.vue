<script setup>
import { ref, nextTick } from 'vue'

const isOpen = ref(false)
const message = ref('')
const messages = ref([
  { role: 'assistant', content: 'Hi! I can help you understand your analytics data. Ask me about cohort trends, attribution models, or segment performance.' },
])
const responding = ref(false)

const demoResponses = [
  'Based on the cohort data, Q1 2025 shows the strongest retention curve — 78% of users are still active at month 3, compared to 71% in Q4 2024.',
  'The time-decay attribution model suggests LinkedIn campaigns are undervalued by last-touch attribution. Consider reallocating 15-20% of budget from direct paid search.',
  'Enterprise segment NRR of 142% is driven primarily by seat expansion in months 4-6. The pattern suggests a "land and expand" motion is working well.',
  'SMB churn is concentrated in the first 30 days. The onboarding completion rate for churned accounts is only 34% vs 82% for retained accounts.',
  'Looking at cross-segment trends, the mid-market segment has the best LTV:CAC ratio at 4.8x, making it the most efficient acquisition target.',
]

function toggle() {
  isOpen.value = !isOpen.value
}

async function send() {
  const text = message.value.trim()
  if (!text || responding.value) return

  messages.value.push({ role: 'user', content: text })
  message.value = ''
  responding.value = true

  await nextTick()
  scrollToBottom()

  await new Promise(r => setTimeout(r, 800 + Math.random() * 600))

  const idx = (messages.value.length - 1) % demoResponses.length
  messages.value.push({ role: 'assistant', content: demoResponses[idx] })
  responding.value = false

  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  const el = document.getElementById('ai-analyst-messages')
  if (el) el.scrollTop = el.scrollHeight
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}
</script>

<template>
  <div class="fixed bottom-5 right-5 z-50">
    <!-- Chat panel -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95 translate-y-2"
      enter-to-class="opacity-100 scale-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100 translate-y-0"
      leave-to-class="opacity-0 scale-95 translate-y-2"
    >
      <div
        v-if="isOpen"
        class="absolute bottom-16 right-0 w-80 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl shadow-lg overflow-hidden"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)] bg-[var(--color-tint)]">
          <div class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span class="text-sm font-semibold text-[var(--color-text)]">AI Analyst</span>
          </div>
          <button @click="toggle" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Messages -->
        <div id="ai-analyst-messages" class="h-64 overflow-y-auto p-3 space-y-3">
          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="flex"
            :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
          >
            <div
              class="max-w-[85%] rounded-lg px-3 py-2 text-xs leading-relaxed"
              :class="msg.role === 'user'
                ? 'bg-[#2068FF] text-white'
                : 'bg-[var(--color-tint)] text-[var(--color-text)]'"
            >
              {{ msg.content }}
            </div>
          </div>
          <div v-if="responding" class="flex justify-start">
            <div class="bg-[var(--color-tint)] rounded-lg px-3 py-2">
              <span class="typing-dots text-[var(--color-text-muted)]">
                <span></span><span></span><span></span>
              </span>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="border-t border-[var(--color-border)] p-3">
          <div class="flex gap-2">
            <input
              v-model="message"
              @keydown="handleKeydown"
              type="text"
              placeholder="Ask about your data..."
              class="flex-1 text-xs px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
              :disabled="responding"
            />
            <button
              @click="send"
              :disabled="!message.trim() || responding"
              class="px-3 py-2 rounded-lg bg-[#2068FF] text-white text-xs font-medium hover:bg-[#1a5ae0] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Floating button -->
    <button
      @click="toggle"
      class="w-12 h-12 rounded-full bg-[#2068FF] text-white shadow-lg hover:bg-[#1a5ae0] hover:shadow-xl transition-all flex items-center justify-center"
      :class="{ 'ring-2 ring-[#2068FF]/30': isOpen }"
      title="AI Analyst"
    >
      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
      </svg>
    </button>
  </div>
</template>

<style scoped>
.typing-dots {
  display: inline-flex;
  gap: 3px;
  align-items: center;
  height: 16px;
}
.typing-dots span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background-color: currentColor;
  animation: dot-bounce 1.4s ease-in-out infinite;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot-bounce {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}
</style>
