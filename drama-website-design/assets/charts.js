// assets/charts.js
(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var bg = style.getPropertyValue('--bg').trim();
  var success = style.getPropertyValue('--success').trim();

  // --- Chart: Quality Radar ---
  var radarEl = document.getElementById('chart-quality-radar');
  if (radarEl) {
    var chartRadar = echarts.init(radarEl, null, { renderer: 'svg' });
    chartRadar.setOption({
      animation: false,
      tooltip: {
        appendToBody: true,
        backgroundColor: bg2,
        borderColor: rule,
        textStyle: { color: ink }
      },
      legend: {
        data: ['当前得分', '目标值 (B级)'],
        textStyle: { color: muted, fontSize: 12 },
        bottom: 0,
      },
      radar: {
        indicator: [
          { name: '钩子密度', max: 100 },
          { name: '情绪张力', max: 100 },
          { name: '人物立体度', max: 100 },
          { name: '剧情逻辑性', max: 100 },
          { name: '对白自然度', max: 100 },
          { name: '节奏紧凑度', max: 100 },
          { name: '场景画面感', max: 100 },
          { name: '商业适配度', max: 100 },
          { name: '原创性', max: 100 },
          { name: '连续性', max: 100 }
        ],
        radius: '65%',
        axisName: {
          color: muted,
          fontSize: 12
        },
        splitArea: {
          areaStyle: {
            color: ['rgba(255,255,255,0.02)', 'rgba(255,255,255,0.04)']
          }
        },
        axisLine: {
          lineStyle: { color: rule }
        },
        splitLine: {
          lineStyle: { color: rule }
        }
      },
      series: [{
        type: 'radar',
        data: [
          {
            value: [82, 78, 75, 70, 68, 72, 76, 80, 65, 85],
            name: '当前得分',
            lineStyle: { color: accent, width: 2 },
            areaStyle: { color: 'rgba(245, 166, 35, 0.2)' },
            itemStyle: { color: accent }
          },
          {
            value: [70, 70, 70, 70, 70, 70, 70, 70, 70, 70],
            name: '目标值 (B级)',
            lineStyle: { color: accent2, width: 1, type: 'dashed' },
            areaStyle: { color: 'rgba(108, 124, 224, 0.1)' },
            itemStyle: { color: accent2 }
          }
        ]
      }]
    });
    window.addEventListener('resize', function() { chartRadar.resize(); });
  }
})();
