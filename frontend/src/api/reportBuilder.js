import client from './client'

const BASE = '/report-builder'

export const reportBuilderApi = {
  // ── Templates ───────────────────────────────────────────
  listTemplates: () => client.get(`${BASE}/templates`),
  getTemplate: (id) => client.get(`${BASE}/templates/${id}`),
  createTemplate: (data) => client.post(`${BASE}/templates`, data),
  updateTemplate: (id, data) => client.put(`${BASE}/templates/${id}`, data),
  deleteTemplate: (id) => client.delete(`${BASE}/templates/${id}`),

  // ── Generated reports ───────────────────────────────────
  generate: (data) => client.post(`${BASE}/generate`, data),
  listReports: () => client.get(`${BASE}/reports`),
  getReport: (id) => client.get(`${BASE}/reports/${id}`),
  deleteReport: (id) => client.delete(`${BASE}/reports/${id}`),
}
