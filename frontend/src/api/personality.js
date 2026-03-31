import client from './client'

export const personalityApi = {
  // Agents & snapshots
  listAgents: (simulationId) =>
    client.get(`/personality/${simulationId}/agents`),

  getSnapshot: (simulationId, agentId, params) =>
    client.get(`/personality/${simulationId}/agents/${agentId}`, { params }),

  getTrajectory: (simulationId, agentId) =>
    client.get(`/personality/${simulationId}/agents/${agentId}/trajectory`),

  // Mutations
  updatePersonality: (simulationId, data) =>
    client.post(`/personality/${simulationId}/update`, data),

  initializeAgent: (simulationId, data) =>
    client.post(`/personality/${simulationId}/initialize`, data),

  // Reference
  listOutcomes: () =>
    client.get('/personality/outcomes'),
}
