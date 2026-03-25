/**
 * Registry of all available dashboard widget types.
 * Maps widget_type → metadata for dynamic rendering and the WidgetPicker panel.
 * Actual widget components will be registered as they are built.
 */

export const WIDGET_CATEGORIES = {
  charts: { label: 'Charts', order: 0 },
  cards: { label: 'Cards', order: 1 },
  tables: { label: 'Tables', order: 2 },
  other: { label: 'Other', order: 3 },
}

const registry = {
  kpi_card: {
    type: 'kpi_card',
    label: 'KPI Card',
    description: 'Display a key metric with trend indicator and sparkline.',
    category: 'cards',
    icon: 'kpi_card',
    component: null,
    defaultConfig: {
      data_source: 'revenue',
      metric_name: 'total_revenue',
      label: 'Total Revenue',
      prefix: '$',
      suffix: '',
      show_trend: true,
      show_sparkline: true,
      color: 'auto',
    },
    defaultSize: { width: 3, height: 2 },
    supportedDataSources: ['revenue', 'pipeline', 'salesforce', 'orders', 'simulation'],
  },
  line_chart: {
    type: 'line_chart',
    label: 'Line Chart',
    description: 'Track metrics over time with multi-series support.',
    category: 'charts',
    icon: 'line_chart',
    component: null,
    defaultConfig: {
      data_source: 'revenue',
      metrics: ['total_revenue'],
      time_range: '30d',
      colors: ['#2068FF', '#ff5600'],
      show_legend: true,
      show_labels: true,
    },
    defaultSize: { width: 6, height: 4 },
    supportedDataSources: ['revenue', 'pipeline', 'salesforce', 'simulation'],
  },
  bar_chart: {
    type: 'bar_chart',
    label: 'Bar Chart',
    description: 'Compare values across categories with grouped bars.',
    category: 'charts',
    icon: 'bar_chart',
    component: null,
    defaultConfig: {
      data_source: 'pipeline',
      metrics: ['deal_count'],
      orientation: 'vertical',
      colors: ['#2068FF'],
      show_legend: true,
      show_labels: true,
    },
    defaultSize: { width: 6, height: 4 },
    supportedDataSources: ['revenue', 'pipeline', 'salesforce', 'orders', 'simulation'],
  },
  donut_chart: {
    type: 'donut_chart',
    label: 'Donut Chart',
    description: 'Show proportional segments with center total.',
    category: 'charts',
    icon: 'donut_chart',
    component: null,
    defaultConfig: {
      data_source: 'pipeline',
      metric: 'stage_distribution',
      colors: ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#f59e0b'],
      show_labels: true,
    },
    defaultSize: { width: 4, height: 4 },
    supportedDataSources: ['pipeline', 'salesforce', 'orders', 'simulation'],
  },
  table: {
    type: 'table',
    label: 'Data Table',
    description: 'Sortable table with configurable columns and formatting.',
    category: 'tables',
    icon: 'table',
    component: null,
    defaultConfig: {
      data_source: 'pipeline',
      columns: [],
      sort_by: null,
      sort_dir: 'asc',
      row_limit: 10,
    },
    defaultSize: { width: 6, height: 4 },
    supportedDataSources: ['revenue', 'pipeline', 'salesforce', 'cpq', 'orders', 'simulation', 'reconciliation'],
  },
  funnel: {
    type: 'funnel',
    label: 'Funnel',
    description: 'Visualize stage-by-stage conversion rates.',
    category: 'other',
    icon: 'funnel',
    component: null,
    defaultConfig: {
      data_source: 'pipeline',
      stages: ['MQL', 'SQL', 'Opportunity', 'Closed Won'],
      show_conversion_rates: true,
    },
    defaultSize: { width: 4, height: 4 },
    supportedDataSources: ['pipeline', 'salesforce', 'simulation'],
  },
  gauge: {
    type: 'gauge',
    label: 'Gauge',
    description: 'Display progress toward a target with a radial gauge.',
    category: 'other',
    icon: 'gauge',
    component: null,
    defaultConfig: {
      data_source: 'revenue',
      metric: 'quota_attainment',
      min: 0,
      max: 100,
      thresholds: [50, 80],
    },
    defaultSize: { width: 3, height: 3 },
    supportedDataSources: ['revenue', 'pipeline', 'salesforce', 'orders'],
  },
  text: {
    type: 'text',
    label: 'Text / Note',
    description: 'Add titles, annotations, or markdown notes.',
    category: 'other',
    icon: 'text',
    component: null,
    defaultConfig: {
      content: '',
      font_size: 'base',
      alignment: 'left',
    },
    defaultSize: { width: 4, height: 2 },
    supportedDataSources: [],
  },
  activity_feed: {
    type: 'activity_feed',
    label: 'Activity Feed',
    description: 'Live stream of recent actions and events.',
    category: 'other',
    icon: 'activity_feed',
    component: null,
    defaultConfig: {
      data_source: 'simulation',
      max_items: 20,
      show_timestamps: true,
    },
    defaultSize: { width: 4, height: 4 },
    supportedDataSources: ['simulation', 'salesforce', 'orders'],
  },
}

export function getWidgetTypes() {
  return Object.values(registry)
}

export function getWidgetType(type) {
  return registry[type] || null
}

export function getWidgetsByCategory() {
  const grouped = {}
  for (const [catKey, catMeta] of Object.entries(WIDGET_CATEGORIES)) {
    grouped[catKey] = {
      ...catMeta,
      widgets: Object.values(registry).filter((w) => w.category === catKey),
    }
  }
  return grouped
}

export default registry
