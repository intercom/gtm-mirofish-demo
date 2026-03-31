import client from './client'

export const benchmarkApi = {
  listEndpoints: () => client.get('/benchmark/endpoints'),
  run: (iterations = 10, endpoints = null) =>
    client.post('/benchmark/run', { iterations, endpoints }),
}
