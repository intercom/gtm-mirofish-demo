<script setup>
import { ref, computed, onMounted } from 'vue'
import client from '../api/client'

const METHOD_COLORS = {
  GET: { bg: 'rgba(16,185,129,0.1)', text: '#10b981', border: 'rgba(16,185,129,0.3)' },
  POST: { bg: 'rgba(32,104,255,0.1)', text: '#2068FF', border: 'rgba(32,104,255,0.3)' },
  PUT: { bg: 'rgba(245,158,11,0.1)', text: '#f59e0b', border: 'rgba(245,158,11,0.3)' },
  PATCH: { bg: 'rgba(168,85,247,0.1)', text: '#a855f7', border: 'rgba(168,85,247,0.3)' },
  DELETE: { bg: 'rgba(239,68,68,0.1)', text: '#ef4444', border: 'rgba(239,68,68,0.3)' },
}

// ── Rich schema data for well-known endpoints ─────────────────────
// Used as both enrichments for auto-discovered routes AND fallback
// when the backend is unreachable. Paths use the simplified format
// (without /v1/) since the auto-discovered paths are normalized to match.
const KNOWN_ENDPOINTS = [
  { category: 'Core', method: 'GET', path: '/health', description: 'Basic health check', request: null, response: '{"status":"ok","service":"MiroFish Backend"}' },

  { category: 'GTM Scenarios', method: 'GET', path: '/api/gtm/scenarios', description: 'List all GTM scenario templates', request: null, response: '{"scenarios":[{"id":"...","name":"...","description":"...","category":"...","icon":"..."}]}' },
  { category: 'GTM Scenarios', method: 'GET', path: '/api/gtm/scenarios/:scenario_id', description: 'Get a scenario template with full configuration', request: null, response: '{"scenario":{...},"seed_data":{...}}' },
  { category: 'GTM Scenarios', method: 'GET', path: '/api/gtm/scenarios/:scenario_id/seed-text', description: 'Get seed text for a specific scenario', request: null, response: '{"seed_text":"..."}' },
  { category: 'GTM Scenarios', method: 'GET', path: '/api/gtm/seed-data/:data_type', description: 'Get seed data by type (personas, industries, etc.)', request: null, response: '{"data":[...]}' },
  { category: 'GTM Scenarios', method: 'POST', path: '/api/gtm/simulate', description: 'Start a unified GTM simulation from scenario config', request: [
    { name: 'scenario_id', type: 'string', required: true, desc: 'ID of the scenario template' },
    { name: 'seed_text', type: 'string', required: true, desc: 'Seed text for the simulation' },
    { name: 'agent_count', type: 'number', required: false, desc: 'Number of agents (default: 200)' },
    { name: 'duration_hours', type: 'number', required: false, desc: 'Simulation duration in hours' },
  ], response: '{"success":true,"data":{"project_id":"...","task_id":"..."}}' },

  { category: 'Knowledge Graph', method: 'GET', path: '/api/graph/project/list', description: 'List all projects', request: null, response: '{"success":true,"data":[...],"count":0}' },
  { category: 'Knowledge Graph', method: 'GET', path: '/api/graph/project/:project_id', description: 'Get project details', request: null, response: '{"success":true,"data":{...}}' },
  { category: 'Knowledge Graph', method: 'DELETE', path: '/api/graph/project/:project_id', description: 'Delete a project', request: null, response: '{"success":true,"message":"..."}' },
  { category: 'Knowledge Graph', method: 'POST', path: '/api/graph/project/:project_id/reset', description: 'Reset project state for graph rebuild', request: null, response: '{"success":true,"data":{...}}' },
  { category: 'Knowledge Graph', method: 'POST', path: '/api/graph/ontology/generate', description: 'Upload files and generate ontology definition (multipart/form-data)', request: [
    { name: 'files', type: 'file[]', required: true, desc: 'Documents to analyze (PDF/MD/TXT)' },
    { name: 'simulation_requirement', type: 'string', required: true, desc: 'Simulation requirement description' },
    { name: 'project_name', type: 'string', required: false, desc: 'Project name' },
  ], response: '{"success":true,"data":{"project_id":"...","ontology":{...}}}' },
  { category: 'Knowledge Graph', method: 'POST', path: '/api/graph/build', description: 'Build knowledge graph from project ontology (async)', request: [
    { name: 'project_id', type: 'string', required: true, desc: 'Project ID from ontology generation' },
    { name: 'graph_name', type: 'string', required: false, desc: 'Name for the graph' },
    { name: 'chunk_size', type: 'number', required: false, desc: 'Text chunk size (default: 500)' },
    { name: 'chunk_overlap', type: 'number', required: false, desc: 'Chunk overlap (default: 50)' },
  ], response: '{"success":true,"data":{"project_id":"...","task_id":"..."}}' },
  { category: 'Knowledge Graph', method: 'GET', path: '/api/graph/task/:task_id', description: 'Check async task status', request: null, response: '{"success":true,"data":{"task_id":"...","status":"...","progress":0}}' },
  { category: 'Knowledge Graph', method: 'GET', path: '/api/graph/tasks', description: 'List all tasks', request: null, response: '{"success":true,"data":[...],"count":0}' },
  { category: 'Knowledge Graph', method: 'GET', path: '/api/graph/data/:graph_id', description: 'Get graph nodes and edges', request: null, response: '{"success":true,"data":{...}}' },
  { category: 'Knowledge Graph', method: 'DELETE', path: '/api/graph/delete/:graph_id', description: 'Delete a Zep graph', request: null, response: '{"success":true,"message":"..."}' },

  { category: 'Simulation', method: 'GET', path: '/api/simulation/entities/:graph_id', description: 'Get all entities from a knowledge graph', request: null, response: '{"success":true,"data":[...]}' },
  { category: 'Simulation', method: 'POST', path: '/api/simulation/create', description: 'Create a new simulation from graph data', request: [
    { name: 'graph_id', type: 'string', required: false, desc: 'Knowledge graph ID' },
  ], response: '{"success":true,"data":{"simulation_id":"..."}}' },
  { category: 'Simulation', method: 'POST', path: '/api/simulation/prepare', description: 'Prepare simulation (generate profiles and config)', request: [
    { name: 'simulation_id', type: 'string', required: true, desc: 'Simulation ID' },
  ], response: '{"success":true,"data":{...}}' },
  { category: 'Simulation', method: 'POST', path: '/api/simulation/prepare/status', description: 'Check preparation status', request: [
    { name: 'simulation_id', type: 'string', required: true, desc: 'Simulation ID' },
  ], response: '{"success":true,"data":{"status":"...","progress":0}}' },
  { category: 'Simulation', method: 'POST', path: '/api/simulation/start', description: 'Start running a prepared simulation', request: [
    { name: 'simulation_id', type: 'string', required: true, desc: 'Simulation ID' },
  ], response: '{"success":true,"data":{...}}' },
  { category: 'Simulation', method: 'POST', path: '/api/simulation/stop', description: 'Stop a running simulation', request: [
    { name: 'simulation_id', type: 'string', required: true, desc: 'Simulation ID' },
  ], response: '{"success":true,"message":"..."}' },
  { category: 'Simulation', method: 'GET', path: '/api/simulation/:simulation_id', description: 'Get simulation details', request: null, response: '{"success":true,"data":{...}}' },
  { category: 'Simulation', method: 'GET', path: '/api/simulation/list', description: 'List all simulations', request: null, response: '{"success":true,"data":[...]}' },
  { category: 'Simulation', method: 'GET', path: '/api/simulation/history', description: 'Get simulation run history', request: null, response: '{"success":true,"data":[...]}' },
  { category: 'Simulation', method: 'GET', path: '/api/simulation/:simulation_id/run-status', description: 'Get real-time simulation run status', request: null, response: '{"success":true,"data":{"status":"...","progress":0}}' },
  { category: 'Simulation', method: 'GET', path: '/api/simulation/:simulation_id/profiles', description: 'Get agent profiles for a simulation', request: null, response: '{"success":true,"data":[...]}' },
  { category: 'Simulation', method: 'GET', path: '/api/simulation/:simulation_id/actions', description: 'Get simulation actions/posts', request: null, response: '{"success":true,"data":[...]}' },
  { category: 'Simulation', method: 'GET', path: '/api/simulation/:simulation_id/timeline', description: 'Get simulation timeline data', request: null, response: '{"success":true,"data":[...]}' },
  { category: 'Simulation', method: 'GET', path: '/api/simulation/:simulation_id/agent-stats', description: 'Get per-agent statistics', request: null, response: '{"success":true,"data":[...]}' },
  { category: 'Simulation', method: 'GET', path: '/api/simulation/:simulation_id/posts', description: 'Get simulation posts', request: null, response: '{"success":true,"data":[...]}' },
  { category: 'Simulation', method: 'GET', path: '/api/simulation/:simulation_id/comments', description: 'Get simulation comments', request: null, response: '{"success":true,"data":[...]}' },
  { category: 'Simulation', method: 'POST', path: '/api/simulation/interview', description: 'Interview a simulated agent', request: [
    { name: 'simulation_id', type: 'string', required: true, desc: 'Simulation ID' },
    { name: 'agent_id', type: 'string', required: true, desc: 'Agent ID to interview' },
    { name: 'question', type: 'string', required: true, desc: 'Interview question' },
  ], response: '{"success":true,"data":{"answer":"..."}}' },

  { category: 'Report', method: 'POST', path: '/api/report/generate', description: 'Generate a predictive report from simulation data', request: [
    { name: 'simulation_id', type: 'string', required: true, desc: 'Simulation ID' },
  ], response: '{"success":true,"data":{"report_id":"..."}}' },
  { category: 'Report', method: 'POST', path: '/api/report/generate/status', description: 'Check report generation progress', request: [
    { name: 'report_id', type: 'string', required: true, desc: 'Report ID' },
  ], response: '{"success":true,"data":{"status":"...","progress":0}}' },
  { category: 'Report', method: 'GET', path: '/api/report/:report_id', description: 'Get a generated report', request: null, response: '{"success":true,"data":{...}}' },
  { category: 'Report', method: 'GET', path: '/api/report/by-simulation/:simulation_id', description: 'Get report by simulation ID', request: null, response: '{"success":true,"data":{...}}' },
  { category: 'Report', method: 'GET', path: '/api/report/list', description: 'List all reports', request: null, response: '{"success":true,"data":[...]}' },
  { category: 'Report', method: 'GET', path: '/api/report/:report_id/progress', description: 'Get report generation progress', request: null, response: '{"success":true,"data":{"progress":0}}' },
  { category: 'Report', method: 'GET', path: '/api/report/:report_id/sections', description: 'Get report sections', request: null, response: '{"success":true,"data":[...]}' },
  { category: 'Report', method: 'DELETE', path: '/api/report/:report_id', description: 'Delete a report', request: null, response: '{"success":true,"message":"..."}' },

  { category: 'Report', method: 'POST', path: '/api/report/chat', description: 'Chat with the simulation world using report context', request: [
    { name: 'message', type: 'string', required: true, desc: 'User message (max 2000 chars)' },
    { name: 'simulation_id', type: 'string', required: false, desc: 'Simulation ID for context' },
    { name: 'report_id', type: 'string', required: false, desc: 'Report ID for context' },
  ], response: '{"success":true,"data":{"reply":"..."}}' },

  { category: 'Settings', method: 'POST', path: '/api/settings/test-llm', description: 'Test LLM provider connection', request: [
    { name: 'provider', type: 'string', required: true, desc: 'Provider: anthropic, openai, or gemini' },
    { name: 'apiKey', type: 'string', required: true, desc: 'API key to test' },
  ], response: '{"ok":true}' },
  { category: 'Settings', method: 'POST', path: '/api/settings/test-zep', description: 'Test Zep Cloud connection', request: [
    { name: 'apiKey', type: 'string', required: true, desc: 'Zep API key to test' },
  ], response: '{"ok":true}' },
  { category: 'Settings', method: 'GET', path: '/api/settings/auth-status', description: 'Get authentication configuration and current user', request: null, response: '{"authEnabled":false,"provider":null,"user":null}' },
]

