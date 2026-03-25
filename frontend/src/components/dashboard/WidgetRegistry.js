const CATEGORIES = [
  { id: 'charts', label: 'Charts', order: 0 },
  { id: 'cards', label: 'Cards', order: 1 },
  { id: 'tables', label: 'Tables', order: 2 },
  { id: 'other', label: 'Other', order: 3 },
]

const WIDGETS = [
  {
    type: 'line-chart',
    label: 'Line Chart',
    description: 'Trend data over time',
    category: 'charts',
    icon: 'chart-line',
    defaultSize: { w: 4, h: 3 },
    defaultConfig: { title: 'Line Chart', dataSource: 'simulation' },
  },
  {
    type: 'bar-chart',
    label: 'Bar Chart',
    description: 'Compare values across categories',
    category: 'charts',
    icon: 'chart-bar',
    defaultSize: { w: 4, h: 3 },
    defaultConfig: { title: 'Bar Chart', dataSource: 'simulation' },
  },
  {
    type: 'donut-chart',
    label: 'Donut Chart',
    description: 'Show proportional distribution',
    category: 'charts',
    icon: 'chart-donut',
    defaultSize: { w: 3, h: 3 },
    defaultConfig: { title: 'Donut Chart', dataSource: 'simulation' },
  },
  {
    type: 'kpi-card',
    label: 'KPI Card',
    description: 'Single metric with trend indicator',
    category: 'cards',
    icon: 'metric',
    defaultSize: { w: 3, h: 2 },
    defaultConfig: { title: 'KPI', value: '—', trend: null },
  },
  {
    type: 'data-table',
    label: 'Data Table',
    description: 'Tabular data with sorting',
    category: 'tables',
    icon: 'table',
    defaultSize: { w: 6, h: 4 },
    defaultConfig: { title: 'Data Table', columns: [], rows: [] },
  },
  {
    type: 'funnel',
    label: 'Funnel',
    description: 'Conversion funnel visualization',
    category: 'other',
    icon: 'funnel',
    defaultSize: { w: 4, h: 3 },
    defaultConfig: { title: 'Funnel', stages: [] },
  },
  {
    type: 'text',
    label: 'Text Block',
    description: 'Rich text or markdown content',
    category: 'other',
    icon: 'text',
    defaultSize: { w: 4, h: 2 },
    defaultConfig: { title: '', content: 'Enter text here...' },
  },
  {
    type: 'activity-feed',
    label: 'Activity Feed',
    description: 'Chronological event stream',
    category: 'other',
    icon: 'activity',
    defaultSize: { w: 3, h: 4 },
    defaultConfig: { title: 'Activity', maxItems: 20 },
  },
]

export function getWidgetDef(type) {
  return WIDGETS.find((w) => w.type === type)
}

export function getWidgetsByCategory() {
  return CATEGORIES.map((cat) => ({
    ...cat,
    widgets: WIDGETS.filter((w) => w.category === cat.id),
  })).filter((cat) => cat.widgets.length > 0)
}

export { CATEGORIES, WIDGETS }
