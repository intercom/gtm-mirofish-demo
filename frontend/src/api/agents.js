import client from './client'

export const agentsApi = {
  // --- Archetypes ---
  listArchetypes: () =>
    client.get('/v1/agents/archetypes'),
  getArchetype: (archetypeId) =>
    client.get(`/v1/agents/archetypes/${archetypeId}`),

  // --- Agent creation ---
  create: (data) =>
    client.post('/v1/agents/create', data),
  createBatch: (data) =>
    client.post('/v1/agents/batch', data),
  createFromScenario: (data) =>
    client.post('/v1/agents/from-scenario', data),
}
