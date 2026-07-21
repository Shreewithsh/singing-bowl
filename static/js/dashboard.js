/**
 * Singing Bowl Export Desk - Dashboard JavaScript
 * Handles global utilities, stats refresh, and shared functions
 */

// Auto-refresh stats every 30 seconds on dashboard
(function() {
  if (document.getElementById('stat-total')) {
    refreshDashboardStats();
    setInterval(refreshDashboardStats, 30000);
  }
})();

async function refreshDashboardStats() {
  try {
    const res = await fetch('/api/reports/stats');
    if (!res.ok) return;
    const data = await res.json();
    
    const setEl = (id, val) => {
      const el = document.getElementById(id);
      if (el && el.textContent !== String(val)) {
        el.textContent = val;
        el.parentElement?.classList.add('animate-pulse');
        setTimeout(() => el.parentElement?.classList.remove('animate-pulse'), 1000);
      }
    };
    
    setEl('stat-total', data.total || 0);
    setEl('stat-contacted', data.contacted || 0);
    setEl('stat-sent', data.sent || 0);
    setEl('stat-failed', data.failed || 0);
  } catch(e) { /* silent */ }
}