// Build enrichment lookup — maps 'METHOD:/normalized/path' to { request, response }
const _enrichments = new Map()
for (const ep of KNOWN_ENDPOINTS) {
  _enrichments.set(`${ep.method}:${ep.path}`, { request: ep.request, response: ep.response })
}

function _normalizeKey(method, path) {
  return `${method}:${path.replace('/api/v1/', '/api/')}`
}

// ── State ──────────────────────────────────────────────────────────
const endpoints = ref([])
const fetchingEndpoints = ref(true)
const search = ref('')
const selectedEndpoint = ref(null)
const requestBody = ref('')
const responseData = ref(null)
const responseError = ref(null)
const trying = ref(false)
const pathParams = ref({})

// ── Computed ───────────────────────────────────────────────────────
const filteredEndpoints = computed(() => {
  const q = search.value.toLowerCase()
  if (!q) return endpoints.value
  return endpoints.value.filter(
    (e) =>
      e.path.toLowerCase().includes(q) ||
      e.description.toLowerCase().includes(q) ||
      e.method.toLowerCase().includes(q) ||
      e.category.toLowerCase().includes(q),
  )
})

const groupedEndpoints = computed(() => {
  const groups = {}
  for (const ep of filteredEndpoints.value) {
    if (!groups[ep.category]) groups[ep.category] = []
    groups[ep.category].push(ep)
  }
  return groups
})

