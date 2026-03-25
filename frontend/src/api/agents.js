import client from './client'

export const agentsApi = {
  list: () => client.get('/agents'),
  get: (id) => client.get(`/agents/${id}`),
  create: (data) => client.post('/agents', data),
  update: (id, data) => client.put(`/agents/${id}`, data),
  remove: (id) => client.delete(`/agents/${id}`),
  clone: (id) => client.post(`/agents/${id}/clone`),
  templates: () => client.get('/agents/templates'),
}
