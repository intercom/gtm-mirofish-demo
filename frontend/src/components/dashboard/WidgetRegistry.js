/**
 * Registry of all available dashboard widget types.
 * Maps widget_type → metadata for dynamic rendering and the WidgetPicker panel.
 */

import KpiCardWidget from './widgets/KpiCardWidget.vue'
import LineChartWidget from './widgets/LineChartWidget.vue'
import BarChartWidget from './widgets/BarChartWidget.vue'
import DonutChartWidget from './widgets/DonutChartWidget.vue'
import TableWidget from './widgets/TableWidget.vue'
import FunnelWidget from './widgets/FunnelWidget.vue'
import GaugeWidget from './widgets/GaugeWidget.vue'
import TextWidget from './widgets/TextWidget.vue'
import ActivityFeedWidget from './widgets/ActivityFeedWidget.vue'

const DATA_SOURCES = [
  'revenue',
  'pipeline',
  'salesforce',
  'cpq',
  'orders',
  'simulation',
  'reconciliation',
]

export const WIDGET_CATEGORIES = {
  charts: { label: 'Charts', order: 0 },
  cards: { label: 'Cards', order: 1 },
  tables: { label: 'Tables', order: 2 },
  other: { label: 'Other', order: 3 },
}

export const widgetRegistry = {
  kpi_card: {
    type: 'kpi_card',
    component: KpiCardWidget,
    label: 'KPI Card',
    description: 'Display a key metric with trend indicator and sparkline.',
    category: 'cards',
    icon: 'hash',
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
    component: LineChartWidget,
    label: 'Line Chart',
    description: 'Track metrics over time with multi-series support.',
    category: 'charts',
    icon: 'trending-up',
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
    component: BarChartWidget,
    label: 'Bar Chart',
    description: 'Compare values across categories with grouped bars.',
    category: 'charts',
    icon: 'bar-chart-2',
    defaultConfig: {
      data_source: 'pipeline',
      metrics: ['deal_count'],
      orientation: 'vertical',
      colors: ['#2068FF'],
      show_legend: true,
      show_labels: true,
    },
    defaultSize: { width: 6, height: 4 },
    supportedDataSources: DATA_SOURCES,
  },
  donut_chart: {
    type: 'donut_chart',
    component: DonutChartWidget,
    label: 'Donut Chart',
    description: 'Show proportional segments with center total.',
    category: 'charts',
    icon: 'pie-chart',
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
    component: TableWidget,
    label: 'Data Table',
    description: 'Sortable table with configurable columns and formatting.',
    category: 'tables',
    icon: 'table',
    defaultConfig: {
      data_source: 'pipeline',
      columns: [],
      sort_by: null,
      sort_dir: 'asc',
      row_limit: 10,
    },
    defaultSize: { width: 6, height: 4 },
    supportedDataSources: DATA_SOURCES,
  },
  funnel: {
    type: 'funnel',
    component: FunnelWidget,
    label: 'Funnel',
    description: 'Visualize stage-by-stage conversion rates.',
    category: 'charts',
    icon: 'filter',
    defaultConfig: {
      data_source: 'pipeline',
      stages: ['MQL', 'SQL', 'Opportunity', 'Closed Won'],
      show_conversion_rates: true,
      show_labels: true,
      show_percentages: true,
    },
    defaultSize: { width: 4, height: 4 },
    supportedDataSources: ['pipeline', 'salesforce', 'simulation'],
  },
  gauge: {
    type: 'gauge',
    component: GaugeWidget,
    label: 'Gauge',
    description: 'Display progress toward a target with a radial gauge.',
    category: 'charts',
    icon: 'activity',
    defaultConfig: {
      data_source: 'revenue',
      metric: 'quota_attainment',
      min: 0,
      max: 100,
      thresholds: [50, 80],
      colors: ['#ef4444', '#f59e0b', '#009900'],
    },
    defaultSize: { width: 3, height: 3 },
    supportedDataSources: ['revenue', 'pipeline', 'salesforce', 'orders'],
  },
  text: {
    type: 'text',
    component: TextWidget,
    label: 'Text / Note',
    description: 'Add titles, annotations, or markdown notes.',
    category: 'other',
    icon: 'type',
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
    component: ActivityFeedWidget,
    label: 'Activity Feed',
    description: 'Live stream of recent actions and events.',
    category: 'other',
    icon: 'activity',
    defaultConfig: {
      title: 'Activity',
      data_source: 'simulation',
      max_items: 20,
      show_timestamps: true,
    },
    defaultSize: { width: 4, height: 4 },
    supportedDataSources: ['simulation', 'salesforce', 'orders'],
  },
}

export const widgetTypes = Object.keys(widgetRegistry)

export const widgetCategories = {}
for (const [key, meta] of Object.entries(WIDGET_CATEGORIES)) {
  widgetCategories[key] = { ...meta, types: [] }
}
for (const [type, entry] of Object.entries(widgetRegistry)) {
  const cat = entry.category
  if (widgetCategories[cat]) {
    widgetCategories[cat].types.push(type)
  }
}

export function getWidgetTypes() {
  return Object.values(widgetRegistry)
}

export function getWidgetType(type) {
  return widgetRegistry[type] || null
}

export function getWidgetComponent(type) {
  return widgetRegistry[type]?.component ?? null
}

export function getWidgetDefaultConfig(type) {
  const entry = widgetRegistry[type]
  if (!entry) return {}
  return structuredClone(entry.defaultConfig)
}

export function getWidgetsByCategory() {
  const grouped = {}
  for (const [catKey, catMeta] of Object.entries(WIDGET_CATEGORIES)) {
    grouped[catKey] = {
      ...catMeta,
      widgets: Object.values(widgetRegistry).filter((w) => w.category === catKey),
    }
  }
  return grouped
}

export default widgetRegistry
