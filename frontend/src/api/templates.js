import client from './client'

export const templatesApi = {
  list: (params) => client.get('/templates', { params }),
  get: (id) => client.get(`/templates/${id}`),
  create: (data) => client.post('/templates', data),
  update: (id, data) => client.put(`/templates/${id}`, data),
  remove: (id) => client.delete(`/templates/${id}`),
  use: (id) => client.post(`/templates/${id}/use`),
  rate: (id, rating) => client.post(`/templates/${id}/rate`, { rating }),
  categories: () => client.get('/templates/categories'),
}
