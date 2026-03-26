import client from './client'

export const agentsApi = {
  list: () => client.get('/v1/agents'),
  get: (id) => client.get(`/v1/agents/${id}`),
  create: (data) => client.post('/v1/agents', data),
  update: (id, data) => client.put(`/v1/agents/${id}`, data),
  delete: (id) => client.delete(`/v1/agents/${id}`),
  clone: (id) => client.post(`/v1/agents/${id}/clone`),
  templates: () => client.get('/v1/agents/templates'),
  generate: (data) => client.post('/v1/agents/generate', data),
  previewResponse: (data) => client.post('/v1/agents/preview-response', data),
}
