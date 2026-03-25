import client from './client'

export const personalityApi = {
  // Agents & snapshots
  listAgents: (simulationId) =>
    client.get(`/v1/personality/${simulationId}/agents`),

  getSnapshot: (simulationId, agentId, params) =>
    client.get(`/v1/personality/${simulationId}/agents/${agentId}`, { params }),

  getTrajectory: (simulationId, agentId) =>
    client.get(`/v1/personality/${simulationId}/agents/${agentId}/trajectory`),

  // Mutations
  updatePersonality: (simulationId, data) =>
    client.post(`/v1/personality/${simulationId}/update`, data),

  initializeAgent: (simulationId, data) =>
    client.post(`/v1/personality/${simulationId}/initialize`, data),

  // Reference
  listOutcomes: () =>
    client.get('/v1/personality/outcomes'),
}
