<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as d3 from 'd3'
import AppBadge from '../common/AppBadge.vue'

const props = defineProps({
  errors: {
    type: Array,
    default: null,
  },
})

// ── Remediation map ──────────────────────────────────────────────────────────
const REMEDIATIONS = {
  auth_expired: {
    title: 'Re-authenticate connector',
    steps: 'Navigate to connector settings and re-authorize with fresh credentials. Check if API tokens need rotation.',
  },
  rate_limited: {
    title: 'Reduce sync frequency',
    steps: 'Increase the sync interval or enable exponential backoff. Consider upgrading the API plan for higher rate limits.',
  },
  schema_change: {
    title: 'Update field mappings',
    steps: 'The source schema has changed. Review new/removed fields in the connector and update mappings accordingly.',
  },
  connection_timeout: {
    title: 'Check network & endpoint health',
    steps: 'Verify the source API is reachable. Check for firewall rules or DNS changes. Increase timeout thresholds if needed.',
  },
  permission_denied: {
    title: 'Fix API permissions',
    steps: 'The service account lacks required scopes. Re-authorize with admin permissions or request the necessary OAuth scopes.',
  },
  data_validation: {
    title: 'Fix source data quality',
    steps: 'Invalid or unexpected data in the source. Check for null required fields, type mismatches, or constraint violations.',
  },
}

const SEVERITY_ORDER = { critical: 0, error: 1, warning: 2 }

// ── Demo data ────────────────────────────────────────────────────────────────
function generateDemoErrors() {
  const connectors = ['Salesforce', 'Stripe', 'HubSpot', 'Zendesk', 'Intercom']
  const errorTypes = Object.keys(REMEDIATIONS)
  const severities = ['critical', 'error', 'warning']
  const now = Date.now()
  const DAY = 86400000

  const templates = [
    { connector: 'Salesforce', type: 'auth_expired', severity: 'critical', message: 'OAuth token expired', full: 'OAuth 2.0 refresh token has expired. The Salesforce connected app requires re-authorization. Last successful auth: 30 days ago. Error code: INVALID_GRANT.' },
    { connector: 'Stripe', type: 'rate_limited', severity: 'warning', message: 'API rate limit exceeded (429)', full: 'Stripe API returned 429 Too Many Requests. Current rate: 95 req/s, limit: 100 req/s. Sync batch size: 500 records. Retry-After header: 60s.' },
    { connector: 'HubSpot', type: 'schema_change', severity: 'error', message: 'Field "deal_stage" removed from API', full: 'HubSpot API v3 no longer returns "deal_stage" in the deals endpoint. Field was renamed to "dealstage" in API version 2024-03. 12 downstream dbt models depend on this field.' },
    { connector: 'Zendesk', type: 'connection_timeout', severity: 'warning', message: 'Connection timed out after 30s', full: 'TCP connection to api.zendesk.com:443 timed out after 30000ms. DNS resolution succeeded (104.16.53.111). TLS handshake did not complete. Possible network congestion or Zendesk maintenance window.' },
    { connector: 'Salesforce', type: 'permission_denied', severity: 'error', message: 'Insufficient privileges for Opportunity object', full: 'SFDC API returned INSUFFICIENT_ACCESS: User does not have access to Opportunity.Amount field. Required permission: "View All Data" or field-level security update. Integration user: sync@company.com.' },
    { connector: 'Intercom', type: 'data_validation', severity: 'warning', message: 'Null value in required field "email"', full: 'Record ID ic_usr_93847 has null "email" field which is required by the destination schema. 3 of 2,847 records in this batch have the same issue. Rows were skipped.' },
    { connector: 'Stripe', type: 'schema_change', severity: 'error', message: 'New required field "tax_id" in invoices', full: 'Stripe invoices endpoint now includes required field "tax_id" (added 2025-12-01). Destination table snowflake.raw.stripe_invoices does not have this column. 0 rows synced until schema is updated.' },
    { connector: 'HubSpot', type: 'rate_limited', severity: 'warning', message: 'Daily API quota 80% consumed', full: 'HubSpot daily API quota at 80% (400,000/500,000 calls). Current sync schedule will exhaust quota by 3:00 PM. Consider reducing sync frequency or upgrading to Enterprise API tier.' },
    { connector: 'Salesforce', type: 'connection_timeout', severity: 'critical', message: 'Repeated timeout — 5 consecutive failures', full: 'Salesforce API has been unreachable for 5 consecutive sync attempts over 2.5 hours. Last successful sync: 4 hours ago. Salesforce status page reports "Performance Degradation" for NA region. 15,000 records pending sync.' },
    { connector: 'Zendesk', type: 'auth_expired', severity: 'error', message: 'API token revoked', full: 'Zendesk API returned 401 Unauthorized. The API token was revoked by an admin. Token ID: zt_a8f3...b2c1. Last used: 2 hours ago. Generate a new token in Zendesk Admin > API.' },
    { connector: 'Intercom', type: 'rate_limited', severity: 'warning', message: 'Approaching rate limit (85%)', full: 'Intercom API rate limit usage at 85% for the current window. 170/200 requests used in the last 10-second window. Sync is throttling automatically.' },
    { connector: 'HubSpot', type: 'permission_denied', severity: 'error', message: 'Missing scope: crm.objects.contacts.read', full: 'HubSpot API returned 403 Forbidden. The private app is missing the "crm.objects.contacts.read" scope. Re-install the app with updated scopes in HubSpot Developer Portal.' },
    { connector: 'Stripe', type: 'data_validation', severity: 'warning', message: 'Currency mismatch: expected USD, got EUR', full: 'Invoice inv_1N2x3Y has currency "eur" but destination expects "usd". 7 invoices in this batch have non-USD currencies. Enable multi-currency support or add a currency filter.' },
    { connector: 'Salesforce', type: 'schema_change', severity: 'error', message: 'Custom field "MRR__c" type changed', full: 'Salesforce custom field "MRR__c" changed from Currency to Formula(Currency). Fivetran cannot sync formula fields with the current connector version. Affects: Account and Opportunity objects. 3 dbt models reference this field.' },
    { connector: 'Zendesk', type: 'data_validation', severity: 'warning', message: 'Oversized field: description > 65535 chars', full: 'Ticket #48291 has a description field exceeding the Snowflake VARCHAR limit (65,535 chars). Actual size: 72,104 chars. Record was truncated during load. Consider using VARIANT column type.' },
  ]

  return templates.map((t, i) => ({
    id: `err_${i + 1}`,
    timestamp: new Date(now - Math.random() * 7 * DAY).toISOString(),
    connector: t.connector,
    errorType: t.type,
    severity: t.severity,
    message: t.message,
    fullMessage: t.full,
  })).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
}

