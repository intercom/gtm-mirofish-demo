import client from './client'

export const cpqApi = {
  getProducts: (params) => client.get('/v1/cpq/products', { params }),
  getQuotes: (params) => client.get('/v1/cpq/quotes', { params }),
  getQuote: (id) => client.get(`/v1/cpq/quotes/${id}`),
  approveQuote: (id) => client.post(`/v1/cpq/quotes/${id}/approve`),
  rejectQuote: (id, reason) =>
    client.post(`/v1/cpq/quotes/${id}/reject`, { reason }),
  getCpqStats: () => client.get('/v1/cpq/stats'),
}
