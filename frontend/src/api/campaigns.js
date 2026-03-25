import client from './client'

export function fetchAttributionComparison() {
  return client.get('/campaigns/attribution')
}
