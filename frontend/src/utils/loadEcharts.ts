/** 动态加载 echarts，便于测试 mock，并控制 Usage 页体积。 */
export async function loadEcharts(): Promise<typeof import('echarts')> {
  return import('echarts')
}
