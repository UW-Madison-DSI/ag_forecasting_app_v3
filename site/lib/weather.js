/* Weather time-series chart (dual axis: temperature line + precip bars).
   Uses Chart.js, loaded from CDN in index.html. */

(function (root) {
  "use strict";

  let chartInstance = null;

  function destroyChart() {
    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }
  }

  function buildDateLabels(startIso, n) {
    const start = new Date(startIso + "T00:00:00Z");
    const labels = new Array(n);
    for (let i = 0; i < n; i++) {
      const d = new Date(start);
      d.setUTCDate(d.getUTCDate() + i);
      labels[i] = d.toISOString().slice(0, 10);
    }
    return labels;
  }

  function renderWeatherChart(canvasId, series, stationLabel) {
    destroyChart();
    const el = document.getElementById(canvasId);
    if (!el) return;
    if (!series || !series.tavg_f || !series.tavg_f.length) {
      el.parentElement.querySelector(".weather-empty").style.display = "block";
      return;
    }
    el.parentElement.querySelector(".weather-empty").style.display = "none";

    const labels = buildDateLabels(series.start, series.tavg_f.length);

    chartInstance = new Chart(el.getContext("2d"), {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Daily avg temp (°F)",
            data: series.tavg_f,
            borderColor: "#C5050C",
            backgroundColor: "rgba(197, 5, 12, 0.10)",
            yAxisID: "y",
            tension: 0.2,
            pointRadius: 0,
            borderWidth: 2,
            spanGaps: true,
          },
          {
            label: "Daily precip (in)",
            data: series.precip_in,
            type: "bar",
            backgroundColor: "rgba(37, 99, 235, 0.55)",
            borderColor: "rgba(37, 99, 235, 0.55)",
            yAxisID: "y1",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          title: { display: true, text: stationLabel || "" },
          legend: { position: "top" },
          tooltip: {
            callbacks: {
              title: (items) => items[0].label,
            },
          },
        },
        scales: {
          x: {
            ticks: { autoSkip: true, maxTicksLimit: 12 },
            grid: { display: false },
          },
          y: {
            type: "linear",
            position: "left",
            title: { display: true, text: "°F" },
          },
          y1: {
            type: "linear",
            position: "right",
            title: { display: true, text: "in" },
            grid: { drawOnChartArea: false },
            beginAtZero: true,
          },
        },
      },
    });
  }

  root.WIWeather = { renderWeatherChart };
})(window);
