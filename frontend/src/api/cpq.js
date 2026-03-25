import client from './client'

export const cpqApi = {
  getProducts: (params) => client.get('/v1/cpq/products', { params }),
  getProduct: (id) => client.get(`/v1/cpq/products/${id}`),
}
