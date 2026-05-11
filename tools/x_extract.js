/* Tweet extractor for the Safari driver — runs in the page context.
 *
 * Matches the DOM that x.com renders for a profile page. The radar reads
 * the JSON this returns and merges it into data/manual_x/posts.json.
 *
 * Resilience strategy:
 *   - tweet_id and url come from the /status/<id> anchor; if missing,
 *     the article is skipped (avoid junk).
 *   - text prefers the dedicated tweetText container; falls back to
 *     article.innerText with a length cap.
 *   - author_handle is recovered from the first profile-style anchor
 *     (path is exactly /<one segment>).
 *   - timestamp comes from the <time datetime> element.
 *   - metrics: scrapes the like/retweet/reply group; supports k/M abbrev.
 *   - returns JSON string (do JavaScript in AppleScript can only pass
 *     primitives back).
 *
 * Safe to re-run as the page scrolls; the caller dedupes by tweet_id.
 */
(function () {
  function parseCount(txt) {
    if (!txt) return 0;
    var clean = String(txt).trim().replace(/,/g, '');
    var m = clean.match(/^([\d.]+)\s*([kKmM])?$/);
    if (!m) {
      var n = parseInt(clean, 10);
      return Number.isFinite(n) ? n : 0;
    }
    var num = parseFloat(m[1]);
    if (!Number.isFinite(num)) return 0;
    var suf = (m[2] || '').toLowerCase();
    if (suf === 'k') return Math.round(num * 1000);
    if (suf === 'm') return Math.round(num * 1000000);
    return Math.round(num);
  }

  function findMetric(article, testid) {
    var btn = article.querySelector('[data-testid="' + testid + '"]');
    if (!btn) return 0;
    var group = btn.closest('[role="group"]') || btn.parentElement;
    if (!group) return 0;
    var txt = group.querySelector('span[data-testid="app-text-transition-container"]');
    if (!txt) return 0;
    return parseCount(txt.innerText || '');
  }

  function authorFromArticle(article) {
    var anchors = article.querySelectorAll('a[role="link"][href]');
    for (var i = 0; i < anchors.length; i++) {
      var href = anchors[i].getAttribute('href') || '';
      var match = href.match(/^\/([A-Za-z0-9_]{1,30})$/);
      if (match) return match[1];
    }
    return '';
  }

  var articles = document.querySelectorAll('article[data-testid="tweet"]');
  var posts = [];
  var seen = {};

  for (var i = 0; i < articles.length; i++) {
    var article = articles[i];

    var permalink = '';
    var anchors = article.querySelectorAll('a[href*="/status/"]');
    for (var a = 0; a < anchors.length; a++) {
      var h = anchors[a].href;
      if (h && /\/status\/\d+/.test(h)) { permalink = h; break; }
    }
    if (!permalink) continue;
    var idm = permalink.match(/\/status\/(\d+)/);
    if (!idm) continue;
    var tweet_id = idm[1];
    if (seen[tweet_id]) continue;
    seen[tweet_id] = true;

    var textEl = article.querySelector('[data-testid="tweetText"]');
    var text = textEl ? textEl.innerText : (article.innerText || '').slice(0, 600);
    text = (text || '').trim();
    if (text.length < 15) continue;

    var timeEl = article.querySelector('time');
    var posted_at = timeEl ? timeEl.getAttribute('datetime') : null;

    var author = authorFromArticle(article);

    posts.push({
      tweet_id:      tweet_id,
      url:           permalink.replace(/\?[^#]*$/, ''),  // strip tracking params
      author_handle: author,
      text:          text,
      posted_at:     posted_at,
      likes:         findMetric(article, 'like'),
      retweets:      findMetric(article, 'retweet'),
      replies:       findMetric(article, 'reply'),
      collected_at:  new Date().toISOString()
    });
  }

  return JSON.stringify({
    page_url:  location.href,
    is_login_wall: /\/i\/flow\/login/.test(location.href) ||
                   !!document.querySelector('input[autocomplete="username"]'),
    count:     posts.length,
    posts:     posts
  });
})();
