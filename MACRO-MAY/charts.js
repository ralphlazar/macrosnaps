/* ─────────────────────────────────────────────────────────────
   MacroSnaps v2 — Chart rendering
   Ported from existing renderMetricChart, adapted for light mode.
   Reads chart data from each metric's mounted element's data-spark
   attribute (JSON-encoded) and renders into the matching canvas.
   ───────────────────────────────────────────────────────────── */

(function () {
  const ORANGE_RGB = '249,115,22';
  const GREEN_RGB = '0,176,116';
  const RED_RGB = '217,58,79';
  const GRID = 'rgba(0,0,0,.05)';
  const ZERO = 'rgba(0,0,0,.2)';
  const TICK = '#888';
  const TOOLTIP_BG = '#fff';
  const TOOLTIP_BORDER = 'rgba(249,115,22,.4)';

  // From shell-frozen.chartConfig.annualLabels
  const ANNUAL_LABELS = [
    '2000','2001','2002','2003','2004','2005','2006','2007','2008','2009',
    '2010','2011','2012','2013','2014','2015','2016','2017','2018','2019',
    '2020','2021','2022','2023','2024','2025','2026F'
  ];

  // Per-metric chart config
  const METRIC_CFG = {
    'GDP Growth':     { type: 'bar', zeroLine: true },
    'Inflation (CPI)':{ type: 'line' },
    'Unemployment':   { type: 'line' },
    'Budget Deficit': { type: 'bar', zeroLine: true },
    'Current Account':{ type: 'bar', zeroLine: true },
    'Policy Rate':    { type: 'line', stepped: true },
    'Stock Market YTD': { type: 'line', zeroLine: true },
    '10Y Bond Yield': { type: 'line' },
    'Yield Curve':    { type: 'line', zeroLine: true, segmentColor: true },
    'USD/DXY':        { type: 'line', indexLabel: true },
    'CAD/USD':        { type: 'line' },
    'GBP/USD':        { type: 'line' },
    'USD/JPY':        { type: 'line' },
    'EUR/USD':        { type: 'line' },
    'USD/CNY':        { type: 'line' },
    'USD/INR':        { type: 'line' },
    'USD/ZAR':        { type: 'line' },
    'USD/BRL':        { type: 'line' },
    'USD/RUB':        { type: 'line' },
    'FX Rate':        { type: 'line' }
  };

  function monthLabelsFrom(startDateStr, n) {
    // startDateStr: "YYYY-MM"
    // Emit "MMM 'YY" at every position so autoSkip has labels to pick from
    // at any tick density (1Y, 2Y, 5Y, All).
    if (!startDateStr) return Array(n).fill('');
    const MONTH_ABBR = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const [y0, m0] = startDateStr.split('-').map(Number);
    const labels = [];
    for (let i = 0; i < n; i++) {
      const monthIdx = (m0 - 1) + i;
      const y = y0 + Math.floor(monthIdx / 12);
      const m = monthIdx % 12;
      labels.push(MONTH_ABBR[m] + " '" + String(y).slice(2));
    }
    return labels;
  }

  function sliceData(allVals, allLabels, rangeMonths) {
    if (!rangeMonths || rangeMonths === 0 || rangeMonths >= allVals.length) {
      return { vals: allVals, labels: allLabels };
    }
    return {
      vals: allVals.slice(-rangeMonths),
      labels: allLabels.slice(-rangeMonths)
    };
  }

  function renderChart(canvas, metricName, metricData, rangeMonths) {
    if (!window.Chart) { console.warn('Chart.js not loaded'); return; }
    const cfg = METRIC_CFG[metricName] || { type: 'line' };
    const isBar = cfg.type === 'bar';
    const allVals = metricData.v || [];
    if (!allVals.length) return;

    // Build labels
    let allLabels;
    if (isBar) {
      allLabels = ANNUAL_LABELS.slice(0, allVals.length);
    } else {
      allLabels = monthLabelsFrom(metricData.startDate, allVals.length);
    }

    const sliced = sliceData(allVals, allLabels, rangeMonths);
    const sliceVals = sliced.vals;
    const sliceLabels = sliced.labels;
    const n = sliceVals.length;

    // Axis range
    const mn = Math.min(...sliceVals);
    const mx = Math.max(...sliceVals);
    const range = mx - mn;
    const pad = (range * 0.15) || (Math.abs(mx) * 0.1) || 1;

    // Destroy any prior chart on this canvas
    if (canvas._chart) { canvas._chart.destroy(); canvas._chart = null; }
    const ctx = canvas.getContext('2d');

    let datasets;
    if (isBar) {
      const colors = sliceVals.map(v => v >= 0 ? `rgba(${ORANGE_RGB},.55)` : `rgba(${RED_RGB},.55)`);
      const borders = sliceVals.map(v => v >= 0 ? `rgba(${ORANGE_RGB},.9)` : `rgba(${RED_RGB},.9)`);
      datasets = [{
        data: sliceVals,
        backgroundColor: colors,
        borderColor: borders,
        borderWidth: 1,
        barPercentage: 0.85,
        categoryPercentage: 0.85
      }];
    } else if (cfg.segmentColor) {
      // Yield curve: green above 0, red below 0
      datasets = [{
        data: sliceVals,
        borderWidth: 1.5,
        pointRadius: 0,
        pointHitRadius: 8,
        pointHoverRadius: 3,
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderWidth: 1,
        tension: .3,
        fill: false,
        segment: {
          borderColor: function (ctx2) {
            const y0 = ctx2.p0.parsed.y, y1 = ctx2.p1.parsed.y;
            if (y0 >= 0 && y1 >= 0) return `rgba(${GREEN_RGB},.8)`;
            if (y0 < 0 && y1 < 0) return `rgba(${RED_RGB},.8)`;
            return 'rgba(120,120,120,.6)';
          }
        }
      }];
    } else {
      const grad = ctx.createLinearGradient(0, 0, 0, 140);
      grad.addColorStop(0, `rgba(${ORANGE_RGB},.22)`);
      grad.addColorStop(1, `rgba(${ORANGE_RGB},.01)`);
      datasets = [{
        data: sliceVals,
        borderColor: `rgba(${ORANGE_RGB},.9)`,
        borderWidth: 1.5,
        backgroundColor: grad,
        fill: true,
        pointRadius: 0,
        pointHitRadius: 8,
        pointHoverRadius: 3,
        pointHoverBackgroundColor: '#F97316',
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 1,
        tension: .35,
        stepped: cfg.stepped || false
      }];
    }

    canvas._chart = new Chart(ctx, {
      type: isBar ? 'bar' : 'line',
      data: { labels: sliceLabels, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        events: ['mousemove', 'mouseout', 'touchstart', 'touchmove'],
        layout: { padding: { left: 2, right: 2, top: 4, bottom: 0 } },
        scales: {
          x: {
            display: true,
            grid: { display: false },
            ticks: {
              color: function (context) {
                var label = sliceLabels[context.index];
                return (label && label.toString().endsWith('F')) ? '#F97316' : TICK;
              },
              font: { family: "'Space Mono', monospace", size: 8 },
              maxRotation: 0, autoSkip: true,
              maxTicksLimit: isBar ? 8 : (n <= 12 ? 6 : n <= 24 ? 8 : 10)
            },
            border: { display: false }
          },
          y: {
            display: true,
            position: 'right',
            grid: {
              color: function (context) {
                if (cfg.zeroLine && context.tick.value === 0) return ZERO;
                return GRID;
              },
              lineWidth: function (context) {
                return (cfg.zeroLine && context.tick.value === 0) ? 1.2 : 1;
              }
            },
            ticks: {
              color: TICK, font: { family: "'Space Mono', monospace", size: 8 },
              maxTicksLimit: 5,
              callback: function (v) {
                if (cfg.indexLabel && v >= 1000) return (v / 1000).toFixed(v % 1000 === 0 ? 0 : 1) + 'k';
                return (v % 1 === 0) ? v : v.toFixed(1);
              }
            },
            border: { display: false },
            min: mn - pad,
            max: mx + pad
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: TOOLTIP_BG,
            borderColor: TOOLTIP_BORDER,
            borderWidth: 1,
            titleFont: { family: "'Space Mono', monospace", size: 9 },
            bodyFont: { family: "'DM Sans', sans-serif", size: 11 },
            titleColor: '#888', bodyColor: '#1a1a1a',
            cornerRadius: 4, padding: 8, displayColors: false,
            callbacks: {
              label: function (ctx2) {
                let v = ctx2.parsed.y;
                if (cfg.indexLabel) return ' ' + v.toLocaleString();
                if (cfg.segmentColor) return ' ' + (v >= 0 ? '+' : '') + v + ' bps';
                return ' ' + v;
              }
            }
          }
        },
        interaction: { mode: 'index', intersect: false },
        animation: { duration: 350, easing: 'easeOutCubic' }
      }
    });
  }

  // Wire up all chart panels on the page
  function initAllCharts() {
    document.querySelectorAll('.metric-chart-wrap').forEach(wrap => {
      const metricName = wrap.dataset.metric;
      const dataAttr = wrap.dataset.chart;
      if (!metricName || !dataAttr) return;
      let metricData;
      try { metricData = JSON.parse(dataAttr); } catch (e) { return; }

      const canvas = wrap.querySelector('canvas');
      if (!canvas) return;

      const cfg = METRIC_CFG[metricName] || {};
      const isBar = cfg.type === 'bar';

      // Render with default range
      const defaultRange = isBar ? 0 : 60; // bar = all years; line = 5Y default
      renderChart(canvas, metricName, metricData, defaultRange);

      // Wire range buttons (line charts only)
      const btns = wrap.querySelectorAll('.mcr-btn');
      btns.forEach(btn => {
        btn.addEventListener('click', () => {
          btns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const r = parseInt(btn.dataset.r) || 0;
          renderChart(canvas, metricName, metricData, r);
        });
      });

      // Mark default-active button
      if (!isBar) {
        btns.forEach(b => { if (parseInt(b.dataset.r) === 60) b.classList.add('active'); });
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAllCharts);
  } else {
    initAllCharts();
  }
})();