// ── State ────────────────────────────────────────────────────────────────────
const allErrors = computed(() => props.errors ?? generateDemoErrors())

const searchQuery = ref('')
const connectorFilter = ref('')
const errorTypeFilter = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const expandedIds = ref(new Set())
const groupByConnector = ref(false)

// ── Derived ──────────────────────────────────────────────────────────────────
const connectors = computed(() =>
  [...new Set(allErrors.value.map((e) => e.connector))].sort(),
)

const errorTypes = computed(() =>
  [...new Set(allErrors.value.map((e) => e.errorType))].sort(),
)

const filteredErrors = computed(() => {
  let result = allErrors.value

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(
      (e) =>
        e.connector.toLowerCase().includes(q) ||
        e.errorType.toLowerCase().includes(q) ||
        e.message.toLowerCase().includes(q),
    )
  }

  if (connectorFilter.value) {
    result = result.filter((e) => e.connector === connectorFilter.value)
  }

  if (errorTypeFilter.value) {
    result = result.filter((e) => e.errorType === errorTypeFilter.value)
  }

  if (dateFrom.value) {
    const from = new Date(dateFrom.value)
    result = result.filter((e) => new Date(e.timestamp) >= from)
  }

  if (dateTo.value) {
    const to = new Date(dateTo.value)
    to.setHours(23, 59, 59, 999)
    result = result.filter((e) => new Date(e.timestamp) <= to)
  }

  return result
})

