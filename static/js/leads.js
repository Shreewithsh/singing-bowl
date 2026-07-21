/**
 * Singing Bowl Export Desk - Lead Database JavaScript
 * Manages email composing, previewing, sending, lead listing, search, filter, bulk operations & pagination.
 */

let currentPage = 1;
let selectedLeadIds = new Set();
let campaignPollInterval = null;

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('leads-tbody')) {
    loadLeads(1);
    setupEventListeners();
  }
});

function setupEventListeners() {
  const searchInput = document.getElementById('table-search');
  if (searchInput) {
    let timeout = null;
    searchInput.addEventListener('input', () => {
      clearTimeout(timeout);
      timeout = setTimeout(() => loadLeads(1), 300);
    });
  }

  const countryFilter = document.getElementById('country-filter');
  if (countryFilter) {
    countryFilter.addEventListener('change', () => loadLeads(1));
  }

  const contactedFilter = document.getElementById('contacted-filter');
  if (contactedFilter) {
    contactedFilter.addEventListener('change', () => loadLeads(1));
  }
}

async function loadLeads(page = 1) {
  currentPage = page;
  const search = document.getElementById('table-search')?.value.trim() || '';
  const country = document.getElementById('country-filter')?.value || '';
  const contacted = document.getElementById('contacted-filter')?.value || '';

  const tbody = document.getElementById('leads-tbody');
  if (tbody) {
    tbody.innerHTML = `
      <tr>
        <td colspan="9" class="py-8 text-center text-gray-400">
          <div class="flex items-center justify-center gap-2">
            <span class="loading-spinner border-gray-400 border-t-primary"></span> Loading leads...
          </div>
        </td>
      </tr>`;
  }

  try {
    const url = `/api/leads?page=${page}&per_page=25&search=${encodeURIComponent(search)}&country=${encodeURIComponent(country)}&contacted=${encodeURIComponent(contacted)}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load leads');
    const data = await res.json();

    renderLeadsTable(data.leads);
    renderPagination(data);
  } catch (err) {
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="9" class="py-8 text-center text-red-500 font-medium">
            Error loading leads: ${err.message}
          </td>
        </tr>`;
    }
  }
}

