import client from './client'

export const personasApi = {
  list: () => client.get('/personas'),
  generate: (payload) => client.post('/personas/generate', payload),
  get: (id) => client.get(`/personas/${id}`),
  update: (id, data) => client.put(`/personas/${id}`, data),
  enhance: (id, simulationContext) =>
    client.post(`/personas/${id}/enhance`, { simulation_context: simulationContext }),
}
