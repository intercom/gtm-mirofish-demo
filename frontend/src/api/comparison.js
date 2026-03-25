import client from './client'

export const comparisonApi = {
  compare: (simIdA, simIdB) =>
    client.get('/simulations/compare', { params: { ids: `${simIdA},${simIdB}` } }),
}
