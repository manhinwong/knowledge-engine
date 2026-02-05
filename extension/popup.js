// Popup logic for Knowledge Engine extension

const statusDiv = document.getElementById('status-message');
const saveBtn = document.getElementById('save-btn');
const pdfBtn = document.getElementById('pdf-btn');
const fileInput = document.getElementById('file-input');
const serverUrlInput = document.getElementById('server-url');
const serverStatus = document.getElementById('server-status');
const pageTitleEl = document.getElementById('page-title');
const pageUrlEl = document.getElementById('page-url');
const recentList = document.getElementById('recent-list');

let currentTab = null;
let serverUrl = 'http://localhost:8284';

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  // Load saved server URL
  const stored = await chrome.storage.local.get(['serverUrl', 'recentSaves']);
  if (stored.serverUrl) {
    serverUrl = stored.serverUrl;
    serverUrlInput.value = serverUrl;
  }

  // Display recent saves
  if (stored.recentSaves && stored.recentSaves.length > 0) {
    stored.recentSaves.slice(0, 5).forEach(item => {
      const div = document.createElement('div');
      div.className = 'recent-item';
      div.textContent = item.title;
      div.title = item.url;
      recentList.appendChild(div);
    });
  } else {
    recentList.innerHTML = '<div class="recent-item" style="color: #999;">No recent saves</div>';
  }

  // Get current tab info
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTab = tabs[0];

  if (currentTab) {
    pageTitleEl.textContent = currentTab.title || 'Untitled';
    pageUrlEl.textContent = currentTab.url || '';
    pageUrlEl.title = currentTab.url || '';
  }

  // Check server health
  checkServerHealth();
});

// Save server URL when changed
serverUrlInput.addEventListener('change', async () => {
  serverUrl = serverUrlInput.value;
  await chrome.storage.local.set({ serverUrl });
  checkServerHealth();
});

// Check if server is running
async function checkServerHealth() {
  try {
    const response = await fetch(`${serverUrl}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.ok) {
      serverStatus.className = 'server-status online';
      saveBtn.disabled = false;
      pdfBtn.disabled = false;
    } else {
      throw new Error('Server unhealthy');
    }
  } catch (error) {
    serverStatus.className = 'server-status offline';
    showStatus('Server offline. Please start the Knowledge Engine server.', 'error');
    saveBtn.disabled = true;
    pdfBtn.disabled = true;
  }
}

// Save current page
saveBtn.addEventListener('click', async () => {
  if (!currentTab) return;

  showStatus('Processing article...', 'processing');
  saveBtn.disabled = true;

  try {
    // Try to extract content from page using content script
    const response = await chrome.tabs.sendMessage(currentTab.id, { action: 'extract' });

    let processResult;

    if (response && response.content) {
      // Send extracted HTML to server
      processResult = await fetch(`${serverUrl}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'html',
          content: response.content,
          metadata: {
            title: response.title || currentTab.title,
            url: currentTab.url,
            author: response.author,
            date: response.date
          }
        })
      });
    } else {
      // Fallback: send URL to server
      processResult = await fetch(`${serverUrl}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'url',
          content: currentTab.url
        })
      });
    }

    if (!processResult.ok) {
      throw new Error(`Server error: ${processResult.statusText}`);
    }

    const data = await processResult.json();

    // Add to recent saves
    await addToRecent({
      title: currentTab.title,
      url: currentTab.url,
      timestamp: new Date().toISOString()
    });

    showStatus('Saved successfully!', 'success');
    saveBtn.disabled = false;

    // Auto-hide success message after 3 seconds
    setTimeout(() => {
      hideStatus();
    }, 3000);

  } catch (error) {
    showStatus(`Error: ${error.message}`, 'error');
    saveBtn.disabled = false;
  }
});

// PDF upload handler
pdfBtn.addEventListener('click', () => {
  fileInput.click();
});

fileInput.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  showStatus('Processing PDF...', 'processing');
  pdfBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${serverUrl}/upload-pdf`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.statusText}`);
    }

    const data = await response.json();

    // Add to recent saves
    await addToRecent({
      title: file.name,
      url: 'local-pdf',
      timestamp: new Date().toISOString()
    });

    showStatus('PDF processed successfully!', 'success');
    pdfBtn.disabled = false;

    // Auto-hide success message
    setTimeout(() => {
      hideStatus();
    }, 3000);

  } catch (error) {
    showStatus(`Error: ${error.message}`, 'error');
    pdfBtn.disabled = false;
  }

  // Reset file input
  fileInput.value = '';
});

// Status display helpers
function showStatus(message, type) {
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`;
  statusDiv.style.display = 'block';

  if (type === 'processing') {
    const spinner = document.createElement('span');
    spinner.className = 'spinner';
    statusDiv.prepend(spinner);
  }
}

function hideStatus() {
  statusDiv.style.display = 'none';
}

// Add to recent saves
async function addToRecent(item) {
  const stored = await chrome.storage.local.get(['recentSaves']);
  const recent = stored.recentSaves || [];

  // Add to front, keep last 10
  recent.unshift(item);
  const trimmed = recent.slice(0, 10);

  await chrome.storage.local.set({ recentSaves: trimmed });

  // Update display
  recentList.innerHTML = '';
  trimmed.slice(0, 5).forEach(save => {
    const div = document.createElement('div');
    div.className = 'recent-item';
    div.textContent = save.title;
    div.title = save.url;
    recentList.appendChild(div);
  });
}
