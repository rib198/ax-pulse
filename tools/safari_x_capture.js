JSON.stringify({
  page_url: location.href,
  page_title: document.title,
  host: location.hostname,
  items: Array.from(document.querySelectorAll('article[data-testid="tweet"]')).map((article) => {
    const text = article.innerText || '';
    const link = Array.from(article.querySelectorAll('a[href*="/status/"]')).map((anchor) => anchor.href).find(Boolean) || location.href;
    return { url: link, text, source: 'safari_visible' };
  }).filter((item) => item.text.trim().length > 20)
});
