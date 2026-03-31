import client from './client'

export const beliefsApi = {
  getDimensions: () =>
    client.get('/beliefs/dimensions'),

  extract: (simulationId, actions, useLlm = false) =>
    client.post(`/beliefs/${simulationId}/extract`, {
      actions,
      use_llm: useLlm,
    }),

  demo: (rounds = 10) =>
    client.get('/beliefs/demo', { params: { rounds } }),
}