function renderLeadsTable(leads) {
  const tbody = document.getElementById('leads-tbody');
  if (!tbody) return;

  if (!leads || leads.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="9" class="py-12 text-center text-gray-400">
          No leads found matching your criteria.
        </td>
      </tr>`;
    return;
  }

  tbody.innerHTML = leads.map(lead => {
    const isChecked = selectedLeadIds.has(lead.id);
    const scoreColor = lead.score >= 70 ? 'score-high' : lead.score >= 40 ? 'score-mid' : 'score-low';
    const statusBadge = lead.contacted 
      ? '<span class="badge badge-success">Contacted</span>'
      : '<span class="badge badge-gray">Not Contacted</span>';

    return `
      <tr data-id="${lead.id}">
        <td>
          <input type="checkbox" class="lead-checkbox rounded" data-id="${lead.id}" ${isChecked ? 'checked' : ''} onchange="toggleLeadSelect(${lead.id}, this.checked)" />
        </td>
        <td class="font-medium text-gray-900 truncate-cell" title="${escapeHtml(lead.owner_name)}">${escapeHtml(lead.owner_name) || '<span class="text-gray-300">—</span>'}</td>
        <td class="font-medium text-gray-900 truncate-cell" title="${escapeHtml(lead.business_name)}">${escapeHtml(lead.business_name) || '<span class="text-gray-300">—</span>'}</td>
        <td class="text-gray-700 truncate-cell" title="${escapeHtml(lead.email)}">
          <a href="mailto:${escapeHtml(lead.email)}" class="hover:text-primary hover:underline">${escapeHtml(lead.email)}</a>
        </td>
        <td class="text-gray-600 text-xs">${escapeHtml(lead.phone) || '<span class="text-gray-300">—</span>'}</td>
        <td class="text-gray-600 text-xs">${escapeHtml(lead.country) || '<span class="text-gray-300">—</span>'}</td>
        <td class="${scoreColor} text-xs text-center">${lead.score}</td>
        <td>${statusBadge}</td>
        <td class="text-right">
          <div class="flex items-center justify-end gap-1">
            <button onclick="sendSingleLeadEmail(${lead.id})" class="btn-icon-green" title="Send Email">
              <i data-lucide="send" class="w-3.5 h-3.5"></i>
            </button>
            <button onclick="deleteSingleLead(${lead.id})" class="btn-icon-red" title="Delete Lead">
              <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  lucide.createIcons();
  updateBulkDeleteBtn();
}

function renderPagination(data) {
  const info = document.getElementById('pagination-info');
  const controls = document.getElementById('pagination-controls');

  if (info) {
    const start = (data.page - 1) * data.per_page + 1;
    const end = Math.min(data.page * data.per_page, data.total);
    info.textContent = data.total > 0 
      ? `Showing ${start}–${end} of ${data.total} leads`
      : '0 leads found';
  }

  if (controls) {
    if (data.pages <= 1) {
      controls.innerHTML = '';
      return;
    }

    let buttons = [];
    if (data.page > 1) {
      buttons.push(`<button onclick="loadLeads(${data.page - 1})" class="btn-secondary text-xs px-2.5 py-1">Prev</button>`);
    }

    for (let i = 1; i <= data.pages; i++) {
      if (i === 1 || i === data.pages || Math.abs(i - data.page) <= 1) {
        const active = i === data.page ? 'btn-primary' : 'btn-secondary';
        buttons.push(`<button onclick="loadLeads(${i})" class="${active} text-xs px-2.5 py-1">${i}</button>`);
      } else if (buttons[buttons.length - 1] !== '<span class="text-gray-400">...</span>') {
        buttons.push('<span class="text-gray-400">...</span>');
      }
    }

    if (data.page < data.pages) {
      buttons.push(`<button onclick="loadLeads(${data.page + 1})" class="btn-secondary text-xs px-2.5 py-1">Next</button>`);
    }

    controls.innerHTML = buttons.join('');
  }
}

/* ─── Selection Logic ────────────────────────────────────────────────────────── */
function toggleLeadSelect(id, isChecked) {
  if (isChecked) {
    selectedLeadIds.add(id);
  } else {
    selectedLeadIds.delete(id);
  }
  updateBulkDeleteBtn();
}

function toggleHeaderCheck(headerCb) {
  const checkboxes = document.querySelectorAll('.lead-checkbox');
  checkboxes.forEach(cb => {
    cb.checked = headerCb.checked;
    const id = parseInt(cb.getAttribute('data-id'));
    if (headerCb.checked) selectedLeadIds.add(id);
    else selectedLeadIds.delete(id);
  });
  updateBulkDeleteBtn();
}

function toggleSelectAll() {
  const checkboxes = document.querySelectorAll('.lead-checkbox');
  const allChecked = Array.from(checkboxes).every(cb => cb.checked);
  const headerCb = document.getElementById('header-checkbox');

  if (headerCb) headerCb.checked = !allChecked;
  checkboxes.forEach(cb => {
    cb.checked = !allChecked;
    const id = parseInt(cb.getAttribute('data-id'));
    if (!allChecked) selectedLeadIds.add(id);
    else selectedLeadIds.delete(id);
  });
  updateBulkDeleteBtn();
}

function updateBulkDeleteBtn() {
  const btn = document.getElementById('bulk-delete-btn');
  const countEl = document.getElementById('selected-count');
  if (btn && countEl) {
    countEl.textContent = selectedLeadIds.size;
    btn.classList.toggle('hidden', selectedLeadIds.size === 0);
  }
}

/* ─── Bulk Operations ────────────────────────────────────────────────────────── */
async function bulkDeleteSelected() {
  if (selectedLeadIds.size === 0) return;
  if (!confirm(`Are you sure you want to delete ${selectedLeadIds.size} selected leads?`)) return;

  try {
    const res = await fetch('/api/leads/bulk-delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: Array.from(selectedLeadIds) })
    });
    if (res.ok) {
      showToast(`Deleted ${selectedLeadIds.size} leads`, 'success');
      selectedLeadIds.clear();
      loadLeads(currentPage);
    } else {
      showToast('Failed to delete leads', 'error');
    }
  } catch (e) {
    showToast('Network error', 'error');
  }
}

