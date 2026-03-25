<script setup>
import { ref, nextTick, computed, watch } from 'vue'
import { marked } from 'marked'
import { insightsApi } from '../../api/insights'
import { useToast } from '../../composables/useToast'

const props = defineProps({
  context: {
    type: Object,
    default: () => ({}),
  },
})

const toast = useToast()

const isOpen = ref(false)
const messages = ref([])
const input = ref('')
const sending = ref(false)
const messagesEnd = ref(null)

const suggestedQuestions = [
  { text: 'Why did churn increase last month?', icon: '📉' },
  { text: 'Which campaign has best ROI?', icon: '🎯' },
  { text: 'Show pipeline health summary', icon: '📊' },
  { text: 'Compare segment performance', icon: '👥' },
  { text: 'What should we prioritize next?', icon: '🚀' },
]

const chatHistory = computed(() =>
  messages.value
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map(({ role, content }) => ({ role, content })),
)

const hasMessages = computed(() => messages.value.length > 0)

function toggle() {
  isOpen.value = !isOpen.value
}

async function scrollToBottom() {
  await nextTick()
  messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
}

async function send(text) {
  const msg = (text || input.value).trim()
  if (!msg || sending.value) return

  input.value = ''
  messages.value.push({ role: 'user', content: msg })
  scrollToBottom()
  sending.value = true

  try {
    const { data: res } = await insightsApi.chat({
      message: msg,
      context: props.context,
      chat_history: chatHistory.value.slice(0, -1),
    })

    if (res.success) {
      messages.value.push({
        role: 'assistant',
        content: res.data.response,
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
    toast.error(`Analyst error: ${e.message}`)
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function clearChat() {
  messages.value = []
}

watch(isOpen, (open) => {
  if (open) nextTick(() => scrollToBottom())
})
</script>

<template>
  <!-- Floating chat bubble trigger -->
  <button
    @click="toggle"
    class="ai-analyst-bubble"
    :class="{ 'ai-analyst-bubble--open': isOpen }"
    aria-label="Open AI Analyst"
  >
    <svg v-if="!isOpen" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
    </svg>
    <svg v-else class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  </button>

  <!-- Chat panel -->
  <Transition name="analyst-panel">
    <div v-if="isOpen" class="ai-analyst-panel">
      <!-- Header -->
      <div class="ai-analyst-header">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-[#2068FF] flex items-center justify-center flex-shrink-0">
            <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12c0 1.74.46 3.37 1.26 4.78L2 22l5.22-1.26C8.63 21.54 10.26 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2z"/>
            </svg>
          </div>
          <div>
            <div class="text-sm font-semibold text-[var(--color-text)]">AI Analyst</div>
            <div class="text-[10px] text-[var(--color-text-muted)]">Ask about your GTM data</div>
          </div>
        </div>
        <button
          v-if="hasMessages"
          @click="clearChat"
          class="text-[10px] text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
        >
          Clear
        </button>
      </div>

      <!-- Messages area -->
      <div class="ai-analyst-messages">
        <!-- Suggested questions (empty state) -->
        <div v-if="!hasMessages && !sending" class="px-4 py-3">
          <p class="text-xs text-[var(--color-text-muted)] mb-3">Suggested questions:</p>
          <div class="space-y-1.5">
            <button
              v-for="q in suggestedQuestions"
              :key="q.text"
              @click="send(q.text)"
              class="ai-analyst-chip"
            >
              <span class="flex-shrink-0">{{ q.icon }}</span>
              <span>{{ q.text }}</span>
            </button>
          </div>
        </div>

        <!-- Message list -->
        <div v-else class="px-4 py-3 space-y-3">
          <div v-for="(msg, i) in messages" :key="i">
            <!-- User -->
            <div v-if="msg.role === 'user'" class="flex justify-end">
              <div class="ai-analyst-msg-user">{{ msg.content }}</div>
            </div>

            <!-- Assistant -->
            <div v-else-if="msg.role === 'assistant'" class="flex justify-start">
              <div class="ai-analyst-msg-assistant">
                <div
                  class="prose prose-sm max-w-none dark:prose-invert text-[13px] leading-relaxed"
                  v-html="marked.parse(msg.content || '')"
                />
                <div v-if="msg.sources?.length" class="mt-2 flex flex-wrap gap-1">
                  <span
                    v-for="(src, si) in msg.sources"
                    :key="si"
                    class="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium bg-[#2068FF]/10 text-[#2068FF]"
                  >
                    {{ typeof src === 'string' ? src : src.name || `Source ${si + 1}` }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Error -->
            <div v-else-if="msg.role === 'error'" class="flex justify-start">
              <div class="ai-analyst-msg-error">{{ msg.content }}</div>
            </div>
          </div>

          <!-- Typing indicator -->
          <div v-if="sending" class="flex justify-start">
            <div class="ai-analyst-msg-assistant">
              <div class="flex items-center gap-1">
                <span class="ai-analyst-dot" style="animation-delay: 0ms" />
                <span class="ai-analyst-dot" style="animation-delay: 150ms" />
                <span class="ai-analyst-dot" style="animation-delay: 300ms" />
              </div>
            </div>
          </div>

          <div ref="messagesEnd" />
        </div>
      </div>

      <!-- Input -->
      <div class="ai-analyst-input-area">
        <input
          v-model="input"
          @keydown.enter.exact="send()"
          :disabled="sending"
          placeholder="Ask about your data..."
          class="ai-analyst-input"
        />
        <button
          @click="send()"
          :disabled="sending || !input.trim()"
          class="ai-analyst-send"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.ai-analyst-bubble {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #2068FF;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: none;
  box-shadow: 0 4px 12px rgba(32, 104, 255, 0.4);
  transition: background 0.2s, transform 0.2s, box-shadow 0.2s;
}
.ai-analyst-bubble:hover {
  background: #1a5ae0;
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(32, 104, 255, 0.5);
}
.ai-analyst-bubble--open {
  background: #050505;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
.ai-analyst-bubble--open:hover {
  background: #1a1a1a;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

.ai-analyst-panel {
  position: fixed;
  bottom: 88px;
  right: 24px;
  z-index: 999;
  width: 380px;
  max-height: calc(100vh - 120px);
  border-radius: 16px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-analyst-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
  background: var(--color-bg, #fff);
}

.ai-analyst-messages {
  flex: 1;
  overflow-y: auto;
  min-height: 200px;
  max-height: 400px;
}

.ai-analyst-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--color-border, #e5e7eb);
  background: var(--color-surface, #fff);
  color: var(--color-text, #1a1a1a);
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.ai-analyst-chip:hover {
  border-color: #2068FF;
  background: rgba(32, 104, 255, 0.04);
}

.ai-analyst-msg-user {
  max-width: 80%;
  background: #2068FF;
  color: white;
  border-radius: 14px 14px 4px 14px;
  padding: 8px 12px;
  font-size: 13px;
  line-height: 1.4;
}

.ai-analyst-msg-assistant {
  max-width: 90%;
  background: var(--color-bg-alt, #f3f4f6);
  color: var(--color-text, #1a1a1a);
  border-radius: 14px 14px 14px 4px;
  padding: 8px 12px;
}

.ai-analyst-msg-error {
  max-width: 80%;
  background: var(--color-error-light, #fef2f2);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: var(--color-text, #1a1a1a);
  border-radius: 14px 14px 14px 4px;
  padding: 8px 12px;
  font-size: 12px;
}

.ai-analyst-input-area {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid var(--color-border, #e5e7eb);
  background: var(--color-bg, #fff);
}

.ai-analyst-input {
  flex: 1;
  background: var(--input-bg, #f9fafb);
  border: 1px solid var(--input-border, #d1d5db);
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--input-text, #1a1a1a);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.ai-analyst-input::placeholder {
  color: var(--input-placeholder, #9ca3af);
}
.ai-analyst-input:focus {
  border-color: #2068FF;
  box-shadow: 0 0 0 2px rgba(32, 104, 255, 0.15);
}
.ai-analyst-input:disabled {
  opacity: 0.6;
}

.ai-analyst-send {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: #2068FF;
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}
.ai-analyst-send:hover:not(:disabled) {
  background: #1a5ae0;
}
.ai-analyst-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ai-analyst-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-muted, #9ca3af);
  animation: analyst-bounce 1.2s infinite;
}

@keyframes analyst-bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-4px); }
}

/* Panel transition */
.analyst-panel-enter-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.analyst-panel-leave-active {
  transition: all 0.2s ease-in;
}
.analyst-panel-enter-from {
  opacity: 0;
  transform: translateY(12px) scale(0.96);
}
.analyst-panel-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}
</style>