// ── Fetch & enrich ────────────────────────────────────────────────
async function fetchEndpoints() {
  fetchingEndpoints.value = true
  try {
    const res = await client.get('/docs/routes')
    const routes = res.data.data || []
    endpoints.value = routes.map((r) => {
      const key = _normalizeKey(r.method, r.path)
      const known = _enrichments.get(key)
      return { ...r, request: known?.request || null, response: known?.response || null }
    })
  } catch {
    endpoints.value = KNOWN_ENDPOINTS
  } finally {
    fetchingEndpoints.value = false
    if (endpoints.value.length && !selectedEndpoint.value) {
      selectEndpoint(endpoints.value[0])
    }
  }
}

// ── Interaction helpers ───────────────────────────────────────────
function selectEndpoint(ep) {
  selectedEndpoint.value = ep
  responseData.value = null
  responseError.value = null
  pathParams.value = {}

  if (ep.request) {
    const body = {}
    for (const field of ep.request) {
      if (field.type === 'file[]') continue
      body[field.name] = field.type === 'number' ? 0 : ''
    }
    requestBody.value = JSON.stringify(body, null, 2)
  } else {
    requestBody.value = ''
  }
}

function getPathParamNames(path) {
  const matches = path.match(/:([a-zA-Z_]+)/g)
  return matches ? matches.map((m) => m.slice(1)) : []
}

