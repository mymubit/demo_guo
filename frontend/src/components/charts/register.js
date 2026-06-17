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
import { LegacyGridContainLabel } from 'echarts/features'
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
    LegacyGridContainLabel,
  ])
  echarts.registerTheme(SCRIPTFORGE_CHART_THEME, scriptforgeChartTheme)
  registered = true
}

// 模块加载时同步注册，避免首屏渲染早于 useEffect 导致 renderer 未就绪
ensureEchartsRegistered()

export { echarts, SCRIPTFORGE_CHART_THEME }
