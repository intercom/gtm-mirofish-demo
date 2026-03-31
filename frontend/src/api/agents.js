import client from './client'

export const agentsApi = {
  // --- Wizard CRUD ---
  list: () => client.get('/agents'),
  get: (id) => client.get(`/agents/${id}`),
  create: (data) => client.post('/agents', data),
  update: (id, data) => client.put(`/agents/${id}`, data),
  delete: (id) => client.delete(`/agents/${id}`),
  clone: (id) => client.post(`/agents/${id}/clone`),
  templates: () => client.get('/agents/templates'),
  generate: (data) => client.post('/agents/generate', data),
  previewResponse: (data) => client.post('/agents/preview-response', data),

  // --- Archetypes ---
  listArchetypes: () =>
    client.get('/agents/archetypes'),
  getArchetype: (archetypeId) =>
    client.get(`/agents/archetypes/${archetypeId}`),

  // --- Agent Factory ---
  createFromArchetype: (data) =>
    client.post('/agents/create', data),
  createBatch: (data) =>
    client.post('/agents/batch', data),
  createFromScenario: (data) =>
    client.post('/agents/from-scenario', data),
}
