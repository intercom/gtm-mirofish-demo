import client from './client'

export const agentsApi = {
  list: () => client.get('/agents'),
  get: (id) => client.get(`/agents/${id}`),
  create: (data) => client.post('/agents', data),
  update: (id, data) => client.put(`/agents/${id}`, data),
  delete: (id) => client.delete(`/agents/${id}`),
  clone: (id) => client.post(`/agents/${id}/clone`),
  templates: () => client.get('/agents/templates'),
  generate: (data) => client.post('/agents/generate', data),
}
