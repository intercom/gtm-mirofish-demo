import client from './client'

export const memoryTransferApi = {
  // Export agent memory from a simulation
  exportMemory: (data) => client.post('/memory/export', data),

  // Import a memory bundle into a simulation
  importMemory: (data) => client.post('/memory/import', data),

  // Transfer memory between simulations in one step
  transfer: (data) => client.post('/memory/transfer', data),

  // List all memory bundles for a simulation
  listBundles: (simulationId) => client.get(`/memory/bundles/${simulationId}`),

  // Get a specific bundle
  getBundle: (simulationId, bundleId) =>
    client.get(`/memory/bundles/${simulationId}/${bundleId}`),

  // Delete a bundle
  deleteBundle: (simulationId, bundleId) =>
    client.delete(`/memory/bundles/${simulationId}/${bundleId}`),

  // Get demo bundles (no simulation data required)
  getDemoBundles: () => client.get('/memory/demo-bundles'),
}
