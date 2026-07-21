/**
 * Singing Bowl Export Desk - Reports JavaScript
 * Fetches analytics, renders Chart.js charts, and handles CSV export.
 */

let dailyChart = null;
let countryChart = null;

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('dailySentChart')) {
    loadReportsData();
  }
});

async function loadReportsData() {
  try {
    const res = await fetch('/api/reports/stats');
    if (!res.ok) throw new Error('Failed to fetch analytics');
    const data = await res.json();

    // Summary metrics
    document.getElementById('r-total').textContent = data.total || 0;
    document.getElementById('r-contacted').textContent = data.contacted || 0;
    document.getElementById('r-sent').textContent = data.sent || 0;
    document.getElementById('r-rate').textContent = `${data.success_rate || 0}%`;
    document.getElementById('r-failed').textContent = data.failed || 0;

    // Daily sent chart
    renderDailyChart(data.daily_sent || []);

    // Country chart
    renderCountryChart(data.countries || []);

    // Campaign table
    renderCampaignsTable(data.campaigns || []);

  } catch (err) {
    showToast('Failed to load report metrics: ' + err.message, 'error');
  }
}

function renderDailyChart(dailyData) {
  const ctx = document.getElementById('dailySentChart')?.getContext('2d');
  if (!ctx) return;

  if (dailyChart) dailyChart.destroy();

  const labels = dailyData.map(d => d.date);
  const counts = dailyData.map(d => d.count);

  dailyChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Emails Sent',
        data: counts,
        borderColor: '#16A34A',
        backgroundColor: 'rgba(22, 163, 74, 0.08)',
        borderWidth: 2.5,
        fill: true,
        tension: 0.35,
        pointBackgroundColor: '#16A34A',
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { precision: 0 },
          grid: { color: 'rgba(229, 231, 235, 0.5)' }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

function renderCountryChart(countryData) {
  const ctx = document.getElementById('countryChart')?.getContext('2d');
  if (!ctx) return;

  if (countryChart) countryChart.destroy();

  const colors = [
    '#16A34A', '#2563EB', '#D97706', '#9333EA', '#DC2626',
    '#0D9488', '#EA580C', '#4F46E5', '#0284C7', '#65A30D'
  ];

  const labels = countryData.map(c => c.country || 'Unknown');
  const counts = countryData.map(c => c.count);

  countryChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: counts,
        backgroundColor: colors.slice(0, counts.length),
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      cutout: '65%'
    }
  });

  // Custom legend
  const legendEl = document.getElementById('country-legend');
  if (legendEl) {
    legendEl.innerHTML = countryData.slice(0, 5).map((c, i) => `
      <div class="flex items-center justify-between text-xs">
        <div class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full" style="background-color: ${colors[i]}"></span>
          <span class="text-gray-700 font-medium">${c.country || 'Unknown'}</span>
        </div>
        <span class="text-gray-500 font-semibold">${c.count}</span>
      </div>
    `).join('');
  }
}

function renderCampaignsTable(campaigns) {
  const tbody = document.getElementById('campaign-tbody');
  if (!tbody) return;

  if (!campaigns || campaigns.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="py-8 text-center text-gray-400">
          No campaigns recorded yet.
        </td>
      </tr>`;
    return;
  }

  tbody.innerHTML = campaigns.map(c => {
    const statusColor = c.status === 'completed' 
      ? 'badge-success' 
      : c.status === 'running' ? 'badge-warning' : 'badge-gray';

    return `
      <tr>
        <td class="font-medium text-gray-900">${escapeHtml(c.name)}</td>
        <td class="text-gray-600 truncate-cell" title="${escapeHtml(c.subject)}">${escapeHtml(c.subject)}</td>
        <td class="text-center font-semibold text-green-700">${c.total_sent}</td>
        <td class="text-center font-semibold text-red-600">${c.total_failed}</td>
        <td class="text-center text-gray-500">${c.total_skipped}</td>
        <td class="text-center"><span class="badge ${statusColor}">${c.status}</span></td>
        <td class="text-xs text-gray-400">${c.created_at}</td>
      </tr>
    `;
  }).join('');
}

function exportReportCSV() {
  window.location.href = '/api/export/csv';
}
