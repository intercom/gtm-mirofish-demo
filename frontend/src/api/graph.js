import client from './client'

export const graphApi = {
  // --- Projects ---
  getProject: (projectId) => client.get(`/graph/project/${projectId}`),
  listProjects: (params) => client.get('/graph/project/list', { params }),
  deleteProject: (projectId) => client.delete(`/graph/project/${projectId}`),
  resetProject: (projectId) => client.post(`/graph/project/${projectId}/reset`),

  // --- Ontology ---
  generateOntology: (formData) =>
    client.post('/graph/ontology/generate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  // --- Graph building ---
  build: (data) => client.post('/gtm/simulate', data),

  // --- Tasks ---
  getTask: (taskId) => client.get(`/graph/task/${taskId}`),
  listTasks: () => client.get('/graph/tasks'),

  // --- Graph data ---
  getData: (graphId) => client.get(`/graph/data/${graphId}`),
  deleteGraph: (graphId) => client.delete(`/graph/delete/${graphId}`),

  // --- Search ---
  search: (graphId, query, { limit = 10, scope = 'edges' } = {}) =>
    client.post('/graph/search', { graph_id: graphId, query, limit, scope }),
}
