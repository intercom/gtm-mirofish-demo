import client from './client'

export const personasApi = {
  list: () => client.get('/v1/personas'),
  generate: (payload) => client.post('/v1/personas/generate', payload),
  get: (id) => client.get(`/v1/personas/${id}`),
  update: (id, data) => client.put(`/v1/personas/${id}`, data),
  enhance: (id, simulationContext) =>
    client.post(`/v1/personas/${id}/enhance`, { simulation_context: simulationContext }),
}
