#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse
import html
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from x_manual_collect import POSTS_FILE, add_signal, load_json


PORT = 8020


BOOKMARKLET = """javascript:(()=>{const t=(window.getSelection&&String(window.getSelection()))||document.title||'';const u=location.href;open('http://127.0.0.1:8020/add?source=for_you&url='+encodeURIComponent(u)+'&text='+encodeURIComponent(t),'_blank','width=560,height=520');})();"""

BULK_BOOKMARKLET = """javascript:(async()=>{const posts=[...document.querySelectorAll('article[data-testid="tweet"]')].map(a=>{const txt=a.innerText||'';const link=[...a.querySelectorAll('a[href*="/status/"]')].map(x=>x.href).find(Boolean)||location.href;return{url:link,text:txt,source:'visible_feed'}}).filter(x=>x.text.trim().length>20);if(!posts.length){alert('لم أجد تغريدات ظاهرة. افتح X timeline أو search ثم جرّب.');return}try{const r=await fetch('http://127.0.0.1:8020/bulk',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({items:posts})});const j=await r.json();alert('AX Pulse: تم حفظ '+j.added+' من '+posts.length+' تغريدة ظاهرة.')}catch(e){alert('لم أستطع الاتصال بأداة AX. تأكد أن start-x-capture.command يعمل.')}})();"""

AUTO_BOOKMARKLET = """javascript:(()=>{if(window.__axCollector){window.__axCollector.stop();return}const box=document.createElement('div');box.style='position:fixed;z-index:999999;top:16px;right:16px;background:#071007;color:#eaffea;border:1px solid #7cff6b;border-radius:10px;padding:12px 14px;font:14px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;box-shadow:0 8px 28px #0008;direction:rtl;max-width:280px';box.innerHTML='<b>AX يجمع التغريدات...</b><div id=\"axc\">0 محفوظة</div><button id=\"axs\" style=\"margin-top:8px;background:#7cff6b;color:#071007;border:0;border-radius:7px;padding:6px 10px;font-weight:700\">إيقاف</button>';document.body.appendChild(box);let seen=new Set(),saved=0,ticks=0,stopped=false;async function collect(){const posts=[...document.querySelectorAll('article[data-testid=\"tweet\"]')].map(a=>{const txt=a.innerText||'';const link=[...a.querySelectorAll('a[href*=\"/status/\"]')].map(x=>x.href).find(Boolean)||'';return{url:link,text:txt,source:'auto_feed'}}).filter(x=>x.url&&x.text.trim().length>20&&!seen.has(x.url));posts.forEach(p=>seen.add(p.url));if(posts.length){try{const r=await fetch('http://127.0.0.1:8020/bulk',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({items:posts})});const j=await r.json();saved+=j.added||0;document.getElementById('axc').textContent=saved+' محفوظة · '+seen.size+' شوهدت'}catch(e){document.getElementById('axc').textContent='تعذر الاتصال بأداة AX'}}}window.scrollBy(0,Math.floor(window.innerHeight*.82));ticks++;if(ticks>=18)stop()}function stop(){if(stopped)return;stopped=true;clearInterval(timer);box.querySelector('b').textContent='انتهى جمع AX';document.getElementById('axc').textContent=saved+' محفوظة من '+seen.size+' تغريدة ظاهرة';setTimeout(()=>box.remove(),6500);window.__axCollector=null}box.querySelector('#axs').onclick=stop;window.__axCollector={stop};collect();const timer=setInterval(collect,2200);})();"""


def page(body):
    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<meta charset="utf-8">
