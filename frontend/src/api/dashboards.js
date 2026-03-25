import client from './client'

export const dashboardsApi = {
  list: () => client.get('/dashboards'),
  get: (id) => client.get(`/dashboards/${id}`),
  save: (config) =>
    config.id
      ? client.put(`/dashboards/${config.id}`, config)
      : client.post('/dashboards', config),
  delete: (id) => client.delete(`/dashboards/${id}`),
  duplicate: (id) => client.post(`/dashboards/${id}/duplicate`),
}
