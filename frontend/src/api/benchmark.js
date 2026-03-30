import client from './client'

export const benchmarkApi = {
  listEndpoints: () => client.get('/api/v1/benchmark/endpoints'),
  run: (iterations = 10, endpoints = null) =>
    client.post('/api/v1/benchmark/run', { iterations, endpoints }),
}
