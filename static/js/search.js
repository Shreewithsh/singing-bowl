/**
 * Singing Bowl Export Desk - Lead Search JavaScript
 * Manages search form submission, SSE/polling for live progress, and result rendering.
 */

let pollInterval = null;

document.addEventListener('DOMContentLoaded', () => {
  const searchForm = document.getElementById('search-form');
  if (searchForm) {
    searchForm.addEventListener('submit', handleSearchSubmit);
  }
});

async function handleSearchSubmit(e) {
  e.preventDefault();
  
  const keywords = document.getElementById('keywords').value.trim();
  const countries = document.getElementById('countries').value.trim();
  const limit = parseInt(document.getElementById('limit').value) || 20;
  const seed_urls = document.getElementById('seed-urls').value.trim();

  if (!keywords) {
    showToast('Please enter search keywords', 'warning');
    return;
  }

  // Update UI state
  setSearchUIState('progress');
  updateProgress(0, 'Initializing search...');
  updateStepCards('search');

  const btn = document.getElementById('search-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Searching...';

  try {
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keywords, countries, limit, seed_urls })
    });

    const data = await response.json();

    if (!response.ok) {
      showErrorState(data.error || 'Search request failed');
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="search" class="w-5 h-5"></i> Search Leads';
      lucide.createIcons();
      return;
    }

    // Poll for status
    startPollingSearchStatus();

  } catch (err) {
    showErrorState('Network error occurred: ' + err.message);
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="search" class="w-5 h-5"></i> Search Leads';
    lucide.createIcons();
  }
}

function startPollingSearchStatus() {
  if (pollInterval) clearInterval(pollInterval);

  pollInterval = setInterval(async () => {
    try {
      const res = await fetch('/api/search/status');
      if (!res.ok) return;
      const status = await res.json();

      updateProgress(status.progress || 0, status.message || '');

      // Update step highlights
      if (status.progress < 20) {
        updateStepCards('search');
      } else if (status.progress < 80) {
        updateStepCards('scrape');
      } else {
        updateStepCards('import');
      }

      if (!status.running) {
        clearInterval(pollInterval);
        pollInterval = null;

        const btn = document.getElementById('search-btn');
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="search" class="w-5 h-5"></i> Search Leads';
        lucide.createIcons();

        if (status.error) {
          showErrorState(status.error);
        } else if (status.results) {
          showResultsState(status.results);
        }
      }
    } catch (e) {
      console.error('Status poll error:', e);
    }
  }, 1000);
}

function updateProgress(percent, message) {
  const bar = document.getElementById('progress-bar');
  const pctText = document.getElementById('progress-pct');
  const msgText = document.getElementById('progress-msg');

  if (bar) bar.style.width = `${percent}%`;
  if (pctText) pctText.textContent = `${percent}%`;
  if (msgText) msgText.textContent = message;
}

function updateStepCards(activeStep) {
  const steps = ['search', 'scrape', 'import'];
  const activeIdx = steps.indexOf(activeStep);

  steps.forEach((step, idx) => {
    const card = document.getElementById(`step-${step}`);
    if (!card) return;
    card.classList.remove('active', 'done');
    if (idx < activeIdx) {
      card.classList.add('done');
    } else if (idx === activeIdx) {
      card.classList.add('active');
    }
  });
}

function setSearchUIState(state) {
  const states = ['idle', 'progress', 'results', 'error'];
  states.forEach(s => {
    const el = document.getElementById(`${s}-state`);
    if (el) el.classList.toggle('hidden', s !== state);
  });
}

function showResultsState(results) {
  setSearchUIState('results');

  document.getElementById('r-websites').textContent = results.websites_found || 0;
  document.getElementById('r-emails').textContent = results.emails_extracted || 0;
  document.getElementById('r-imported').textContent = results.imported || 0;
  document.getElementById('r-duplicates').textContent = results.duplicates || 0;

  showToast(`Found ${results.imported} new unique leads!`, 'success');
}

function showErrorState(message) {
  setSearchUIState('error');
  const msgEl = document.getElementById('error-msg');
  if (msgEl) msgEl.textContent = message;
  showToast('Search encountered an error', 'error');
}

function resetSearchUI() {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
  setSearchUIState('idle');
  const btn = document.getElementById('search-btn');
  if (btn) {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="search" class="w-5 h-5"></i> Search Leads';
    lucide.createIcons();
  }
}