const groupedErrors = computed(() => {
  if (!groupByConnector.value) return null
  const groups = {}
  for (const err of filteredErrors.value) {
    if (!groups[err.connector]) groups[err.connector] = []
    groups[err.connector].push(err)
  }
  return Object.entries(groups).sort(
    ([, a], [, b]) => b.length - a.length,
  )
})

const errorCountByConnector = computed(() => {
  const counts = {}
  for (const err of allErrors.value) {
    counts[err.connector] = (counts[err.connector] || 0) + 1
  }
  return counts
})

const hasActiveFilters = computed(
  () =>
    searchQuery.value ||
    connectorFilter.value ||
    errorTypeFilter.value ||
    dateFrom.value ||
    dateTo.value,
)

// ── Sparkline data (errors per day, last 7 days) ────────────────────────────
const sparklineData = computed(() => {
  const now = new Date()
  const days = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    d.setHours(0, 0, 0, 0)
    days.push({ date: new Date(d), count: 0 })
  }

  for (const err of allErrors.value) {
    const errDate = new Date(err.timestamp)
    errDate.setHours(0, 0, 0, 0)
    const match = days.find((d) => d.date.getTime() === errDate.getTime())
    if (match) match.count++
  }
  return days
})

// ── Actions ──────────────────────────────────────────────────────────────────
function toggleExpand(id) {
  const next = new Set(expandedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expandedIds.value = next
}

function clearFilters() {
  searchQuery.value = ''
  connectorFilter.value = ''
  errorTypeFilter.value = ''
  dateFrom.value = ''
  dateTo.value = ''
}

function formatErrorType(type) {
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatTimestamp(ts) {
  const d = new Date(ts)
  const now = new Date()
  const diffMs = now - d
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHrs = Math.floor(diffMins / 60)
  if (diffHrs < 24) return `${diffHrs}h ago`
  const diffDays = Math.floor(diffHrs / 24)
  if (diffDays < 7) return `${diffDays}d ago`
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function severityBadgeVariant(severity) {
  if (severity === 'critical') return 'error'
  if (severity === 'error') return 'warning'
  return 'neutral'
}

// ── Sparkline D3 rendering ───────────────────────────────────────────────────
const sparklineRef = ref(null)
let sparklineObserver = null

function renderSparkline() {
  if (!sparklineRef.value) return
  const container = sparklineRef.value
  d3.select(container).selectAll('*').remove()

  const data = sparklineData.value
  const width = container.clientWidth || 200
  const height = 40
  const margin = { top: 4, right: 4, bottom: 4, left: 4 }
  const innerW = width - margin.left - margin.right
  const innerH = height - margin.top - margin.bottom

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3
    .scaleTime()
    .domain(d3.extent(data, (d) => d.date))
    .range([0, innerW])

  const maxCount = d3.max(data, (d) => d.count) || 1
  const y = d3.scaleLinear().domain([0, maxCount]).range([innerH, 0])

  const area = d3
    .area()
    .x((d) => x(d.date))
    .y0(innerH)
    .y1((d) => y(d.count))
    .curve(d3.curveMonotoneX)

  const line = d3
    .line()
    .x((d) => x(d.date))
    .y((d) => y(d.count))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(data)
    .attr('d', area)
    .attr('fill', 'var(--color-error-light)')

  g.append('path')
    .datum(data)
    .attr('d', line)
    .attr('fill', 'none')
    .attr('stroke', 'var(--color-error)')
    .attr('stroke-width', 1.5)

  g.selectAll('.dot')
    .data(data)
    .join('circle')
    .attr('cx', (d) => x(d.date))
    .attr('cy', (d) => y(d.count))
    .attr('r', 2)
    .attr('fill', 'var(--color-error)')
}

onMounted(() => {
  nextTick(() => renderSparkline())
  if (sparklineRef.value) {
    sparklineObserver = new ResizeObserver(() => {
      renderSparkline()
    })
    sparklineObserver.observe(sparklineRef.value)
  }
})

onUnmounted(() => {
  if (sparklineObserver) sparklineObserver.disconnect()
})

watch(sparklineData, () => nextTick(() => renderSparkline()))
</script>

<template>
  <div class="bg-[--color-surface] border border-[--color-border] rounded-lg">
    <!-- Header -->
    <div class="p-4 border-b border-[--color-border]">
      <div class="flex items-center justify-between mb-3">
        <div>
          <h3 class="text-sm font-semibold text-[--color-text]">Sync Error Log</h3>
          <p class="text-xs text-[--color-text-muted] mt-0.5">
            {{ filteredErrors.length }} error{{ filteredErrors.length !== 1 ? 's' : '' }}
            <span v-if="hasActiveFilters"> (filtered)</span>
          </p>
        </div>
        <div class="flex items-center gap-3">
          <!-- Sparkline -->
          <div class="hidden sm:block">
            <div class="text-[10px] text-[--color-text-muted] mb-0.5 text-right">7-day trend</div>
            <div ref="sparklineRef" class="w-[120px] h-[40px]" />
          </div>
          <!-- Group toggle -->
          <button
            :class="[
              'text-xs px-2.5 py-1 rounded-md border transition-colors',
              groupByConnector
                ? 'bg-[--color-primary-light] border-[--color-primary-border] text-[--color-primary]'
                : 'bg-[--color-surface] border-[--color-border] text-[--color-text-secondary] hover:border-[--color-primary]',
            ]"
            @click="groupByConnector = !groupByConnector"
          >
            Group by connector
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-2">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search errors..."
          class="flex-1 min-w-[160px] bg-[--color-surface] border border-[--color-border] rounded-lg px-3 py-1.5 text-xs text-[--color-text] placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-primary] focus:ring-1 focus:ring-[--color-primary] transition-colors"
        />
        <select
          v-model="connectorFilter"
          class="bg-[--color-surface] border border-[--color-border] rounded-lg px-2 py-1.5 text-xs text-[--color-text] focus:outline-none focus:border-[--color-primary] transition-colors"
        >
          <option value="">All connectors</option>
          <option v-for="c in connectors" :key="c" :value="c">
            {{ c }} ({{ errorCountByConnector[c] || 0 }})
          </option>
        </select>
        <select
          v-model="errorTypeFilter"
          class="bg-[--color-surface] border border-[--color-border] rounded-lg px-2 py-1.5 text-xs text-[--color-text] focus:outline-none focus:border-[--color-primary] transition-colors"
        >
          <option value="">All error types</option>
          <option v-for="t in errorTypes" :key="t" :value="t">{{ formatErrorType(t) }}</option>
        </select>
        <input
          v-model="dateFrom"
          type="date"
          class="bg-[--color-surface] border border-[--color-border] rounded-lg px-2 py-1.5 text-xs text-[--color-text] focus:outline-none focus:border-[--color-primary] transition-colors"
        />
        <input
          v-model="dateTo"
          type="date"
          class="bg-[--color-surface] border border-[--color-border] rounded-lg px-2 py-1.5 text-xs text-[--color-text] focus:outline-none focus:border-[--color-primary] transition-colors"
        />
        <button
          v-if="hasActiveFilters"
          class="text-xs text-[--color-text-muted] hover:text-[--color-text] px-2 py-1.5 transition-colors"
          @click="clearFilters"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Error list -->
    <div class="max-h-[480px] overflow-y-auto">
      <!-- Empty state -->
      <div
        v-if="filteredErrors.length === 0"
        class="p-8 text-center text-xs text-[--color-text-muted]"
      >
        {{ hasActiveFilters ? 'No errors match the current filters.' : 'No sync errors recorded.' }}
      </div>

      <!-- Grouped view -->
      <template v-else-if="groupedErrors">
        <div v-for="[connector, errors] in groupedErrors" :key="connector">
          <div
            class="sticky top-0 z-10 px-4 py-2 bg-[--color-bg] border-b border-[--color-border] flex items-center gap-2"
          >
            <span class="text-xs font-semibold text-[--color-text]">{{ connector }}</span>
            <AppBadge variant="error">{{ errors.length }}</AppBadge>
          </div>
          <div
            v-for="err in errors"
            :key="err.id"
            class="border-b border-[--color-border] last:border-b-0"
          >
            <div
              class="px-4 py-3 flex items-start gap-3 cursor-pointer hover:bg-[--color-tint] transition-colors"
              @click="toggleExpand(err.id)"
            >
              <div
                :class="[
                  'mt-0.5 w-2 h-2 rounded-full shrink-0',
                  err.severity === 'critical' && 'bg-[--color-error]',
                  err.severity === 'error' && 'bg-[--color-warning]',
                  err.severity === 'warning' && 'bg-[--color-text-muted]',
                ]"
              />
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <AppBadge :variant="severityBadgeVariant(err.severity)">
                    {{ err.severity }}
                  </AppBadge>
                  <span class="text-xs text-[--color-text-secondary] font-mono">
                    {{ formatErrorType(err.errorType) }}
                  </span>
                </div>
                <p class="text-xs text-[--color-text] mt-1 truncate">{{ err.message }}</p>
              </div>
              <span class="text-[10px] text-[--color-text-muted] whitespace-nowrap shrink-0">
                {{ formatTimestamp(err.timestamp) }}
              </span>
              <svg
                :class="[
                  'w-3.5 h-3.5 shrink-0 text-[--color-text-muted] transition-transform duration-150',
                  expandedIds.has(err.id) && 'rotate-180',
                ]"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fill-rule="evenodd"
                  d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>

            <!-- Expanded detail -->
            <div
              v-if="expandedIds.has(err.id)"
              class="px-4 pb-3 pl-9"
            >
              <div class="bg-[--color-bg] rounded-md p-3 text-xs">
                <p class="text-[--color-text-secondary] font-mono leading-relaxed whitespace-pre-wrap">{{ err.fullMessage }}</p>
                <div
                  v-if="REMEDIATIONS[err.errorType]"
                  class="mt-3 pt-3 border-t border-[--color-border]"
                >
                  <p class="text-[--color-primary] font-semibold">
                    {{ REMEDIATIONS[err.errorType].title }}
                  </p>
                  <p class="text-[--color-text-muted] mt-1">
                    {{ REMEDIATIONS[err.errorType].steps }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Flat list view -->
      <template v-else>
        <div
          v-for="err in filteredErrors"
          :key="err.id"
          class="border-b border-[--color-border] last:border-b-0"
        >
          <div
            class="px-4 py-3 flex items-start gap-3 cursor-pointer hover:bg-[--color-tint] transition-colors"
            @click="toggleExpand(err.id)"
          >
            <div
              :class="[
                'mt-0.5 w-2 h-2 rounded-full shrink-0',
                err.severity === 'critical' && 'bg-[--color-error]',
                err.severity === 'error' && 'bg-[--color-warning]',
                err.severity === 'warning' && 'bg-[--color-text-muted]',
              ]"
            />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <AppBadge :variant="severityBadgeVariant(err.severity)">
                  {{ err.severity }}
                </AppBadge>
                <span class="text-xs font-semibold text-[--color-text]">{{ err.connector }}</span>
                <span class="text-xs text-[--color-text-secondary] font-mono">
                  {{ formatErrorType(err.errorType) }}
                </span>
              </div>
              <p class="text-xs text-[--color-text] mt-1 truncate">{{ err.message }}</p>
            </div>
            <span class="text-[10px] text-[--color-text-muted] whitespace-nowrap shrink-0">
              {{ formatTimestamp(err.timestamp) }}
            </span>
            <svg
              :class="[
                'w-3.5 h-3.5 shrink-0 text-[--color-text-muted] transition-transform duration-150',
                expandedIds.has(err.id) && 'rotate-180',
              ]"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                clip-rule="evenodd"
              />
            </svg>
          </div>

          <!-- Expanded detail -->
          <div
            v-if="expandedIds.has(err.id)"
            class="px-4 pb-3 pl-9"
          >
            <div class="bg-[--color-bg] rounded-md p-3 text-xs">
              <p class="text-[--color-text-secondary] font-mono leading-relaxed whitespace-pre-wrap">{{ err.fullMessage }}</p>
              <div
                v-if="REMEDIATIONS[err.errorType]"
                class="mt-3 pt-3 border-t border-[--color-border]"
              >
                <p class="text-[--color-primary] font-semibold">
                  {{ REMEDIATIONS[err.errorType].title }}
                </p>
                <p class="text-[--color-text-muted] mt-1">
                  {{ REMEDIATIONS[err.errorType].steps }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