function resolvedPath(ep) {
  let path = ep.path
  for (const [key, val] of Object.entries(pathParams.value)) {
    if (val) path = path.replace(`:${key}`, val)
  }
  return path
}

function formatJson(str) {
  try {
    return JSON.stringify(JSON.parse(str), null, 2)
  } catch {
    return str
  }
}

function getMethodColor(method) {
  return METHOD_COLORS[method] || METHOD_COLORS.GET
}

// ── Try It ────────────────────────────────────────────────────────
async function tryIt() {
  const ep = selectedEndpoint.value
  trying.value = true
  responseData.value = null
  responseError.value = null

  try {
    const path = resolvedPath(ep)

    // Compute the correct client path based on the route's prefix.
    // The axios client has baseURL /api/v1, so:
    //   /api/v1/... → strip /api/v1, use client directly
    //   /api/...    → use /../ to go up one level from /v1 to /api
    //   /health etc → raw fetch (not covered by Vite proxy in dev)
    let clientPath
    if (path.startsWith('/api/v1/')) {
      clientPath = path.slice(7)
    } else if (path.startsWith('/api/')) {
      clientPath = '/../' + path.slice(5)
    } else {
      const res = await fetch(path)
      responseData.value = await res.json()
      return
    }

    let res
    switch (ep.method) {
      case 'GET':
        res = await client.get(clientPath)
        break
      case 'POST': {
        const body = requestBody.value ? JSON.parse(requestBody.value) : {}
        res = await client.post(clientPath, body)
        break
      }
      case 'PUT': {
        const body = requestBody.value ? JSON.parse(requestBody.value) : {}
        res = await client.put(clientPath, body)
        break
      }
      case 'PATCH': {
        const body = requestBody.value ? JSON.parse(requestBody.value) : {}
        res = await client.patch(clientPath, body)
        break
      }
      case 'DELETE':
        res = await client.delete(clientPath)
        break
    }
    responseData.value = res.data
  } catch (err) {
    responseError.value = err.data || err.message || String(err)
  } finally {
    trying.value = false
  }
}

