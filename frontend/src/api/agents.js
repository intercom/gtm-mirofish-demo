import client from './client'

export const agentsApi = {
  // --- Wizard CRUD ---
  list: () => client.get('/v1/agents'),
  get: (id) => client.get(`/v1/agents/${id}`),
  create: (data) => client.post('/v1/agents', data),
  update: (id, data) => client.put(`/v1/agents/${id}`, data),
  delete: (id) => client.delete(`/v1/agents/${id}`),
  clone: (id) => client.post(`/v1/agents/${id}/clone`),
  templates: () => client.get('/v1/agents/templates'),
  generate: (data) => client.post('/v1/agents/generate', data),
  previewResponse: (data) => client.post('/v1/agents/preview-response', data),

  // --- Archetypes ---
  listArchetypes: () =>
    client.get('/v1/agents/archetypes'),
  getArchetype: (archetypeId) =>
    client.get(`/v1/agents/archetypes/${archetypeId}`),

  // --- Agent Factory ---
  createFromArchetype: (data) =>
    client.post('/v1/agents/create', data),
  createBatch: (data) =>
    client.post('/v1/agents/batch', data),
  createFromScenario: (data) =>
    client.post('/v1/agents/from-scenario', data),
}
