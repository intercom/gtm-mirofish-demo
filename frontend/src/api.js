/**
 * MiroFish API client — thin wrapper around fetch for backend communication.
 * All backend responses use the envelope: { success: bool, data: {...}, error?: string }
 */

import { API_BASE } from './api/client'

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const json = await res.json()
  if (!res.ok || json.success === false) {
    throw new Error(json.error || `Request failed: ${res.status}`)
  }
  return json
}

// ── GTM Scenarios ──

export function listScenarios() {
  return fetch(`${API_BASE}/gtm/scenarios`).then(r => r.json())
}

export function getScenario(id) {
  return fetch(`${API_BASE}/gtm/scenarios/${id}`).then(r => r.json())
}

// ── Graph ──

export function buildGraph(projectId, opts = {}) {
  return request(`${API_BASE}/graph/build`, {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId, ...opts }),
  })
}

export function getTask(taskId) {
  return request(`${API_BASE}/graph/task/${taskId}`)
}

export function generateOntology(formData) {
  return fetch(`${API_BASE}/graph/ontology/generate`, {
    method: 'POST',
    body: formData,
  }).then(r => r.json())
}

// ── Simulation ──

export function createSimulation(projectId, graphId, opts = {}) {
  return request(`${API_BASE}/simulation/create`, {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId, graph_id: graphId, ...opts }),
  })
}

export function prepareSimulation(simulationId, opts = {}) {
  return request(`${API_BASE}/simulation/prepare`, {
    method: 'POST',
    body: JSON.stringify({ simulation_id: simulationId, ...opts }),
  })
}

export function getPrepareStatus(taskId, simulationId) {
  const body = {}
  if (taskId) body.task_id = taskId
  if (simulationId) body.simulation_id = simulationId
  return request(`${API_BASE}/simulation/prepare/status`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function startSimulation(simulationId, platform = 'parallel') {
  return request(`${API_BASE}/simulation/start`, {
    method: 'POST',
    body: JSON.stringify({ simulation_id: simulationId, platform }),
  })
}

export function getRunStatus(simulationId) {
  return request(`${API_BASE}/simulation/${simulationId}/run-status`)
}

export function getSimulationActions(simulationId, limit = 20) {
  return request(`${API_BASE}/simulation/${simulationId}/actions?limit=${limit}`)
}

// ── Report ──

export function generateReport(simulationId) {
  return request(`${API_BASE}/report/generate`, {
    method: 'POST',
    body: JSON.stringify({ simulation_id: simulationId }),
  })
}

export function getReportGenerateStatus(taskId, simulationId) {
  return request(`${API_BASE}/report/generate/status`, {
    method: 'POST',
    body: JSON.stringify({ task_id: taskId, simulation_id: simulationId }),
  })
}

export function getReport(reportId) {
  return request(`${API_BASE}/report/${reportId}`)
}

export function getReportBySimulation(simulationId) {
  return request(`${API_BASE}/report/by-simulation/${simulationId}`)
}

export function getReportSections(reportId) {
  return request(`${API_BASE}/report/${reportId}/sections`)
}

// ── Chat ──

export function chatWithReport(simulationId, message, chatHistory = []) {
  return request(`${API_BASE}/report/chat`, {
    method: 'POST',
    body: JSON.stringify({
      simulation_id: simulationId,
      message,
      chat_history: chatHistory,
    }),
  })
}

// ── Insights ──

export function listInsights(category) {
  const params = category ? `?category=${category}` : ''
  return request(`${API_BASE}/insights${params}`)
}

export function refreshInsights() {
  return request(`${API_BASE}/insights/refresh`, { method: 'POST' })
}

export function pinInsight(insightId) {
  return request(`${API_BASE}/insights/${insightId}/pin`, { method: 'POST' })
}

export function dismissInsight(insightId) {
  return request(`${API_BASE}/insights/${insightId}/dismiss`, { method: 'POST' })
}

// ── Polling helper ──

export function poll(fn, interval = 3000) {
  let timer = null
  let stopped = false

  async function tick(onData) {
    if (stopped) return
    try {
      const result = await fn()
      onData(result)
    } catch (e) {
      onData(null, e)
    }
    if (!stopped) {
      timer = setTimeout(() => tick(onData), interval)
    }
  }

  return {
    start(onData) {
      stopped = false
      tick(onData)
    },
    stop() {
      stopped = true
      if (timer) clearTimeout(timer)
    },
  }
}
