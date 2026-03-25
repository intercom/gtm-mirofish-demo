import client from './client'

export const memoryApi = {
  search: (graphId, data) =>
    client.post(`/memory/${graphId}/search`, data),

  getAgents: (graphId) =>
    client.get(`/memory/${graphId}/agents`),

  getTopics: (graphId, params) =>
    client.get(`/memory/${graphId}/topics`, { params }),
}
