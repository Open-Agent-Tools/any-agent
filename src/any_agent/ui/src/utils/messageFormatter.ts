/**
 * URL regex pattern that matches http/https URLs
 * Handles ports, query parameters, fragments, and various URL formats
 * More comprehensive pattern that handles modern URL structures
 */
const URL_REGEX = /https?:\/\/(?:[-\w.])+(?::[0-9]+)?(?:\/(?:[\w\/_.~!*'();:@&=+$,?#[\]-])*)?/g;

/**
 * Escapes HTML characters to prevent XSS attacks
 * @param text - The text to escape
 * @returns Escaped text safe for HTML
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Converts URLs in text to clickable HTML links with proper security attributes
 * @param text - The text containing potential URLs
 * @returns Text with URLs converted to HTML anchor tags
 */
function linkifyUrls(text: string): string {
  return text.replace(URL_REGEX, (url) => {
    // Remove trailing punctuation that shouldn't be part of the URL
    let cleanUrl = url.replace(/[.,;:!?)"'>]+$/, '');
    
    // Handle balanced parentheses - if URL ends with ) but has no opening (, remove the )
    if (cleanUrl.endsWith(')') && !cleanUrl.includes('(')) {
      cleanUrl = cleanUrl.slice(0, -1);
    }
    
    const trailingPunctuation = url.slice(cleanUrl.length);
    
    // Escape the URL for security (prevent XSS)
    const escapedUrl = escapeHtml(cleanUrl);
    
    return `<a href="${escapedUrl}" target="_blank" rel="noopener noreferrer" class="message-link" role="link" aria-label="Open ${escapedUrl} in new tab">${escapedUrl}</a>${trailingPunctuation}`;
  });
}

/**
 * Formats message content for display, handling markdown-style formatting
 * and converting URLs to clickable links
 * 
 * URL Processing Features:
 * - Automatically detects HTTP/HTTPS URLs in text
 * - Converts URLs to clickable <a> tags with target="_blank"
 * - Adds security attributes (rel="noopener noreferrer")
 * - Handles trailing punctuation correctly
 * - Supports complex URLs with query parameters, fragments, and ports
 * - Includes ARIA labels for accessibility
 * - Prevents XSS attacks through URL escaping
 * 
 * Example transformations:
 * Input:  "Visit https://example.com for details."
 * Output: "Visit <a href="https://example.com" target="_blank" rel="noopener noreferrer" class="message-link" role="link" aria-label="Open https://example.com in new tab">https://example.com</a> for details."
 */
export function formatMessageContent(text: string): string {
  if (!text) return '';
  
  // Debug logging to see what we're processing
  if (text.includes('_')) {
    console.log('🔍 Input text with underscores:', JSON.stringify(text));
  }
  
  let formatted = text;
  
  // Convert URLs to clickable links FIRST, before other formatting
  // This prevents URLs from being broken by other formatting rules
  formatted = linkifyUrls(formatted);
  
  // Handle bullet lists (lines starting with * or -)
  formatted = formatted.replace(/^[\s]*[*-]\s+(.+)$/gm, '<li>$1</li>');
  
  // Wrap consecutive list items in ul tags
  formatted = formatted.replace(/((<li>.*<\/li>\s*)+)/g, '<ul>$1</ul>');
  
  // Handle numbered lists (lines starting with numbers)
  formatted = formatted.replace(/^[\s]*(\d+\.)\s+(.+)$/gm, '<li>$2</li>');
  formatted = formatted.replace(/((<li>.*<\/li>\s*)+)/g, function(match: string) {
    if (!match.includes('<ul>')) {
      return '<ol>' + match + '</ol>';
    }
    return match;
  });
  
  // Handle code blocks (backticks) - but avoid touching links inside them
  formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
  formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // Handle bold and italic (escape asterisks properly) - but avoid touching links
  formatted = formatted.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  formatted = formatted.replace(/\*(.+?)\*/g, '<em>$1</em>');
  
  // Convert line breaks to proper spacing
  formatted = formatted.replace(/\n\n/g, '</p><p>');
  formatted = formatted.replace(/\n/g, '<br>');
  
  // Wrap in paragraphs if not already wrapped
  if (!formatted.includes('<p>') && !formatted.includes('<ul>') && !formatted.includes('<ol>')) {
    formatted = '<p>' + formatted + '</p>';
  }
  
  // Debug logging to see final output
  if (text.includes('_')) {
    console.log('✅ Output HTML with underscores:', JSON.stringify(formatted));
  }
  
  return formatted;
}

/**
 * Generates a cryptographically secure, unique session ID
 * Uses timestamp + crypto-strong randomness to ensure uniqueness
 */
export function generateSessionId(): string {
  const timestamp = Date.now().toString(36);
  
  // Use crypto.getRandomValues for cryptographically secure randomness
  const randomBytes = new Uint8Array(12); // 12 bytes = 96 bits of entropy
  crypto.getRandomValues(randomBytes);
  
  // Convert to base36 for URL-safe string
  const randomString = Array.from(randomBytes)
    .map(byte => byte.toString(36))
    .join('')
    .substring(0, 12); // Truncate to reasonable length
  
  return `session_${timestamp}_${randomString}`;
}

/**
 * Formats timestamp for display
 */
export function formatTimestamp(date: Date = new Date()): string {
  return date.toLocaleTimeString();
}

/**
 * Test utility function for URL linkification (development only)
 * Helps verify that URL detection and linking works correctly
 */
export function testUrlLinkification(): void {
  if (process.env.NODE_ENV === 'development') {
    const testCases = [
      'Check out https://example.com for more info.',
      'Visit http://docs.example.com/api and https://github.com/user/repo.',
      'The URL https://example.com/path?param=value#section looks interesting.',
      'Multiple URLs: https://site1.com, http://site2.com, and https://site3.com/path.',
      'URL at end: Visit https://example.com.',
      'URL with punctuation: Go to https://example.com, then continue.',
      'URL in parentheses: Check (https://example.com) for details.',
      'URL with port: https://localhost:3000/api/endpoint',
      'Complex URL: https://api.example.com/v2/users?id=123&sort=name#results',
      'URL with underscore: https://my_site.example.com/page_name',
    ];

    console.group('🔗 URL Linkification Test Results');
    testCases.forEach((testCase, index) => {
      console.log(`Test ${index + 1}:`, testCase);
      console.log('Result:', formatMessageContent(testCase));
      console.log('---');
    });
    console.groupEnd();
  }
}