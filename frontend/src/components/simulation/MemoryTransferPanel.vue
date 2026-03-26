<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMemoryTransfer } from '../../composables/useMemoryTransfer'
import { useMemoryTransferStore } from '../../stores/memoryTransfer'
import { useSimulationStore } from '../../stores/simulation'

const props = defineProps({
  simulationId: { type: String, default: null },
})

const memoryStore = useMemoryTransferStore()
const simStore = useSimulationStore()
const {
  exporting,
  importing,
  transferring,
  exportMemory,
  importMemory,
  transferMemory,
  loadBundles,
  loadDemoBundles,
  deleteBundle,
} = useMemoryTransfer()

const activeTab = ref('export')
const selectedAgent = ref(null)
const filterType = ref('all')
const targetSimId = ref('')
const targetAgentId = ref(null)
const selectedBundleForImport = ref(null)
const showBundleDetail = ref(false)
const detailBundle = ref(null)

const filterOptions = [
  { value: 'all', label: 'All Memory' },
  { value: 'decisions_only', label: 'Decisions Only' },
  { value: 'relationships_only', label: 'Relationships Only' },
  { value: 'facts_only', label: 'Facts Only' },
]

const tabs = [
  { key: 'export', label: 'Export' },
  { key: 'import', label: 'Import' },
  { key: 'transfer', label: 'Transfer' },
  { key: 'bundles', label: 'Bundles' },
]

const availableAgents = computed(() => {
  const runs = simStore.sessionRuns
  if (!runs.length) {
    return [
      { id: 0, name: 'Sarah Chen, VP Support @ Acme SaaS' },
      { id: 1, name: 'James Wright, CX Director @ Retail Plus' },
      { id: 2, name: 'Robert Williams, IT Director @ EduSpark' },
      { id: 3, name: 'Michael Chang, Head of Ops @ FinEdge' },
      { id: 4, name: 'Anika Sharma, Head of Support Engineering @ DevStack' },
    ]
  }
  const personas = runs[runs.length - 1]?.personas || []
  return personas.length
    ? personas.map((p, i) => ({ id: i, name: p }))
    : [{ id: 0, name: 'Agent 0' }, { id: 1, name: 'Agent 1' }, { id: 2, name: 'Agent 2' }]
})

const currentSimId = computed(() => props.simulationId || simStore.simulationId || 'demo')

const bundlesByAgent = computed(() => {
  const map = {}
  for (const b of memoryStore.bundles) {
    const key = b.agent_name || `Agent ${b.agent_id}`
    if (!map[key]) map[key] = []
    map[key].push(b)
  }
  return map
})

onMounted(async () => {
  if (currentSimId.value && currentSimId.value !== 'demo') {
    await loadBundles(currentSimId.value)
  } else {
    await loadDemoBundles()
  }
})

async function handleExport() {
  if (selectedAgent.value === null) return
  await exportMemory(currentSimId.value, selectedAgent.value, filterType.value)
}

async function handleImport() {
  if (targetAgentId.value === null || !selectedBundleForImport.value) return
  const bundle = memoryStore.bundles.find(b => b.bundle_id === selectedBundleForImport.value)
  if (!bundle) return
  const simId = targetSimId.value || currentSimId.value
  await importMemory(simId, targetAgentId.value, bundle)
}

async function handleTransfer() {
  if (selectedAgent.value === null || !targetSimId.value) return
  const toAgent = targetAgentId.value ?? selectedAgent.value
  await transferMemory(selectedAgent.value, currentSimId.value, targetSimId.value, filterType.value)
}

async function handleDelete(bundleId) {
  await deleteBundle(currentSimId.value, bundleId)
}

function viewBundle(bundle) {
  detailBundle.value = bundle
  showBundleDetail.value = true
}

function memorySectionCount(bundle) {
  const mem = bundle.memory || {}
  return Object.keys(mem).length
}
</script>

