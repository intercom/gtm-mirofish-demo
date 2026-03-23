import client from './client'

// ── Entities ────────────────────────────────────

export function getEntities(graphId, params) {
  return client.get(`/simulation/entities/${graphId}`, { params })
}

export function getEntityDetail(graphId, entityUuid) {
  return client.get(`/simulation/entities/${graphId}/${entityUuid}`)
}

export function getEntitiesByType(graphId, entityType) {
  return client.get(`/simulation/entities/${graphId}/by-type/${entityType}`)
}

// ── Simulation Lifecycle ────────────────────────

export function createSimulation(data) {
  return client.post('/simulation/create', data)
}

export function prepareSimulation(data) {
  return client.post('/simulation/prepare', data)
}

export function getPrepareStatus(data) {
  return client.post('/simulation/prepare/status', data)
}

export function startSimulation(data) {
  return client.post('/simulation/start', data)
}

export function stopSimulation(data) {
  return client.post('/simulation/stop', data)
}

export function generateProfiles(data) {
  return client.post('/simulation/generate-profiles', data)
}

// ── Simulation Data ─────────────────────────────

export function getSimulation(simulationId) {
  return client.get(`/simulation/${simulationId}`)
}

export function listSimulations(params) {
  return client.get('/simulation/list', { params })
}

export function getHistory(params) {
  return client.get('/simulation/history', { params })
}

// ── Profiles & Config ───────────────────────────

export function getProfiles(simulationId) {
  return client.get(`/simulation/${simulationId}/profiles`)
}

export function getRealtimeProfiles(simulationId) {
  return client.get(`/simulation/${simulationId}/profiles/realtime`)
}

export function getConfig(simulationId) {
  return client.get(`/simulation/${simulationId}/config`)
}

export function getRealtimeConfig(simulationId) {
  return client.get(`/simulation/${simulationId}/config/realtime`)
}

export function downloadConfig(simulationId) {
  return client.get(`/simulation/${simulationId}/config/download`, {
    responseType: 'blob',
  })
}

export function downloadScript(scriptName) {
  return client.get(`/simulation/script/${scriptName}/download`, {
    responseType: 'blob',
  })
}

// ── Run Status & Results ────────────────────────

export function getRunStatus(simulationId) {
  return client.get(`/simulation/${simulationId}/run-status`)
}

export function getRunStatusDetail(simulationId) {
  return client.get(`/simulation/${simulationId}/run-status/detail`)
}

export function getActions(simulationId, params) {
  return client.get(`/simulation/${simulationId}/actions`, { params })
}

export function getTimeline(simulationId, params) {
  return client.get(`/simulation/${simulationId}/timeline`, { params })
}

export function getAgentStats(simulationId) {
  return client.get(`/simulation/${simulationId}/agent-stats`)
}

export function getPosts(simulationId, params) {
  return client.get(`/simulation/${simulationId}/posts`, { params })
}

export function getComments(simulationId, params) {
  return client.get(`/simulation/${simulationId}/comments`, { params })
}

// ── Environment ─────────────────────────────────

export function getEnvStatus(data) {
  return client.post('/simulation/env-status', data)
}

export function closeEnv(data) {
  return client.post('/simulation/close-env', data)
}
