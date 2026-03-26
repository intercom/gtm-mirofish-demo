import client from './client'

const PREFIX = '/v1/memory'

export const memoryApi = {
  search: (graphId, data) =>
    client.post(`/memory/${graphId}/search`, data),

  getAgents: (graphId) =>
    client.get(`/memory/${graphId}/agents`),

  getTopics: (graphId, params) =>
    client.get(`/memory/${graphId}/topics`, { params }),

  getConfig: () => client.get(`${PREFIX}/config`),
  saveConfig: (data) => client.post(`${PREFIX}/config`, data),
  getStats: (params) => client.get(`${PREFIX}/stats`, { params }),
  testConnection: (data) => client.post(`${PREFIX}/test-connection`, data),
}
