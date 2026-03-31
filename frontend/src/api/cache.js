import client from './client'

const BASE = '/cache/simulations'

export const cacheApi = {
  list: () => client.get(BASE),
  get: (simulationId) => client.get(`${BASE}/${simulationId}`),
  create: (simulationId) => client.post(`${BASE}/${simulationId}`),
  delete: (simulationId) => client.delete(`${BASE}/${simulationId}`),
}
