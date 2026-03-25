import client from './client'

export const agentsApi = {
  create: (formData) => client.post('/v1/agents', formData),
  list: () => client.get('/v1/agents'),
  get: (id) => client.get(`/v1/agents/${id}`),
  delete: (id) => client.delete(`/v1/agents/${id}`),
  previewResponse: (formData) => client.post('/v1/agents/preview-response', formData),
}
