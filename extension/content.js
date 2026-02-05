// Content script for extracting article content from web pages

// Listen for extraction requests from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extract') {
    extractArticleContent().then(sendResponse);
    return true; // Keep message channel open for async response
  }
});

async function extractArticleContent() {
  try {
    // Use Readability-like extraction
    const article = extractMainContent();

    if (!article) {
      return null;
    }

    return {
      title: article.title,
      author: article.author,
      date: article.date,
      content: article.content
    };
  } catch (error) {
    console.error('Content extraction error:', error);
    return null;
  }
}

function extractMainContent() {
  // Try to extract metadata
  const title = document.title || extractMetaTag('og:title') || extractMetaTag('twitter:title');

  const author = extractMetaTag('author') ||
                extractMetaTag('article:author') ||
                extractMetaTag('twitter:creator');

  const date = extractMetaTag('article:published_time') ||
              extractMetaTag('datePublished') ||
              extractMetaTag('publishdate');

  // Extract main content
  let content = '';

  // Try common article containers
  const selectors = [
    'article',
    '[role="main"]',
    'main',
    '.article-content',
    '.post-content',
    '.entry-content',
    '#content',
    '.content'
  ];

  for (const selector of selectors) {
    const element = document.querySelector(selector);
    if (element) {
      content = cleanText(element);
      if (content.split(/\s+/).length > 100) {
        break; // Found substantial content
      }
    }
  }

  // Fallback: get body text
  if (!content || content.split(/\s+/).length < 100) {
    content = cleanText(document.body);
  }

  return {
    title,
    author,
    date,
    content: content.slice(0, 15000) // Limit size
  };
}

function extractMetaTag(name) {
  // Try property
  let tag = document.querySelector(`meta[property="${name}"]`);
  if (tag) return tag.getAttribute('content');

  // Try name
  tag = document.querySelector(`meta[name="${name}"]`);
  if (tag) return tag.getAttribute('content');

  return null;
}

function cleanText(element) {
  // Clone to avoid modifying the page
  const clone = element.cloneNode(true);

  // Remove unwanted elements
  const unwanted = clone.querySelectorAll(
    'script, style, nav, header, footer, aside, .ad, .advertisement, .social-share, [role="complementary"]'
  );
  unwanted.forEach(el => el.remove());

  // Get text with basic formatting
  let text = clone.innerText || clone.textContent || '';

  // Clean up whitespace
  text = text.replace(/\n{3,}/g, '\n\n').trim();

  return text;
}
