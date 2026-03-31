import client from './client'

export const cpqApi = {
  // --- Products ---
  getProducts: (params) => client.get('/cpq/products', { params }),
  getProduct: (id) => client.get(`/cpq/products/${id}`),

  // --- Quotes ---
  getQuotes: (params) => client.get('/cpq/quotes', { params }),
  getQuote: (id) => client.get(`/cpq/quotes/${id}`),
  getPdfPreview: (id) => client.get(`/cpq/quotes/${id}/pdf-preview`),
  approveQuote: (id) => client.post(`/cpq/quotes/${id}/approve`),
  rejectQuote: (id, reason) =>
    client.post(`/cpq/quotes/${id}/reject`, { reason }),

  // --- Stats ---
  getCpqStats: () => client.get('/cpq/stats'),
}
