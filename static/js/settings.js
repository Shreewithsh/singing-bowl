/**
 * Singing Bowl Export Desk - Settings JavaScript
 * Form submissions for SMTP, SerpApi, search parameters, outreach defaults, and connection testing.
 */

document.addEventListener('DOMContentLoaded', () => {
  const smtpForm = document.getElementById('smtp-form');
  if (smtpForm) {
    smtpForm.addEventListener('submit', saveSMTP);
  }

  const searchSettingsForm = document.getElementById('search-settings-form');
  if (searchSettingsForm) {
    searchSettingsForm.addEventListener('submit', saveSearchSettings);
  }

  const outreachForm = document.getElementById('outreach-form');
  if (outreachForm) {
    outreachForm.addEventListener('submit', saveSearchSettings);
  }
});

async function saveSMTP(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const payload = {};
  formData.forEach((val, key) => payload[key] = val);

  try {
    const res = await fetch('/api/settings/smtp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast('SMTP settings saved successfully!', 'success');
    } else {
      showToast('Failed to save SMTP settings', 'error');
    }
  } catch (err) {
    showToast('Network error saving SMTP settings', 'error');
  }
}

async function saveSearchSettings(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const payload = {};
  formData.forEach((val, key) => payload[key] = val);

  try {
    const res = await fetch('/api/settings/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast('Settings saved successfully!', 'success');
    } else {
      showToast('Failed to save settings', 'error');
    }
  } catch (err) {
    showToast('Network error saving settings', 'error');
  }
}

async function testSMTP() {
  const resDiv = document.getElementById('smtp-test-result');
  if (resDiv) {
    resDiv.classList.remove('hidden');
    resDiv.className = 'p-3 rounded-lg text-xs bg-gray-100 text-gray-700 flex items-center gap-2';
    resDiv.innerHTML = '<span class="loading-spinner border-gray-600 border-t-primary"></span> Testing SMTP connection...';
  }

  try {
    const res = await fetch('/api/settings/test-smtp', { method: 'POST' });
    const data = await res.json();

    if (resDiv) {
      if (data.success) {
        resDiv.className = 'p-3 rounded-lg text-xs bg-green-50 border border-green-200 text-green-800 flex items-center gap-2 font-medium';
        resDiv.innerHTML = '<i data-lucide="check-circle" class="w-4 h-4 text-green-600"></i> ' + data.message;
      } else {
        resDiv.className = 'p-3 rounded-lg text-xs bg-red-50 border border-red-200 text-red-800 flex items-center gap-2 font-medium';
        resDiv.innerHTML = '<i data-lucide="alert-circle" class="w-4 h-4 text-red-600"></i> ' + data.message;
      }
      lucide.createIcons();
    }
  } catch (err) {
    if (resDiv) {
      resDiv.className = 'p-3 rounded-lg text-xs bg-red-50 border border-red-200 text-red-800 flex items-center gap-2 font-medium';
      resDiv.innerHTML = '<i data-lucide="alert-circle" class="w-4 h-4 text-red-600"></i> Connection test failed: ' + err.message;
      lucide.createIcons();
    }
  }
}

function togglePasswordVis(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isPassword = input.type === 'password';
  input.type = isPassword ? 'text' : 'password';
}
