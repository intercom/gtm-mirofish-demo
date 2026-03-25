import client from './client'

export const reportBuilderApi = {
  // --- Templates ---
  listTemplates: () => client.get('/report-builder/templates'),
  getTemplate: (id) => client.get(`/report-builder/templates/${id}`),
  saveTemplate: (data) => client.post('/report-builder/templates', data),
  updateTemplate: (id, data) => client.put(`/report-builder/templates/${id}`, data),
  deleteTemplate: (id) => client.delete(`/report-builder/templates/${id}`),

  // --- Reports ---
  generate: (data) => client.post('/report-builder/generate', data),
  listReports: (params) => client.get('/report-builder/reports', { params }),
  getReport: (id) => client.get(`/report-builder/reports/${id}`),
}
