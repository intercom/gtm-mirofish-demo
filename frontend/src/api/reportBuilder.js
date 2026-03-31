import client from './client'

const BASE = '/report-builder'

export const reportBuilderApi = {
  // --- Templates ---
  listTemplates: () => client.get(`${BASE}/templates`),
  getTemplate: (id) => client.get(`${BASE}/templates/${id}`),
  saveTemplate: (data) => client.post(`${BASE}/templates`, data),
  updateTemplate: (id, data) => client.put(`${BASE}/templates/${id}`, data),
  deleteTemplate: (id) => client.delete(`${BASE}/templates/${id}`),

  // --- Reports ---
  generate: (data) => client.post(`${BASE}/generate`, data),
  listReports: (params) => client.get(`${BASE}/reports`, { params }),
  getReport: (id) => client.get(`${BASE}/reports/${id}`),
  deleteReport: (id) => client.delete(`${BASE}/reports/${id}`),
}
