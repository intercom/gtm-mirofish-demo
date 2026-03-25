import client from './client'

export const agentsApi = {
  list: () => client.get('/agents'),
  get: (agentId) => client.get(`/agents/${agentId}`),
  create: (data) => client.post('/agents', data),
  update: (agentId, data) => client.put(`/agents/${agentId}`, data),
  delete: (agentId) => client.delete(`/agents/${agentId}`),
  clone: (agentId) => client.post(`/agents/${agentId}/clone`),
  templates: () => client.get('/agents/templates'),
  generate: (description) => client.post('/agents/generate', { description }),
}