onMounted(fetchEndpoints)
</script>

<template>
  <div class="flex h-[calc(100vh-56px)] overflow-hidden">
    <!-- Sidebar -->
    <aside class="hidden md:block w-72 shrink-0 border-r border-[var(--color-border)] bg-[var(--color-surface)] overflow-y-auto">
      <div class="p-3 border-b border-[var(--color-border)]">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">API Reference</span>
          <span v-if="!fetchingEndpoints" class="text-[10px] tabular-nums text-[var(--color-text-muted)]">{{ endpoints.length }} endpoints</span>
        </div>
        <input
          v-model="search"
          type="text"
          placeholder="Search endpoints or categories..."
          class="w-full border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text)] rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#2068FF] focus:outline-none"
        />
      </div>

      <!-- Loading state -->
      <div v-if="fetchingEndpoints" class="flex items-center justify-center py-12">
        <svg class="animate-spin h-5 w-5 text-[var(--color-text-muted)]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>

      <!-- Endpoint navigation -->
      <nav v-else class="p-2">
        <template v-for="(items, category) in groupedEndpoints" :key="category">
          <div class="px-2 pt-3 pb-1 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] flex items-center justify-between">
            <span>{{ category }}</span>
            <span class="text-[10px] font-normal tabular-nums">{{ items.length }}</span>
          </div>
          <button
            v-for="ep in items"
            :key="ep.method + ep.path"
            @click="selectEndpoint(ep)"
            class="w-full text-left flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors cursor-pointer"
            :class="selectedEndpoint === ep
              ? 'bg-[rgba(32,104,255,0.1)] text-[var(--color-text)]'
              : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-primary-light)]'"
          >
            <span
              class="text-[10px] font-bold tracking-wide shrink-0 px-1.5 py-0.5 rounded"
              :style="{
                backgroundColor: getMethodColor(ep.method).bg,
                color: getMethodColor(ep.method).text,
              }"
            >{{ ep.method }}</span>
            <span class="truncate text-xs font-mono">{{ ep.path }}</span>
          </button>
        </template>

        <div v-if="Object.keys(groupedEndpoints).length === 0" class="px-3 py-6 text-center text-sm text-[var(--color-text-muted)]">
          No endpoints match your search.
        </div>
      </nav>
    </aside>

    <!-- Main content -->
    <main class="flex-1 overflow-y-auto p-6 md:p-8">
      <div v-if="selectedEndpoint" class="max-w-3xl">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-1">
          <span
            class="text-xs font-bold tracking-wide px-2 py-1 rounded border"
            :style="{
              backgroundColor: getMethodColor(selectedEndpoint.method).bg,
              color: getMethodColor(selectedEndpoint.method).text,
              borderColor: getMethodColor(selectedEndpoint.method).border,
            }"
          >{{ selectedEndpoint.method }}</span>
          <code class="text-base font-mono text-[var(--color-text)]">{{ selectedEndpoint.path }}</code>
        </div>
        <p class="text-sm text-[var(--color-text-secondary)] mb-1">{{ selectedEndpoint.description }}</p>
        <p class="text-xs text-[var(--color-text-muted)] mb-6">
          <span class="inline-block px-1.5 py-0.5 rounded bg-[var(--color-surface)] border border-[var(--color-border)]">{{ selectedEndpoint.category }}</span>
        </p>

        <!-- Path Parameters -->
        <section v-if="getPathParamNames(selectedEndpoint.path).length" class="mb-6">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Path Parameters</h3>
          <div class="space-y-2">
            <div v-for="param in getPathParamNames(selectedEndpoint.path)" :key="param" class="flex items-center gap-2">
              <label class="text-sm font-mono text-[var(--color-text)] w-40 shrink-0">:{{ param }}</label>
              <input
                v-model="pathParams[param]"
                type="text"
                :placeholder="param"
                class="flex-1 border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text)] rounded-lg px-3 py-1.5 text-sm font-mono focus:ring-2 focus:ring-[#2068FF] focus:outline-none"
              />
            </div>
          </div>
        </section>

        <!-- Request Body Schema -->
        <section v-if="selectedEndpoint.request" class="mb-6">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Request Body</h3>
          <div class="border border-[var(--color-border)] rounded-lg overflow-hidden">
            <table class="w-full text-sm">
              <thead>
                <tr class="bg-[var(--color-surface)]">
                  <th class="text-left px-3 py-2 text-xs font-semibold text-[var(--color-text-muted)]">Field</th>
                  <th class="text-left px-3 py-2 text-xs font-semibold text-[var(--color-text-muted)]">Type</th>
                  <th class="text-left px-3 py-2 text-xs font-semibold text-[var(--color-text-muted)]">Required</th>
                  <th class="text-left px-3 py-2 text-xs font-semibold text-[var(--color-text-muted)]">Description</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="field in selectedEndpoint.request" :key="field.name" class="border-t border-[var(--color-border)]">
                  <td class="px-3 py-2 font-mono text-[var(--color-text)]">{{ field.name }}</td>
                  <td class="px-3 py-2 text-[var(--color-text-secondary)]">{{ field.type }}</td>
                  <td class="px-3 py-2">
                    <span v-if="field.required" class="text-[#2068FF] font-medium">Yes</span>
                    <span v-else class="text-[var(--color-text-muted)]">No</span>
                  </td>
                  <td class="px-3 py-2 text-[var(--color-text-secondary)]">{{ field.desc }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <h3 class="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mt-4 mb-2">Request JSON</h3>
          <textarea
            v-model="requestBody"
            rows="6"
            class="w-full border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text)] rounded-lg px-4 py-3 text-sm font-mono focus:ring-2 focus:ring-[#2068FF] focus:outline-none resize-y"
            spellcheck="false"
          ></textarea>
        </section>

        <!-- Example Response -->
        <section v-if="selectedEndpoint.response" class="mb-6">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Example Response</h3>
          <pre class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3 text-sm font-mono text-[var(--color-text-secondary)] overflow-x-auto whitespace-pre-wrap">{{ formatJson(selectedEndpoint.response) }}</pre>
        </section>

        <!-- Try It -->
        <section class="mb-8">
          <button
            @click="tryIt"
            :disabled="trying"
            class="px-5 py-2 text-sm font-medium text-white bg-[#2068FF] rounded-lg hover:bg-[#1a57d6] transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {{ trying ? 'Sending...' : 'Try It' }}
          </button>

          <div v-if="responseData !== null" class="mt-4">
            <h3 class="text-xs font-semibold uppercase tracking-wider text-[#10b981] mb-2">Response</h3>
            <pre class="bg-[#0a1628] border border-[rgba(16,185,129,0.2)] rounded-lg px-4 py-3 text-sm font-mono text-[#d1fae5] overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto">{{ JSON.stringify(responseData, null, 2) }}</pre>
          </div>

          <div v-if="responseError !== null" class="mt-4">
            <h3 class="text-xs font-semibold uppercase tracking-wider text-[#ef4444] mb-2">Error</h3>
            <pre class="bg-[#1c0a0a] border border-[rgba(239,68,68,0.2)] rounded-lg px-4 py-3 text-sm font-mono text-[#fecaca] overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto">{{ typeof responseError === 'string' ? responseError : JSON.stringify(responseError, null, 2) }}</pre>
          </div>
        </section>
      </div>

      <!-- Empty state when no endpoint selected -->
      <div v-else-if="!fetchingEndpoints" class="flex flex-col items-center justify-center h-full text-[var(--color-text-muted)] gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p class="text-sm">Select an endpoint from the sidebar</p>
      </div>
    </main>
  </div>
</template>
