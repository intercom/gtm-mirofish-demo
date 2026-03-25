import client from './client'

export const reportApi = {
  // --- Generation ---
  generate: (data) => client.post('/report/generate', data),
  generateStatus: (data) => client.post('/report/generate/status', data),
  getReportTypes: () => client.get('/report/types'),

  // --- CRUD ---
  get: (reportId) => client.get(`/report/${reportId}`),
  getBySimulation: (simulationId) =>
    client.get(`/report/by-simulation/${simulationId}`),
  list: (params) => client.get('/report/list', { params }),
  delete: (reportId) => client.delete(`/report/${reportId}`),
  download: (reportId) =>
    client.get(`/report/${reportId}/download`, { responseType: 'blob' }),

  // --- Status & progress ---
  getStatus: (reportId) => client.get(`/report/${reportId}/status`),
  getProgress: (reportId) => client.get(`/report/${reportId}/progress`),
  getSections: (reportId) => client.get(`/report/${reportId}/sections`),
  getSection: (reportId, sectionIndex) =>
    client.get(`/report/${reportId}/section/${sectionIndex}`),
  checkStatus: (simulationId) =>
    client.get(`/report/check/${simulationId}`),

  // --- Transparency & logs ---
  getToolCalls: (reportId) => client.get(`/report/${reportId}/tool-calls`),
  getAgentLog: (reportId, params) =>
    client.get(`/report/${reportId}/agent-log`, { params }),
  getAgentLogStream: (reportId) =>
    client.get(`/report/${reportId}/agent-log/stream`),
  getConsoleLog: (reportId, params) =>
    client.get(`/report/${reportId}/console-log`, { params }),
  getConsoleLogStream: (reportId) =>
    client.get(`/report/${reportId}/console-log/stream`),

  // --- Data sources ---
  listDataSources: () => client.get('/report/data-sources'),
  previewDataSource: (sourceType, params) =>
    client.get(`/report/data-sources/${sourceType}/preview`, { params }),
}
