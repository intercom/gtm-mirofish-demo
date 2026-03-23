import client from './client'

// ── Report Generation ───────────────────────────

export function generateReport(data) {
  return client.post('/report/generate', data)
}

export function getGenerateStatus(data) {
  return client.post('/report/generate/status', data)
}

// ── Report Data ─────────────────────────────────

export function getReport(reportId) {
  return client.get(`/report/${reportId}`)
}

export function getReportBySimulation(simulationId) {
  return client.get(`/report/by-simulation/${simulationId}`)
}

export function listReports(params) {
  return client.get('/report/list', { params })
}

export function deleteReport(reportId) {
  return client.delete(`/report/${reportId}`)
}

export function downloadReport(reportId) {
  return client.get(`/report/${reportId}/download`, {
    responseType: 'blob',
  })
}

// ── Report Status & Progress ────────────────────

export function checkReportStatus(simulationId) {
  return client.get(`/report/check/${simulationId}`)
}

export function getReportProgress(reportId) {
  return client.get(`/report/${reportId}/progress`)
}

// ── Sections ────────────────────────────────────

export function getReportSections(reportId) {
  return client.get(`/report/${reportId}/sections`)
}

export function getSection(reportId, sectionIndex) {
  return client.get(`/report/${reportId}/section/${sectionIndex}`)
}

// ── Agent & Console Logs ────────────────────────

export function getAgentLog(reportId, fromLine) {
  return client.get(`/report/${reportId}/agent-log`, {
    params: { from_line: fromLine },
  })
}

export function streamAgentLog(reportId) {
  return client.get(`/report/${reportId}/agent-log/stream`)
}

export function getConsoleLog(reportId, fromLine) {
  return client.get(`/report/${reportId}/console-log`, {
    params: { from_line: fromLine },
  })
}

export function streamConsoleLog(reportId) {
  return client.get(`/report/${reportId}/console-log/stream`)
}
