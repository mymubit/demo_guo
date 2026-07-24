(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var accent3 = style.getPropertyValue('--accent3').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var danger = style.getPropertyValue('--danger').trim();
  var warn = style.getPropertyValue('--warn').trim();

  // --- Chart 1: Pain Points Severity ---
  var chart1 = echarts.init(document.getElementById('chart-painpoints'), null, { renderer: 'svg' });
  chart1.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, axisPointer: { type: 'shadow' } },
    grid: { left: 180, right: 40, top: 20, bottom: 30 },
    xAxis: {
      type: 'value',
      max: 10,
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: muted },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: ['入口分散', '质检环过度设计', '进化机制空转', 'build脚本臃肿', '配置文件散落', '角色/模块/规则三层嵌套', '知识与规则重复', '层级过多认知负担', '规则碎片化'],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: ink, fontSize: 13 }
    },
    series: [{
      type: 'bar',
      data: [
        { value: 6.5, itemStyle: { color: '#fbbf24' } },
        { value: 7.0, itemStyle: { color: '#fbbf24' } },
        { value: 7.5, itemStyle: { color: '#f97316' } },
        { value: 7.5, itemStyle: { color: '#f97316' } },
        { value: 8.0, itemStyle: { color: '#f97316' } },
        { value: 8.5, itemStyle: { color: '#ef4444' } },
        { value: 8.5, itemStyle: { color: '#ef4444' } },
        { value: 9.0, itemStyle: { color: '#dc2626' } },
        { value: 9.5, itemStyle: { color: '#dc2626' } }
      ],
      barWidth: 22,
      itemStyle: { borderRadius: [0, 4, 4, 0] },
      label: {
        show: true,
        position: 'right',
        color: ink,
        fontSize: 12,
        fontWeight: 600,
        formatter: '{c}/10'
      }
    }]
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  // --- Chart 2: Before vs After File Count ---
  var chart2 = echarts.init(document.getElementById('chart-filecount'), null, { renderer: 'svg' });
  chart2.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true },
    legend: {
      data: ['优化前', '优化后'],
      top: 0,
      textStyle: { color: ink }
    },
    grid: { left: 60, right: 30, top: 50, bottom: 40 },
    xAxis: {
      type: 'category',
      data: ['规则文件', '约束文件', '配置文件', 'build脚本', '技能目录'],
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: muted, fontSize: 12, interval: 0 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: muted },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    series: [
      {
        name: '优化前',
        type: 'bar',
        data: [17, 11, 8, 15, 10],
        itemStyle: { color: muted, borderRadius: [4, 4, 0, 0] },
        barGap: '20%',
        barWidth: 28
      },
      {
        name: '优化后',
        type: 'bar',
        data: [8, 5, 4, 6, 3],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: accent },
            { offset: 1, color: accent2 }
          ]),
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: 28
      }
    ]
  });
  window.addEventListener('resize', function() { chart2.resize(); });

  // --- Chart 3: Architecture Layers Before vs After ---
  var chart3 = echarts.init(document.getElementById('chart-layers'), null, { renderer: 'svg' });
  chart3.setOption({
    animation: false,
    tooltip: { appendToBody: true },
    grid: { left: 50, right: 30, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: ['优化前 (8层)', '优化后 (5层)'],
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: ink, fontWeight: 600 }
    },
    yAxis: {
      type: 'value',
      max: 10,
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: muted },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    series: [{
      type: 'bar',
      data: [
        { value: 8, itemStyle: { color: danger } },
        { value: 5, itemStyle: { color: accent3 } }
      ],
      barWidth: 80,
      label: {
        show: true,
        position: 'top',
        color: ink,
        fontSize: 24,
        fontWeight: 700,
        formatter: '{c}层'
      },
      itemStyle: { borderRadius: [8, 8, 0, 0] }
    }]
  });
  window.addEventListener('resize', function() { chart3.resize(); });

  // --- Chart 4: Implementation Roadmap ---
  var chart4 = echarts.init(document.getElementById('chart-roadmap'), null, { renderer: 'svg' });
  chart4.setOption({
    animation: false,
    tooltip: {
      appendToBody: true,
      formatter: function(params) {
        return params.name + '<br/>工作量: ' + params.value + ' 人天';
      }
    },
    grid: { left: 120, right: 40, top: 30, bottom: 40 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: rule } },
      axisLabel: { color: muted, formatter: '{value} 天' },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: [
        'P3: 质检环简化',
        'P3: 进化机制瘦身',
        'P3: build脚本归类',
        'P2: 配置文件整合',
        'P2: 知识规则合并',
        'P1: 目录结构重组',
        'P1: 规则文件合并',
        'P0: 架构分层简化'
      ],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: ink, fontSize: 13 }
    },
    series: [{
      type: 'bar',
      data: [
        { value: 2, itemStyle: { color: '#94a3b8' } },
        { value: 2, itemStyle: { color: '#94a3b8' } },
        { value: 3, itemStyle: { color: '#94a3b8' } },
        { value: 5, itemStyle: { color: '#f59e0b' } },
        { value: 5, itemStyle: { color: '#f59e0b' } },
        { value: 6, itemStyle: { color: '#6366f1' } },
        { value: 8, itemStyle: { color: '#6366f1' } },
        { value: 4, itemStyle: { color: '#ec4899' } }
      ],
      barWidth: 24,
      itemStyle: { borderRadius: [0, 4, 4, 0] },
      label: {
        show: true,
        position: 'right',
        color: muted,
        fontSize: 12,
        formatter: '{c} 天'
      }
    }]
  });
  window.addEventListener('resize', function() { chart4.resize(); });

  // --- Chart 5: Benefit Radar ---
  var chart5 = echarts.init(document.getElementById('chart-benefits'), null, { renderer: 'svg' });
  chart5.setOption({
    animation: false,
    tooltip: { appendToBody: true },
    legend: {
      data: ['优化前', '优化后'],
      bottom: 0,
      textStyle: { color: ink }
    },
    radar: {
      indicator: [
        { name: '新人上手速度', max: 100 },
        { name: '规则查找效率', max: 100 },
        { name: '维护成本', max: 100 },
        { name: '系统清晰度', max: 100 },
        { name: '扩展便利性', max: 100 },
        { name: '调试排错速度', max: 100 }
      ],
      axisName: { color: ink, fontSize: 12 },
      splitLine: { lineStyle: { color: rule } },
      splitArea: { areaStyle: { color: [bg2, 'transparent'] } },
      axisLine: { lineStyle: { color: rule } }
    },
    series: [{
      type: 'radar',
      data: [
        {
          value: [30, 35, 25, 30, 40, 35],
          name: '优化前',
          lineStyle: { color: muted, width: 2 },
          areaStyle: { color: muted + '22' },
          itemStyle: { color: muted }
        },
        {
          value: [80, 85, 75, 85, 75, 80],
          name: '优化后',
          lineStyle: { color: accent, width: 2 },
          areaStyle: { color: accent + '33' },
          itemStyle: { color: accent }
        }
      ]
    }]
  });
  window.addEventListener('resize', function() { chart5.resize(); });

})();
