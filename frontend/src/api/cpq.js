import client from './client'

export const cpqApi = {
  // --- Products ---
  getProducts: (params) => client.get('/v1/cpq/products', { params }),
  getProduct: (id) => client.get(`/v1/cpq/products/${id}`),

  // --- Quotes ---
  getQuotes: (params) => client.get('/v1/cpq/quotes', { params }),
  getQuote: (id) => client.get(`/v1/cpq/quotes/${id}`),
  getPdfPreview: (id) => client.get(`/v1/cpq/quotes/${id}/pdf-preview`),
  approveQuote: (id) => client.post(`/v1/cpq/quotes/${id}/approve`),
  rejectQuote: (id, reason) =>
    client.post(`/v1/cpq/quotes/${id}/reject`, { reason }),

  // --- Stats ---
  getCpqStats: () => client.get('/v1/cpq/stats'),
}
