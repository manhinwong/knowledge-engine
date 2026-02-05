// Background service worker for Knowledge Engine extension

// Keep track of processing queue
const processingQueue = [];
let isProcessing = false;

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'process') {
    queueProcessing(request.data);
    sendResponse({ queued: true });
  } else if (request.action === 'getQueue') {
    sendResponse({ queue: processingQueue, processing: isProcessing });
  }
  return true;
});

// Queue processing requests
function queueProcessing(data) {
  processingQueue.push(data);
  updateBadge();
  processQueue();
}

// Process queue one at a time
async function processQueue() {
  if (isProcessing || processingQueue.length === 0) {
    return;
  }

  isProcessing = true;
  const item = processingQueue.shift();
  updateBadge();

  try {
    // Process would happen here
    // For now, this is handled synchronously in popup.js
    console.log('Processing:', item);
  } catch (error) {
    console.error('Processing error:', error);
  } finally {
    isProcessing = false;
    updateBadge();
    processQueue(); // Process next item
  }
}

// Update extension badge with queue count
function updateBadge() {
  const count = processingQueue.length;
  if (count > 0) {
    chrome.action.setBadgeText({ text: count.toString() });
    chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
  } else {
    chrome.action.setBadgeText({ text: '' });
  }
}

// Initialize
chrome.action.setBadgeText({ text: '' });
