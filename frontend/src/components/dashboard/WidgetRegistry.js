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

export const widgetRegistry = {
  kpi_card: {
    component: KpiCardWidget,
    defaultConfig: {
      label: 'KPI',
      metric_name: '',
      data_source: 'simulation',
      prefix: '',
      suffix: '',
      show_trend: true,
      show_sparkline: false,
      color: 'auto',
    },
    icon: 'hash',
    label: 'KPI Card',
    category: 'cards',
    description: 'Display a key metric with optional trend and sparkline',
    supportedDataSources: DATA_SOURCES,
  },

  line_chart: {
    component: LineChartWidget,
    defaultConfig: {
      title: '',
      data_source: 'simulation',
      metrics: [],
      time_range: '30d',
      colors: [],
      show_legend: true,
      show_labels: false,
    },
    icon: 'trending-up',
    label: 'Line Chart',
    category: 'charts',
    description: 'Multi-line time series chart with hover crosshair',
    supportedDataSources: DATA_SOURCES,
  },

  bar_chart: {
    component: BarChartWidget,
    defaultConfig: {
      title: '',
      data_source: 'simulation',
      metrics: [],
      orientation: 'vertical',
      colors: [],
      show_legend: true,
      show_labels: true,
    },
    icon: 'bar-chart-2',
    label: 'Bar Chart',
    category: 'charts',
    description: 'Single or grouped bars, horizontal or vertical',
    supportedDataSources: DATA_SOURCES,
  },

  donut_chart: {
    component: DonutChartWidget,
    defaultConfig: {
      title: '',
      data_source: 'simulation',
      metrics: [],
      colors: [],
      show_labels: true,
      center_text: '',
    },
    icon: 'pie-chart',
    label: 'Donut Chart',
    category: 'charts',
    description: 'Segmented donut with center summary text',
    supportedDataSources: DATA_SOURCES,
  },

  table: {
    component: TableWidget,
    defaultConfig: {
      title: '',
      data_source: 'simulation',
      columns: [],
      sort_by: '',
      sort_dir: 'asc',
      row_limit: 25,
    },
    icon: 'table',
    label: 'Table',
    category: 'tables',
    description: 'Sortable table with configurable columns and formatting',
    supportedDataSources: DATA_SOURCES,
  },

  funnel: {
    component: FunnelWidget,
    defaultConfig: {
      title: '',
      data_source: 'pipeline',
      stages: [],
      colors: [],
      show_labels: true,
      show_percentages: true,
    },
    icon: 'filter',
    label: 'Funnel',
    category: 'charts',
    description: 'Funnel visualization for pipeline or conversion stages',
    supportedDataSources: DATA_SOURCES,
  },

  gauge: {
    component: GaugeWidget,
    defaultConfig: {
      title: '',
      data_source: 'simulation',
      metric_name: '',
      min: 0,
      max: 100,
      thresholds: [30, 70],
      colors: ['#ef4444', '#f59e0b', '#009900'],
    },
    icon: 'activity',
    label: 'Gauge',
    category: 'charts',
    description: 'Radial gauge with configurable thresholds',
    supportedDataSources: DATA_SOURCES,
  },

  text: {
    component: TextWidget,
    defaultConfig: {
      content: '',
      font_size: 'base',
      alignment: 'left',
    },
    icon: 'type',
    label: 'Text',
    category: 'other',
    description: 'Markdown content for titles, notes, or annotations',
    supportedDataSources: [],
  },

  activity_feed: {
    component: ActivityFeedWidget,
    defaultConfig: {
      title: 'Activity',
      data_source: 'simulation',
      max_items: 20,
      show_timestamps: true,
    },
    icon: 'activity',
    label: 'Activity Feed',
    category: 'other',
    description: 'Chronological event log from simulation or data source',
    supportedDataSources: DATA_SOURCES,
  },
}

export const widgetTypes = Object.keys(widgetRegistry)

export const widgetCategories = {
  cards: { label: 'Cards', types: [] },
  charts: { label: 'Charts', types: [] },
  tables: { label: 'Tables', types: [] },
  other: { label: 'Other', types: [] },
}

for (const [type, entry] of Object.entries(widgetRegistry)) {
  const cat = entry.category
  if (widgetCategories[cat]) {
    widgetCategories[cat].types.push(type)
  }
}

export function getWidgetComponent(type) {
  return widgetRegistry[type]?.component ?? null
}

export function getWidgetDefaultConfig(type) {
  const entry = widgetRegistry[type]
  if (!entry) return {}
  return structuredClone(entry.defaultConfig)
}