async function deleteSingleLead(id) {
  if (!confirm('Are you sure you want to delete this lead?')) return;
  try {
    const res = await fetch(`/api/leads/${id}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Lead deleted', 'success');
      selectedLeadIds.delete(id);
      loadLeads(currentPage);
    } else {
      showToast('Failed to delete lead', 'error');
    }
  } catch (e) {
    showToast('Network error', 'error');
  }
}

/* ─── Email Operations ───────────────────────────────────────────────────────── */
async function saveDraft() {
  const subject = document.getElementById('email-subject')?.value || '';
  const body = document.getElementById('email-body')?.value || '';

  try {
    const res = await fetch('/api/leads/save-template', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject, body })
    });
    if (res.ok) showToast('Email draft saved', 'success');
    else showToast('Failed to save draft', 'error');
  } catch (e) {
    showToast('Network error', 'error');
  }
}

async function previewEmail() {
  const subject = document.getElementById('email-subject')?.value || '';
  const body = document.getElementById('email-body')?.value || '';

  try {
    const res = await fetch('/api/leads/preview-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject, body })
    });
    if (!res.ok) throw new Error('Preview failed');
    const data = await res.json();

    document.getElementById('preview-subject').textContent = data.subject;
    const iframe = document.getElementById('preview-iframe');
    iframe.srcdoc = data.body;

    document.getElementById('preview-modal').classList.remove('hidden');
  } catch (e) {
    showToast('Failed to generate email preview', 'error');
  }
}

async function sendSingleLeadEmail(leadId) {
  const subject = document.getElementById('email-subject')?.value || '';
  const body = document.getElementById('email-body')?.value || '';

  if (!confirm('Send email to this contact now?')) return;

  try {
    showToast('Sending email...', 'info');
    const res = await fetch(`/api/leads/${leadId}/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject, body })
    });
    const data = await res.json();

    if (res.ok) {
      showToast(data.message || 'Email sent successfully!', 'success');
      loadLeads(currentPage);
    } else {
      showToast(data.error || 'Failed to send email', 'error');
    }
  } catch (e) {
    showToast('Network error during send', 'error');
  }
}

async function sendBulkEmail() {
  const subject = document.getElementById('email-subject')?.value || '';
  const body = document.getElementById('email-body')?.value || '';

  if (!confirm('Start bulk outreach campaign for all uncontacted leads?')) return;

  const btn = document.getElementById('send-bulk-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Starting...';

  try {
    const res = await fetch('/api/leads/send-bulk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subject, body })
    });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.error || 'Failed to start campaign', 'error');
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="send" class="w-3.5 h-3.5"></i> Send Bulk Email';
      lucide.createIcons();
      return;
    }

    showToast(`Bulk campaign started for ${data.total} leads`, 'success');
    startPollingCampaignStatus();

  } catch (e) {
    showToast('Network error starting campaign', 'error');
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="send" class="w-3.5 h-3.5"></i> Send Bulk Email';
    lucide.createIcons();
  }
}

function startPollingCampaignStatus() {
  const banner = document.getElementById('campaign-banner');
  if (banner) banner.classList.remove('hidden');

  if (campaignPollInterval) clearInterval(campaignPollInterval);

  campaignPollInterval = setInterval(async () => {
    try {
      const res = await fetch('/api/leads/email-status');
      if (!res.ok) return;
      const status = await res.json();

      document.getElementById('camp-sent').textContent = status.sent || 0;
      document.getElementById('camp-failed').textContent = status.failed || 0;
      document.getElementById('camp-skipped').textContent = status.skipped || 0;
      document.getElementById('camp-current').textContent = status.current || 0;
      document.getElementById('camp-total').textContent = status.total || 0;
      document.getElementById('camp-current-email').textContent = status.current_email || 'Finished';

      const pct = status.total > 0 ? Math.round((status.current / status.total) * 100) : 0;
      document.getElementById('camp-progress-bar').style.width = `${pct}%`;

      if (!status.running) {
        clearInterval(campaignPollInterval);
        campaignPollInterval = null;

        const btn = document.getElementById('send-bulk-btn');
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i data-lucide="send" class="w-3.5 h-3.5"></i> Send Bulk Email';
          lucide.createIcons();
        }

        showToast(`Campaign complete! Sent: ${status.sent}, Failed: ${status.failed}`, 'success');
        loadLeads(currentPage);
      }
    } catch (e) {
      console.error('Campaign poll error:', e);
    }
  }, 1500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
