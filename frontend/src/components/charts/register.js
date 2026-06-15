import * as echarts from 'echarts/core'
import {
  BarChart,
  LineChart,
  PieChart,
  GraphChart,
  SankeyChart,
} from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DatasetComponent,
  GraphicComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { SCRIPTFORGE_CHART_THEME, scriptforgeChartTheme } from './theme'

let registered = false

/** 按需注册 ECharts 模块（柱/线/饼/关系图/桑基图） */
export function ensureEchartsRegistered() {
  if (registered) return
  echarts.use([
    BarChart,
    LineChart,
    PieChart,
    GraphChart,
    SankeyChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
    TitleComponent,
    DatasetComponent,
    GraphicComponent,
    CanvasRenderer,
  ])
  echarts.registerTheme(SCRIPTFORGE_CHART_THEME, scriptforgeChartTheme)
  registered = true
}

export { echarts, SCRIPTFORGE_CHART_THEME }
