import client from './client'

const BASE = '/dashboards'

export const dashboardsApi = {
  list: () => client.get(BASE),
  get: (id) => client.get(`${BASE}/${id}`),
  save: (config) =>
    config.id
      ? client.put(`${BASE}/${config.id}`, config)
      : client.post(BASE, config),
  delete: (id) => client.delete(`${BASE}/${id}`),
  duplicate: (id) => client.post(`${BASE}/${id}/duplicate`),
  widgetData: (widgets) => client.post(`${BASE}/widget-data`, { widgets }),
}
