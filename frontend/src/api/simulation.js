import client from './client'
import { API_BASE } from './client'

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
  pause: (simulationId) =>
    client.post(`/simulation/${simulationId}/pause`),
  resume: (simulationId) =>
    client.post(`/simulation/${simulationId}/resume`),

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

  // --- OASIS round & metrics ---
  getRound: (simulationId, roundNum) =>
    client.get(`/simulation/${simulationId}/round/${roundNum}`),
  getMetrics: (simulationId) =>
    client.get(`/simulation/${simulationId}/metrics`),

  // --- Results ---
  getActions: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/actions`, { params }),
  getTimeline: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/timeline`, { params }),
  getKnowledgeTimeline: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/knowledge-timeline`, { params }),
  getAgentStats: (simulationId) =>
    client.get(`/simulation/${simulationId}/agent-stats`),
  getAdjacencyMatrix: (simulationId) =>
    client.get(`/simulation/${simulationId}/adjacency-matrix`),
  getSentiment: (simulationId) =>
    client.get(`/simulation/${simulationId}/sentiment`),
  getAgentSentimentTimeline: (simulationId) =>
    client.get(`/simulation/${simulationId}/agent-sentiment-timeline`),
  getAgentNetwork: (simulationId) =>
    client.get(`/simulation/${simulationId}/agent-network`),
  getReplay: (simulationId) =>
    client.get(`/simulation/${simulationId}/replay`),
  getPosts: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/posts`, { params }),
  getComments: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/comments`, { params }),

  // --- Anomalies ---
  getAnomalies: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/anomalies`, { params }),

  // --- Sentiment dynamics ---
  getSentimentDynamics: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/sentiment-dynamics`, { params }),
  getSentimentPrompts: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/sentiment-dynamics/prompt`, { params }),

  // --- Relationships ---
  getRelationships: (simulationId) =>
    client.get(`/simulation/${simulationId}/relationships`),

  // --- Agent Journeys ---
  getAgentJourneys: (simulationId) =>
    client.get(`/simulation/${simulationId}/agent-journeys`),

  // --- Interviews ---
  interview: (data) => client.post('/simulation/interview', data),
  interviewBatch: (data) => client.post('/simulation/interview/batch', data),
  interviewAll: (data) => client.post('/simulation/interview/all', data),
  interviewHistory: (data) => client.post('/simulation/interview/history', data),

  // --- Snapshots ---
  snapshotCompare: (simulationId, roundA, roundB) =>
    client.get(`/simulation/${simulationId}/snapshot/compare`, {
      params: { round_a: roundA, round_b: roundB },
    }),

  // --- Influence ---
  getInfluence: (simulationId) =>
    client.get(`/simulation/${simulationId}/influence`),

  // --- Branches ---
  getBranchPoints: (simulationId) =>
    client.get(`/simulation/${simulationId}/branch-points`),

  // --- Environment ---
  envStatus: (data) => client.post('/simulation/env-status', data),
  closeEnv: (data) => client.post('/simulation/close-env', data),

  // --- Branching ---
  createBranch: (simulationId, data) =>
    client.post(`/simulation/${simulationId}/branch`, data),
  getBranches: (simulationId) =>
    client.get(`/simulation/${simulationId}/branches`),
  getBranchTree: (simulationId) =>
    client.get(`/simulation/${simulationId}/branch-tree`),
  compareBranches: (ids) =>
    client.get('/simulation/compare-branches', { params: { ids: ids.join(',') } }),
  deleteBranch: (simulationId, params) =>
    client.delete(`/simulation/${simulationId}/branch`, { params }),

  // --- Predictions ---
  getPredictions: (simulationId) =>
    client.get(`/simulation/${simulationId}/predictions`),
  getPredictionAccuracy: (simulationId) =>
    client.get(`/simulation/${simulationId}/predictions/accuracy`),

  // --- Personality ---
  getPersonalityEvolution: (simulationId, params) =>
    client.get(`/simulation/${simulationId}/personality`, { params }),

  // --- Consensus ---
  getConsensus: (simulationId) =>
    client.get(`/simulation/${simulationId}/consensus`),

  // --- Counterfactual analysis ---
  analyzeCounterfactual: (simulationId, data) =>
    client.post(`/simulation/${simulationId}/counterfactual`, data),

  // --- Coalitions ---
  getCoalitions: (simulationId) =>
    client.get(`/simulation/${simulationId}/coalitions`),
  getCoalitionEvolution: (simulationId) =>
    client.get(`/simulation/${simulationId}/coalitions/evolution`),
  getPolarization: (simulationId) =>
    client.get(`/simulation/${simulationId}/coalitions/polarization`),
  getSwingAgents: (simulationId) =>
    client.get(`/simulation/${simulationId}/coalitions/swing-agents`),

  // --- Relationship tracker ---
  getAgentRelationships: (simulationId, agentId) =>
    client.get(`/simulation/${simulationId}/agents/${agentId}/relationships`),
  getAlliances: (simulationId) =>
    client.get(`/simulation/${simulationId}/alliances`),
  getConflicts: (simulationId) =>
    client.get(`/simulation/${simulationId}/conflicts`),

  // --- SSE stream ---
  getProgressStreamUrl: (simulationId, interval = 2) =>
    `${API_BASE}/simulation/${simulationId}/progress/stream?interval=${interval}`,

  // --- Anomaly explanation ---
  getAnomalyExplanation: (simulationId, anomalyId) =>
    client.get(`/simulation/${simulationId}/anomalies/${anomalyId}/explanation`),
}
