/**
 * MiroFish API service layer.
 * Centralizes all backend communication with consistent error handling.
 */

import { API_BASE } from '../api/client'

function getCsrfToken() {
  const match = document.cookie.match(/(?:^|; )csrf_token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : null
}

function csrfHeaders(method) {
  if (method && method !== 'GET' && method !== 'HEAD') {
    const token = getCsrfToken()
    if (token) return { 'X-CSRFToken': token }
  }
  return {}
}

async function request(url, options = {}) {
  const res = await fetch(url, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...csrfHeaders(options.method),
      ...options.headers,
    },
    ...options,
  })
  const data = await res.json()
  if (!res.ok || data.success === false) {
    throw new Error(data.error || `Request failed: ${res.status}`)
  }
  return data
}

/**
 * Poll a task endpoint until it reaches a terminal state.
 * Calls onProgress with each intermediate response.
 * Returns the final response data.
 */
export async function pollTask(pollFn, { interval = 2000, timeout = 600000, onProgress } = {}) {
  const start = Date.now()
  while (Date.now() - start < timeout) {
    const data = await pollFn()
    const status = data.data?.status
    if (onProgress) onProgress(data.data)
    if (status === 'completed' || status === 'ready' || data.data?.already_prepared || data.data?.already_completed) {
      return data
    }
    if (status === 'failed') {
      throw new Error(data.data?.message || data.data?.error || 'Task failed')
    }
    await new Promise((r) => setTimeout(r, interval))
  }
  throw new Error('Task timed out')
}

// ── GTM Scenarios ──

export async function listScenarios() {
  return request(`${API_BASE}/gtm/scenarios`)
}

export async function getScenario(id) {
  return request(`${API_BASE}/gtm/scenarios/${id}`)
}

// ── Graph Building ──

export async function generateOntology(formData) {
  // multipart/form-data — don't set Content-Type, let browser set boundary
  const res = await fetch(`${API_BASE}/graph/ontology/generate`, {
    method: 'POST',
    credentials: 'include',
    headers: csrfHeaders('POST'),
    body: formData,
  })
  const data = await res.json()
  if (!res.ok || data.success === false) throw new Error(data.error || 'Ontology generation failed')
  return data
}

export async function buildGraph({ projectId, graphName, chunkSize, chunkOverlap }) {
  return request(`${API_BASE}/graph/build`, {
    method: 'POST',
    body: JSON.stringify({
      project_id: projectId,
      graph_name: graphName,
      chunk_size: chunkSize,
      chunk_overlap: chunkOverlap,
    }),
  })
}

export async function getGraphTask(taskId) {
  return request(`${API_BASE}/graph/task/${taskId}`)
}

export async function getGraphData(graphId) {
  return request(`${API_BASE}/graph/data/${graphId}`)
}

export async function getProject(projectId) {
  return request(`${API_BASE}/graph/project/${projectId}`)
}

// ── Simulation ──

export async function createSimulation({ projectId, graphId, enableTwitter = true, enableReddit = true }) {
  return request(`${API_BASE}/simulation/create`, {
    method: 'POST',
    body: JSON.stringify({
      project_id: projectId,
      graph_id: graphId,
      enable_twitter: enableTwitter,
      enable_reddit: enableReddit,
    }),
  })
}

export async function prepareSimulation({ simulationId, entityTypes, forceRegenerate = false }) {
  return request(`${API_BASE}/simulation/prepare`, {
    method: 'POST',
    body: JSON.stringify({
      simulation_id: simulationId,
      entity_types: entityTypes,
      force_regenerate: forceRegenerate,
    }),
  })
}

export async function getPrepareStatus({ taskId, simulationId }) {
  return request(`${API_BASE}/simulation/prepare/status`, {
    method: 'POST',
    body: JSON.stringify({ task_id: taskId, simulation_id: simulationId }),
  })
}

export async function startSimulation({ simulationId, platform = 'parallel' }) {
  return request(`${API_BASE}/simulation/start`, {
    method: 'POST',
    body: JSON.stringify({ simulation_id: simulationId, platform }),
  })
}

export async function getRunStatus(simulationId) {
  return request(`${API_BASE}/simulation/${simulationId}/run-status`)
}

export async function getSimulation(simulationId) {
  return request(`${API_BASE}/simulation/${simulationId}`)
}

export async function getSimulationActions(simulationId, { limit = 50, offset = 0 } = {}) {
  return request(`${API_BASE}/simulation/${simulationId}/actions?limit=${limit}&offset=${offset}`)
}

// ── Report ──

export async function generateReport({ simulationId }) {
  return request(`${API_BASE}/report/generate`, {
    method: 'POST',
    body: JSON.stringify({ simulation_id: simulationId }),
  })
}

export async function getReportGenerateStatus({ taskId, simulationId }) {
  return request(`${API_BASE}/report/generate/status`, {
    method: 'POST',
    body: JSON.stringify({ task_id: taskId, simulation_id: simulationId }),
  })
}

export async function getReport(reportId) {
  return request(`${API_BASE}/report/${reportId}`)
}

export async function getReportSections(reportId) {
  return request(`${API_BASE}/report/${reportId}/sections`)
}

export async function checkReportStatus(simulationId) {
  return request(`${API_BASE}/report/check/${simulationId}`)
}

// ── Chat ──

export async function chatWithReport({ simulationId, message, chatHistory = [] }) {
  return request(`${API_BASE}/report/chat`, {
    method: 'POST',
    body: JSON.stringify({
      simulation_id: simulationId,
      message,
      chat_history: chatHistory,
    }),
  })
}
