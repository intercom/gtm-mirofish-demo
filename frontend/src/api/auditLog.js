import client, { API_BASE } from './client'

export const auditLogApi = {
  getLogs(params = {}) {
    return client.get('/audit/logs', { params })
  },

  getExportUrl(params = {}) {
    const qs = new URLSearchParams()
    for (const [k, v] of Object.entries(params)) {
      if (v) qs.set(k, v)
    }
    const query = qs.toString()
    return `${API_BASE}/audit/logs/export${query ? '?' + query : ''}`
  },
}