<template>
  <div class="flex flex-col gap-4 p-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-base font-semibold text-[var(--color-text)]">Memory Transfer</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
          Export, import, and transfer agent memory across simulations
        </p>
      </div>
      <span
        class="text-xs font-medium px-2 py-0.5 rounded-full"
        :class="memoryStore.bundleCount > 0
          ? 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]'
          : 'bg-gray-100 text-gray-500'"
      >
        {{ memoryStore.bundleCount }} bundle{{ memoryStore.bundleCount !== 1 ? 's' : '' }}
      </span>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 p-0.5 bg-gray-100 rounded-lg">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="flex-1 text-xs font-medium py-1.5 px-2 rounded-md transition-all"
        :class="activeTab === tab.key
          ? 'bg-white text-[var(--color-primary)] shadow-sm'
          : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Error banner -->
    <div
      v-if="memoryStore.error"
      class="text-xs text-[var(--color-error)] bg-[var(--color-error-light)] rounded-lg px-3 py-2"
    >
      {{ memoryStore.error }}
    </div>

    <!-- Export tab -->
    <div v-if="activeTab === 'export'" class="flex flex-col gap-3">
      <label class="text-xs font-medium text-[var(--color-text)]">Agent</label>
      <select
        v-model="selectedAgent"
        class="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent outline-none"
      >
        <option :value="null" disabled>Select agent...</option>
        <option v-for="agent in availableAgents" :key="agent.id" :value="agent.id">
          {{ agent.name }}
        </option>
      </select>

      <label class="text-xs font-medium text-[var(--color-text)]">Filter</label>
      <select
        v-model="filterType"
        class="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent outline-none"
      >
        <option v-for="opt in filterOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <button
        class="w-full text-sm font-medium py-2 px-4 rounded-lg transition-all disabled:opacity-40"
        :class="exporting
          ? 'bg-gray-200 text-gray-500'
          : 'bg-[var(--color-primary)] text-white hover:bg-[#1a5ae0]'"
        :disabled="selectedAgent === null || exporting"
        @click="handleExport"
      >
        {{ exporting ? 'Exporting...' : 'Export Memory' }}
      </button>

      <!-- Last export result -->
      <div
        v-if="memoryStore.lastExport"
        class="bg-[rgba(32,104,255,0.05)] border border-[rgba(32,104,255,0.15)] rounded-lg p-3"
      >
        <p class="text-xs font-medium text-[var(--color-primary)]">Exported successfully</p>
        <p class="text-xs text-[var(--color-text-muted)] mt-1">
          Bundle: {{ memoryStore.lastExport.bundle_id?.slice(0, 8) }}...
          &middot; {{ memoryStore.lastExport.agent_name }}
          &middot; {{ memorySectionCount(memoryStore.lastExport) }} sections
        </p>
      </div>
    </div>

    <!-- Import tab -->
    <div v-if="activeTab === 'import'" class="flex flex-col gap-3">
      <label class="text-xs font-medium text-[var(--color-text)]">Target Simulation ID</label>
      <input
        v-model="targetSimId"
        type="text"
        :placeholder="currentSimId"
        class="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent outline-none"
      />

      <label class="text-xs font-medium text-[var(--color-text)]">Target Agent</label>
      <select
        v-model="targetAgentId"
        class="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent outline-none"
      >
        <option :value="null" disabled>Select agent...</option>
        <option v-for="agent in availableAgents" :key="agent.id" :value="agent.id">
          {{ agent.name }}
        </option>
      </select>

      <label class="text-xs font-medium text-[var(--color-text)]">Source Bundle</label>
      <select
        v-model="selectedBundleForImport"
        class="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent outline-none"
      >
        <option :value="null" disabled>Select bundle...</option>
        <option v-for="b in memoryStore.bundles" :key="b.bundle_id" :value="b.bundle_id">
          {{ b.agent_name }} &middot; {{ b.filter_type }} &middot; {{ b.bundle_id?.slice(0, 8) }}
        </option>
      </select>

      <button
        class="w-full text-sm font-medium py-2 px-4 rounded-lg transition-all disabled:opacity-40"
        :class="importing
          ? 'bg-gray-200 text-gray-500'
          : 'bg-[var(--color-primary)] text-white hover:bg-[#1a5ae0]'"
        :disabled="targetAgentId === null || !selectedBundleForImport || importing"
        @click="handleImport"
      >
        {{ importing ? 'Importing...' : 'Import Memory' }}
      </button>

      <div
        v-if="memoryStore.lastImport"
        class="bg-[rgba(16,185,129,0.05)] border border-[rgba(16,185,129,0.15)] rounded-lg p-3"
      >
        <p class="text-xs font-medium text-emerald-600">Imported successfully</p>
        <p class="text-xs text-[var(--color-text-muted)] mt-1">
          Import: {{ memoryStore.lastImport.import_id?.slice(0, 8) }}...
          &middot; {{ memoryStore.lastImport.memory_sections?.join(', ') }}
        </p>
      </div>
    </div>

    <!-- Transfer tab -->
    <div v-if="activeTab === 'transfer'" class="flex flex-col gap-3">
      <label class="text-xs font-medium text-[var(--color-text)]">Agent</label>
      <select
        v-model="selectedAgent"
        class="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent outline-none"
      >
        <option :value="null" disabled>Select agent...</option>
        <option v-for="agent in availableAgents" :key="agent.id" :value="agent.id">
          {{ agent.name }}
        </option>
      </select>

      <label class="text-xs font-medium text-[var(--color-text)]">Target Simulation ID</label>
      <input
        v-model="targetSimId"
        type="text"
        placeholder="Target simulation ID"
        class="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent outline-none"
      />

      <label class="text-xs font-medium text-[var(--color-text)]">Filter</label>
      <select
        v-model="filterType"
        class="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent outline-none"
      >
        <option v-for="opt in filterOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <button
        class="w-full text-sm font-medium py-2 px-4 rounded-lg transition-all disabled:opacity-40"
        :class="transferring
          ? 'bg-gray-200 text-gray-500'
          : 'bg-[#ff5600] text-white hover:bg-[#e64d00]'"
        :disabled="selectedAgent === null || !targetSimId || transferring"
        @click="handleTransfer"
      >
        {{ transferring ? 'Transferring...' : 'Transfer Memory' }}
      </button>

      <p class="text-xs text-[var(--color-text-muted)]">
        Exports memory from current simulation and imports it into the target in one step.
      </p>
    </div>

    <!-- Bundles tab -->
    <div v-if="activeTab === 'bundles'" class="flex flex-col gap-3">
      <div v-if="memoryStore.loading" class="text-xs text-[var(--color-text-muted)] text-center py-4">
        Loading bundles...
      </div>

      <div v-else-if="memoryStore.bundles.length === 0" class="text-center py-6">
        <p class="text-sm text-[var(--color-text-muted)]">No memory bundles yet</p>
        <p class="text-xs text-[var(--color-text-muted)] mt-1">
          Export an agent's memory to create a bundle
        </p>
      </div>

      <template v-else>
        <div
          v-for="(agentBundles, agentName) in bundlesByAgent"
          :key="agentName"
          class="border border-gray-200 rounded-lg overflow-hidden"
        >
          <div class="bg-gray-50 px-3 py-2 border-b border-gray-200">
            <span class="text-xs font-semibold text-[var(--color-text)]">{{ agentName }}</span>
            <span class="text-xs text-[var(--color-text-muted)] ml-1">
              ({{ agentBundles.length }})
            </span>
          </div>
          <div class="divide-y divide-gray-100">
            <div
              v-for="bundle in agentBundles"
              :key="bundle.bundle_id"
              class="flex items-center justify-between px-3 py-2 hover:bg-gray-50 transition-colors"
            >
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5">
                  <span
                    class="text-[10px] font-medium px-1.5 py-0.5 rounded"
                    :class="bundle.is_import
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]'"
                  >
                    {{ bundle.is_import ? 'Imported' : 'Exported' }}
                  </span>
                  <span class="text-[10px] text-[var(--color-text-muted)]">
                    {{ bundle.filter_type }}
                  </span>
                </div>
                <p class="text-xs text-[var(--color-text-muted)] mt-0.5 truncate">
                  {{ bundle.bundle_id?.slice(0, 12) }}...
                  &middot; {{ bundle.memory_sections?.join(', ') || 'unknown' }}
                </p>
              </div>
              <div class="flex items-center gap-1 ml-2">
                <button
                  class="text-xs text-[var(--color-primary)] hover:underline"
                  @click="viewBundle(bundle)"
                >
                  View
                </button>
                <button
                  class="text-xs text-[var(--color-error)] hover:underline"
                  @click="handleDelete(bundle.bundle_id)"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Bundle detail modal -->
    <div
      v-if="showBundleDetail && detailBundle"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      @click.self="showBundleDetail = false"
    >
      <div class="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col">
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <h4 class="text-sm font-semibold text-[var(--color-text)]">Bundle Detail</h4>
          <button
            class="text-gray-400 hover:text-gray-600 text-lg leading-none"
            @click="showBundleDetail = false"
          >&times;</button>
        </div>

        <div class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
          <!-- Metadata -->
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span class="text-[var(--color-text-muted)]">Agent</span>
              <p class="font-medium text-[var(--color-text)]">{{ detailBundle.agent_name }}</p>
            </div>
            <div>
              <span class="text-[var(--color-text-muted)]">Filter</span>
              <p class="font-medium text-[var(--color-text)]">{{ detailBundle.filter_type }}</p>
            </div>
            <div>
              <span class="text-[var(--color-text-muted)]">Source Simulation</span>
              <p class="font-medium text-[var(--color-text)] truncate">{{ detailBundle.source_simulation_id }}</p>
            </div>
            <div>
              <span class="text-[var(--color-text-muted)]">Created</span>
              <p class="font-medium text-[var(--color-text)]">{{ detailBundle.created_at?.slice(0, 19) }}</p>
            </div>
          </div>

          <!-- Memory sections -->
          <template v-if="detailBundle.memory">
            <!-- Facts -->
            <div v-if="detailBundle.memory.facts?.length" class="border border-gray-200 rounded-lg p-3">
              <h5 class="text-xs font-semibold text-[var(--color-text)] mb-2">
                Facts ({{ detailBundle.memory.facts.length }})
              </h5>
              <div
                v-for="(fact, i) in detailBundle.memory.facts.slice(0, 5)"
                :key="i"
                class="flex items-start gap-2 text-xs mb-1.5"
              >
                <span class="text-[var(--color-primary)] mt-0.5 shrink-0">&#9679;</span>
                <span class="text-[var(--color-text)]">{{ fact.content }}</span>
                <span class="text-[var(--color-text-muted)] shrink-0 ml-auto">
                  {{ Math.round(fact.confidence * 100) }}%
                </span>
              </div>
            </div>

            <!-- Decisions -->
            <div v-if="detailBundle.memory.decisions?.length" class="border border-gray-200 rounded-lg p-3">
              <h5 class="text-xs font-semibold text-[var(--color-text)] mb-2">
                Decisions ({{ detailBundle.memory.decisions.length }})
              </h5>
              <div
                v-for="(decision, i) in detailBundle.memory.decisions.slice(0, 5)"
                :key="i"
                class="text-xs mb-1.5"
              >
                <span class="text-[var(--color-text-muted)]">R{{ decision.round }}</span>
                <span class="text-[#ff5600] font-medium ml-1">{{ decision.action_type }}</span>
                <p class="text-[var(--color-text)] mt-0.5">{{ decision.content }}</p>
              </div>
            </div>

            <!-- Relationships -->
            <div v-if="detailBundle.memory.relationships?.length" class="border border-gray-200 rounded-lg p-3">
              <h5 class="text-xs font-semibold text-[var(--color-text)] mb-2">
                Relationships ({{ detailBundle.memory.relationships.length }})
              </h5>
              <div
                v-for="(rel, i) in detailBundle.memory.relationships.slice(0, 5)"
                :key="i"
                class="flex items-center justify-between text-xs mb-1"
              >
                <span class="text-[var(--color-text)]">{{ rel.entity }}</span>
                <div class="flex items-center gap-2">
                  <div class="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-[var(--color-primary)] rounded-full transition-all"
                      :style="{ width: `${rel.strength * 100}%` }"
                    />
                  </div>
                  <span class="text-[var(--color-text-muted)] w-8 text-right">
                    {{ rel.interactions }}x
                  </span>
                </div>
              </div>
            </div>

            <!-- Actions summary -->
            <div v-if="detailBundle.memory.actions_summary" class="border border-gray-200 rounded-lg p-3">
              <h5 class="text-xs font-semibold text-[var(--color-text)] mb-2">Actions Summary</h5>
              <p class="text-xs text-[var(--color-text-muted)]">
                Total: {{ detailBundle.memory.actions_summary.total }}
              </p>
              <div class="flex flex-wrap gap-1.5 mt-1">
                <span
                  v-for="(count, type) in detailBundle.memory.actions_summary.by_type"
                  :key="type"
                  class="text-[10px] bg-gray-100 text-[var(--color-text-muted)] px-1.5 py-0.5 rounded"
                >
                  {{ type }}: {{ count }}
                </span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