<title>AX X Capture</title>
<style>
body{{margin:0;background:#090a0d;color:#f5f7f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.7}}
main{{max-width:860px;margin:auto;padding:28px}}
.card{{border:1px solid rgba(255,255,255,.1);background:#111317;border-radius:10px;padding:18px;margin:14px 0}}
a.button,button{{display:inline-block;background:#7cff6b;color:#071007;border:0;border-radius:7px;padding:9px 14px;font-weight:700;text-decoration:none}}
textarea,input{{width:100%;box-sizing:border-box;background:#090a0d;color:#f5f7f8;border:1px solid rgba(255,255,255,.12);border-radius:7px;padding:10px}}
textarea.code{{direction:ltr;unicode-bidi:embed;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}}
small,p{{color:#9aa2ad}} code{{direction:ltr;unicode-bidi:embed;color:#7cff6b}}
.item{{border-top:1px solid rgba(255,255,255,.08);padding:12px 0}}
</style>
<main>{body}</main>"""


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/add":
            self.handle_add(parsed)
            return
        self.handle_home()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/bulk":
            self.handle_bulk()
            return
        if parsed.path == "/paste":
            self.handle_paste()
            return
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        params = parse_qs(raw)
        text = params.get("text", [""])[0]
        source = params.get("source", ["manual_page"])[0]
        added, message, _item = add_signal(text, source=source)
        self.respond(page(f"<div class='card'><h1>{html.escape(message)}</h1><p>يمكنك إغلاق هذه النافذة والرجوع إلى X.</p><p><a class='button' href='/'>عرض المحفوظات</a></p></div>"))

    def handle_paste(self):
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        params = parse_qs(raw)
        text = params.get("text", [""])[0]
        chunks = split_pasted_x_text(text)
        added = 0
        for chunk in chunks:
            ok, _message, _saved = add_signal(chunk, source="pasted_feed")
            if ok:
                added += 1
        self.respond(page(f"<div class='card'><h1>تم استخراج {added} إشارة</h1><p>من نص الصفحة الملصوق. إذا كان الرقم قليلًا، جرّب نسخ الصفحة بعد تمرير X قليلًا.</p><p><a class='button' href='/'>رجوع</a></p></div>"))

    def handle_bulk(self):
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self.respond_json({"error": "invalid_json"}, 400)
            return
        added = 0
        skipped = 0
        for item in payload.get("items", []):
            text = ((item.get("url") or "") + "\n" + (item.get("text") or "")).strip()
            if not text:
                skipped += 1
                continue
            ok, _message, _saved = add_signal(text, source=item.get("source") or "visible_feed")
            if ok:
                added += 1
            else:
                skipped += 1
        self.respond_json({"added": added, "skipped": skipped})

    def handle_add(self, parsed):
        params = parse_qs(parsed.query)
        url = unquote(params.get("url", [""])[0])
        text = unquote(params.get("text", [""])[0])
        source = params.get("source", ["for_you"])[0]
        payload = (url + "\n" + text).strip()
        added, message, _item = add_signal(payload, source=source)
        self.respond(page(f"<div class='card'><h1>{html.escape(message)}</h1><p>تم الحفظ من X. يمكنك إغلاق هذه النافذة.</p><p><a class='button' href='/'>عرض المحفوظات</a></p></div>"))

    def handle_home(self):
        posts = load_json(POSTS_FILE, {"items": []})
        recent = list(reversed(posts["items"][-10:]))
        items = "".join(
            f"<div class='item'><b>score={item.get('pain_signal_score')}</b> <small>{html.escape(item.get('source_type',''))}</small><p>{html.escape(item.get('text','')[:500])}</p><small>{html.escape(item.get('url') or '')}</small></div>"
            for item in recent
        ) or "<p>لا توجد إشارات محفوظة بعد.</p>"
        bookmarklet = html.escape(BOOKMARKLET, quote=True)
        bulk_bookmarklet = html.escape(BULK_BOOKMARKLET, quote=True)
        auto_bookmarklet = html.escape(AUTO_BOOKMARKLET, quote=True)
        body = f"""
<h1>AX X Capture</h1>
<div class="card">
  <h2>الأسهل: راقب واجمع تلقائيًا</h2>
  <p><a class="button" href="https://x.com/home" target="_blank">افتح X الآن</a></p>
  <p>اسحب هذا الزر إلى شريط المفضلة. افتح X واضغطه مرة واحدة؛ سيجمع التغريدات الظاهرة، يمرر الصفحة تلقائيًا، ويتوقف بعد أقل من دقيقة.</p>
  <p><a class="button" href="{auto_bookmarklet}">راقب واجمع في AX</a></p>
  <p>إذا لم يعمل السحب في Safari: أنشئ مفضلة جديدة باسم <code>راقب واجمع في AX</code> والصق هذا النص كرابط:</p>
  <textarea class="code" rows="6" readonly>{auto_bookmarklet}</textarea>
</div>
<div class="card">
  <h2>جمع الصفحة الحالية فقط</h2>
  <p>اسحب هذا الزر إلى شريط المفضلة. افتح For You أو Search في X ثم اضغطه مرة واحدة ليحفظ كل التغريدات الظاهرة:</p>
  <p><a class="button" href="{bulk_bookmarklet}">اجمع الظاهر في AX</a></p>
  <p>إذا لم يعمل السحب في Safari: أنشئ مفضلة جديدة باسم <code>اجمع الظاهر في AX</code> والصق هذا النص كرابط:</p>
  <textarea class="code" rows="5" readonly>{bulk_bookmarklet}</textarea>
</div>
<div class="card">
  <h2>حفظ تغريدة واحدة</h2>
  <p>هذا الزر يحفظ التغريدة الحالية أو النص المظلل فقط:</p>
  <p><a class="button" href="{bookmarklet}">احفظ في AX</a></p>
  <p>بعدها افتح أي تغريدة في X واضغط الزر. إذا ظللت نصًا قبل الضغط سيُحفظ النص أيضًا.</p>
  <p>إذا لم يعمل السحب في Safari: أنشئ مفضلة جديدة، واجعل العنوان <code>احفظ في AX</code>، والصق النص التالي في خانة الرابط:</p>
  <textarea class="code" rows="4" readonly>{bookmarklet}</textarea>
</div>
<div class="card">
  <h2>إذا لم تعمل الأزرار: لصق صفحة X</h2>
  <p>افتح X، اضغط <code>Cmd+A</code> ثم <code>Cmd+C</code>، ثم الصق هنا. هذه الطريقة لا تحتاج Bookmarklet.</p>
  <form method="post" action="/paste">
    <textarea name="text" rows="8" placeholder="الصق هنا النص المنسوخ من صفحة X"></textarea>
    <p><button type="submit">استخرج التغريدات من النص</button></p>
  </form>
</div>
<div class="card">
  <h2>إضافة يدوية سريعة</h2>
  <form method="post">
    <textarea name="text" rows="5" placeholder="الصق رابط أو نص تغريدة هنا"></textarea>
    <input type="hidden" name="source" value="manual_page">
    <p><button type="submit">حفظ</button></p>
  </form>
</div>
<div class="card">
  <h2>آخر الإشارات ({len(posts['items'])})</h2>
  {items}
</div>
"""
        self.respond(page(body))

    def respond(self, content, status=200):
        data = content.encode("utf-8")
        self.send_response(status)
        self.cors_headers()
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def respond_json(self, value, status=200):
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.cors_headers()
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def cors_headers(self):
        self.send_header("access-control-allow-origin", "*")
        self.send_header("access-control-allow-methods", "GET, POST, OPTIONS")
        self.send_header("access-control-allow-headers", "content-type")

    def log_message(self, *_args):
        return


def split_pasted_x_text(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    urls = re.findall(r"https?://(?:www\.)?(?:x|twitter)\.com/[^\s]+/status/\d+[^\s]*", text)
    chunks = []
    if urls:
        for url in urls:
            chunks.append(url)
    blocks = re.split(r"\n(?=(?:@|[A-Za-z0-9_]{2,30}\n@|Follow|متابعة)\b)", text)
    for block in blocks:
        clean = "\n".join(line.strip() for line in block.splitlines() if line.strip())
        if len(clean) < 80:
            continue
        if any(term.lower() in clean.lower() for term in ["ai", "claude", "chatgpt", "gpt", "agent", "ذكاء", "كلاود", "وكلاء"]):
            chunks.append(clean[:1800])
    seen = set()
    unique = []
    for chunk in chunks:
        key = chunk[:180]
        if key in seen:
            continue
        seen.add(key)
        unique.append(chunk)
    return unique[:80]


def main():
    print(f"AX X Capture: http://127.0.0.1:{PORT}")
    print("اضغط Ctrl+C للإيقاف.")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
