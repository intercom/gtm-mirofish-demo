import client from './client'

export const simulationApi = {
  // --- Entities ---
  getEntities: (graphId, params) =>
    client.get(`/simulation/entities/${graphId}`, { params }),
  getEntity: (graphId, entityUuid) =>
    client.get(`/simulation/entities/${graphId}/${entityUuid}`),
  getEntitiesByType: (graphId, entityType, params) =>
    client.get(`/simulation/entities/${graphId}/by-type/${entityType}`, { params }),

  // --- Lifecycle ---
  create: (data) => client.post('/simulation/create', data),
  prepare: (data) => client.post('/simulation/prepare', data),
  prepareStatus: (data) => client.post('/simulation/prepare/status', data),
  start: (data) => client.post('/simulation/start', data),
  stop: (data) => client.post('/simulation/stop', data),

  // --- Status & info ---
  get: (simulationId) => client.get(`/simulation/${simulationId}`),
  list: (params) => client.get('/simulation/list', { params }),
  history: (params) => client.get('/simulation/history', { params }),
  getRunStatus: (simulationId) =>
    client.get(`/simulation/${simulationId}/run-status`),
  getRunStatusDetail: (simulationId) =>
    client.get(`/simulation/${simulationId}/run-status/detail`),

  // --- Profiles & config ---
  getProfiles: (simulationId) =>
    client.get(`/simulation/${simulationId}/profiles`),
  getProfilesRealtime: (simulationId) =>
    client.get(`/simulation/${simulationId}/profiles/realtime`),
  getConfig: (simulationId) =>
    client.get(`/simulation/${simulationId}/config`),
  getConfigRealtime: (simulationId) =>
    client.get(`/simulation/${simulationId}/config/realtime`),
  downloadConfig: (simulationId) =>
    client.get(`/simulation/${simulationId}/config/download`, { responseType: 'blob' }),
  downloadScript: (scriptName) =>
    client.get(`/simulation/script/${scriptName}/download`, { responseType: 'blob' }),
  generateProfiles: (data) =>
    client.post('/simulation/generate-profiles', data),

  // --- Results ---
  getActions: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/actions`, { params }),
  getTimeline: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/timeline`, { params }),
  getAgentStats: (simulationId) =>
    client.get(`/simulation/${simulationId}/agent-stats`),
  getPosts: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/posts`, { params }),
  getComments: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/comments`, { params }),

  // --- Interviews ---
  interview: (data) => client.post('/simulation/interview', data),
  interviewBatch: (data) => client.post('/simulation/interview/batch', data),
  interviewAll: (data) => client.post('/simulation/interview/all', data),
  interviewHistory: (data) => client.post('/simulation/interview/history', data),

  // --- Environment ---
  envStatus: (data) => client.post('/simulation/env-status', data),
  closeEnv: (data) => client.post('/simulation/close-env', data),

  // --- Relationships ---
  getRelationships: (simulationId) =>
    client.get(`/simulation/${simulationId}/relationships`),
  getAgentRelationships: (simulationId, agentId) =>
    client.get(`/simulation/${simulationId}/agents/${agentId}/relationships`),
  getAlliances: (simulationId) =>
    client.get(`/simulation/${simulationId}/alliances`),
  getConflicts: (simulationId) =>
    client.get(`/simulation/${simulationId}/conflicts`),
}
