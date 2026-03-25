import client from './client'

export const reportApi = {
  // --- Generation ---
  generate: (data) => client.post('/report/generate', data),
  generateStatus: (data) => client.post('/report/generate/status', data),

  // --- CRUD ---
  get: (reportId) => client.get(`/report/${reportId}`),
  getBySimulation: (simulationId) =>
    client.get(`/report/by-simulation/${simulationId}`),
  list: (params) => client.get('/report/list', { params }),
  delete: (reportId) => client.delete(`/report/${reportId}`),
  download: (reportId, format = 'md') =>
    client.get(`/report/${reportId}/download`, { params: { format }, responseType: 'blob' }),

  // --- Progress & sections ---
  getProgress: (reportId) => client.get(`/report/${reportId}/progress`),
  getSections: (reportId) => client.get(`/report/${reportId}/sections`),
  getSection: (reportId, sectionIndex) =>
    client.get(`/report/${reportId}/section/${sectionIndex}`),
  checkStatus: (simulationId) =>
    client.get(`/report/check/${simulationId}`),

  // --- Agent logs ---
  getAgentLog: (reportId, params) =>
    client.get(`/report/${reportId}/agent-log`, { params }),
  getAgentLogStream: (reportId) =>
    client.get(`/report/${reportId}/agent-log/stream`),
  getConsoleLog: (reportId, params) =>
    client.get(`/report/${reportId}/console-log`, { params }),
  getConsoleLogStream: (reportId) =>
    client.get(`/report/${reportId}/console-log/stream`),
}
