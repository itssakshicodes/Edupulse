/* ================================================================
   EduPulse — Main JavaScript
   Sidebar toggle, chart helpers, AJAX filter utilities
   ================================================================ */

// ── Sidebar toggle ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const toggle  = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const wrapper = document.getElementById('mainWrapper');

  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
      } else {
        const collapsed = sidebar.style.width === '60px';
        sidebar.style.width     = collapsed ? '260px' : '60px';
        if (wrapper) wrapper.style.marginLeft = collapsed ? '260px' : '60px';
        sidebar.querySelectorAll('.brand-text, .user-info, .nav-item span, .nav-section-label')
          .forEach(el => el.style.display = collapsed ? '' : 'none');
      }
    });
  }

  // Close sidebar on outside click (mobile)
  document.addEventListener('click', function (e) {
    if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('open')) {
      if (!sidebar.contains(e.target) && e.target !== toggle) {
        sidebar.classList.remove('open');
      }
    }
  });
});


// ── Google Charts loader ─────────────────────────────────────────────────
window.EduPulse = window.EduPulse || {};

EduPulse.chartsLoaded = false;
EduPulse.chartQueue   = [];

google.charts.load('current', { packages: ['corechart', 'bar'] });
google.charts.setOnLoadCallback(function () {
  EduPulse.chartsLoaded = true;
  EduPulse.chartQueue.forEach(fn => fn());
  EduPulse.chartQueue = [];
});

/**
 * Safely draw a chart, queuing it if Google Charts isn't ready yet.
 * @param {Function} drawFn — zero-argument function that draws the chart
 */
EduPulse.drawChart = function (drawFn) {
  if (EduPulse.chartsLoaded) drawFn();
  else EduPulse.chartQueue.push(drawFn);
};

/**
 * Fetch JSON from a URL and draw a Google Chart.
 * @param {string} url      — AJAX endpoint returning { data: [[...], ...] }
 * @param {string} divId    — target container element ID
 * @param {string} type     — 'PieChart'|'ColumnChart'|'BarChart'|'LineChart'|'ScatterChart'
 * @param {object} options  — extra Google Charts options
 */
EduPulse.loadChart = function (url, divId, type, options = {}) {
  const container = document.getElementById(divId);
  if (!container) return;

  // Loading state
  container.innerHTML = '<div class="d-flex align-items-center justify-content-center" style="height:200px"><div class="spinner-border text-secondary"></div></div>';

  fetch(url)
    .then(r => r.json())
    .then(json => {
      if (!json.data || json.data.length < 2) {
        container.innerHTML = '<p class="text-center text-muted py-4">No data available</p>';
        return;
      }
      EduPulse.drawChart(() => {
        const dataTable = google.visualization.arrayToDataTable(json.data);
        const defaultOpts = {
          fontName: 'Inter',
          colors: ['#00b4d8', '#e94560', '#2ec4b6', '#ff9f1c', '#1a1a2e'],
          legend: { position: 'bottom', textStyle: { fontSize: 12 } },
          chartArea: { left: 60, right: 20, top: 20, bottom: 60, width: '90%', height: '75%' },
          backgroundColor: 'transparent',
          animation: { startup: true, duration: 800, easing: 'out' },
        };
        const merged = Object.assign({}, defaultOpts, options);
        const chart  = new google.visualization[type](container);
        chart.draw(dataTable, merged);
      });
    })
    .catch(() => {
      container.innerHTML = '<p class="text-center text-danger py-4">Failed to load chart data.</p>';
    });
};


// ── Smart filter: AJAX reload on select change ────────────────────────────
EduPulse.bindFilterForm = function (formId) {
  const form = document.getElementById(formId);
  if (!form) return;
  form.querySelectorAll('select').forEach(sel => {
    sel.addEventListener('change', () => form.submit());
  });
};


// ── File upload drag-and-drop ─────────────────────────────────────────────
(function () {
  const zone  = document.querySelector('.upload-zone');
  const input = document.getElementById('id_file');
  if (!zone || !input) return;

  zone.addEventListener('click', () => input.click());

  ['dragover', 'dragenter'].forEach(evt => {
    zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.add('dragover'); });
  });
  ['dragleave', 'drop'].forEach(evt => {
    zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.remove('dragover'); });
  });
  zone.addEventListener('drop', e => {
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      zone.querySelector('.upload-zone-name').textContent = file.name;
    }
  });
  input.addEventListener('change', () => {
    const nameEl = zone.querySelector('.upload-zone-name');
    if (nameEl && input.files.length) nameEl.textContent = input.files[0].name;
  });
})();


// ── Auto-dismiss alerts after 5 seconds ──────────────────────────────────
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    const bsAlert = new bootstrap.Alert(alert);
    bsAlert.close();
  }, 5000);
});
