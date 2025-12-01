import json
import time
import urllib.request
import xml.etree.ElementTree as ET
import re
import os
import hashlib
from urllib.parse import urlparse

FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://rss.cnn.com/rss/money_latest.rss",
    "https://finance.yahoo.com/rss/topstories",
    "https://www.investing.com/rss/news_25.rss",
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.moneycontrol.com/rss/markets.xml",
    "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "https://www.business-standard.com/rss/home_page_top_stories.rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

UA_POOL = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/121.0 Safari/537.36'
]
RETRY_OVERRIDES = {
    'www.moneycontrol.com': 4,
    'www.business-standard.com': 4
}
SLEEP_BETWEEN_FEEDS = 0.75

def fetch(url, timeout=15, retries=2, backoff=1.5):
    host = url.split('/')[2] if '://' in url else ''
    retries = RETRY_OVERRIDES.get(host, retries)
    ua = UA_POOL[(int(time.time()*1000) // 1000) % len(UA_POOL)]
    headers = {
        'User-Agent': ua,
        'Accept': 'application/rss+xml, application/xml;q=0.9, */*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'close',
        'Referer': ('https://' + host) if host else 'https://localhost'
    }
    req = urllib.request.Request(url, headers=headers)
    attempt = 0
    while attempt <= retries:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            print("[WARN] feed error:", url, e)
            attempt += 1
            if attempt > retries:
                break
            try:
                time.sleep(backoff * attempt)
            except Exception:
                pass
    return None

def normalize_image_url(url):
    try:
        if not url:
            return url
        if 's.yimg.com/ny/api/res' in url and 'https://media.zenfs.com/' in url:
            i = url.find('https://media.zenfs.com/')
            return url[i:]
        return url
    except Exception:
        return url

def slugify(text):
    try:
        s = re.sub(r'[^a-zA-Z0-9\s-]', '', text or '')
        s = re.sub(r'\s+', '-', s.strip())
        return s.lower()[:80] or 'news'
    except Exception:
        return 'news'

def fetch_html(url, timeout=12):
    try:
        ua = UA_POOL[(int(time.time()*1000) // 1000) % len(UA_POOL)]
        headers = {
            'User-Agent': ua,
            'Accept': 'text/html,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'close',
            'Referer': 'https://' + (url.split('/')[2] if '://' in url else 'localhost')
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(350000).decode('utf-8', errors='ignore')
    except Exception as e:
        print('[WARN] extract error:', url, e)
        return ''

def extract_article_html(page_html):
    if not page_html:
        return ''
    # Prefer <article> content
    m = re.search(r'<article[\s\S]*?</article>', page_html, re.IGNORECASE)
    if m:
        return m.group(0)
    # Common containers
    m = re.search(r'<div[^>]+(id|class)=("|")[^"]*(story|content|article|post|entry|text)[^"]*("|")[\s\S]*?</div>', page_html, re.IGNORECASE)
    if m:
        return m.group(0)
    # Fallback: paragraphs
    paras = re.findall(r'<p[\s\S]*?</p>', page_html, re.IGNORECASE)
    if paras:
        return '<div>' + ''.join(paras[:60]) + '</div>'
    return ''

def write_article_page(item, content_html):
    try:
        title = item['title']
        src = item['source']
        link = item['link']
        pub = item.get('pubDate','')
        image = item.get('image','')
        slug = item['slug']
        os.makedirs(os.path.join('news','articles'), exist_ok=True)
        meta_desc = re.sub(r'<[^>]+>', ' ', content_html or '')
        meta_desc = ' '.join(meta_desc.split())[:240] or (title[:240])
        lines = []
        lines.append('<!doctype html>')
        lines.append('<html lang="en">')
        lines.append('<head>')
        lines.append('<meta charset="utf-8">')
        lines.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
        lines.append('<link rel="stylesheet" href="/assets/css/styles.css">')
        lines.append('<link rel="canonical" href="/news/articles/'+slug+'.html">')
        lines.append('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7510164795562884" crossorigin="anonymous"></script>')
        lines.append('<script src="/assets/js/main.js" defer></script>')
        lines.append('</head>')
        lines.append('<body data-title="'+title+'" data-meta="'+meta_desc+'">')
        lines.append('<div id="header"></div>')
        lines.append('<main class="container">')
        lines.append('<section class="section">')
        lines.append('<h1>'+title+'</h1>')
        if image:
            lines.append('<img class="thumb" src="'+normalize_image_url(image)+'" alt="'+title+'">')
        lines.append(content_html or '<p>Full article could not be extracted. Read on the source below.</p>')
        lines.append('<div class="card" style="margin-top:1rem"><strong>Source:</strong> <a href="'+link+'" rel="nofollow noopener" target="_blank">'+src+'</a>')
        if pub:
            lines.append('<br><small>'+pub+'</small>')
        lines.append('</div>')
        lines.append('</section>')
        lines.append('<div class="in-article-ad ad"></div>')
        lines.append('</main>')
        lines.append('<div id="footer"></div>')
        lines.append('</body>')
        lines.append('</html>')
        out_path = os.path.join('news','articles', slug+'.html')
        with open(out_path,'w',encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return out_path
    except Exception as e:
        print('[WARN] write page error:', e)
        return ''

def parse_items(xml_bytes, source):
    items = []
    try:
        root = ET.fromstring(xml_bytes)
    except Exception:
        return items
    media_ns1 = {'media': 'http://search.yahoo.com/mrss/'}
    media_ns2 = {'media': 'https://search.yahoo.com/mrss/'}
    for item in root.findall('.//item'):
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        pub = (item.findtext('pubDate') or item.findtext('updated') or '').strip()
        image = ''
        enc = item.find('enclosure')
        if enc is not None:
            et = (enc.get('type') or '')
            if et.startswith('image'):
                image = enc.get('url') or image
        if not image:
            m1 = item.find('media:content', media_ns1)
            if m1 is None:
                m1 = item.find('media:content', media_ns2)
            if m1 is not None:
                if (m1.get('medium') or '') == 'image' or (m1.get('type') or '').startswith('image'):
                    image = m1.get('url') or image
        if not image:
            mt = item.find('media:thumbnail', media_ns1)
            if mt is None:
                mt = item.find('media:thumbnail', media_ns2)
            if mt is not None:
                image = mt.get('url') or image
        if not image:
            desc = item.findtext('description') or ''
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc)
            if m:
                image = m.group(1)
        if title and link:
            items.append({"title": title, "link": link, "source": source, "pubDate": pub, "image": normalize_image_url(image)})
    if not items:
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('.//atom:entry', ns):
            title = (entry.findtext('atom:title', default='', namespaces=ns) or '').strip()
            link = ''
            for l in entry.findall('atom:link', ns):
                rel = (l.get('rel') or '')
                href = l.get('href') or ''
                if rel in ('alternate', '') and href and not link:
                    link = href
            pub = (entry.findtext('atom:updated', default='', namespaces=ns) or '').strip()
            image = ''
            for l in entry.findall('atom:link', ns):
                rel = (l.get('rel') or '')
                typ = (l.get('type') or '')
                href = l.get('href') or ''
                if rel == 'enclosure' and (typ.startswith('image') or not typ) and href:
                    image = href
            if not image:
                m1 = entry.find('media:content', media_ns1)
                if m1 is None:
                    m1 = entry.find('media:content', media_ns2)
                if m1 is not None:
                    if (m1.get('medium') or '') == 'image' or (m1.get('type') or '').startswith('image'):
                        image = m1.get('url') or image
            if not image:
                mt = entry.find('media:thumbnail', media_ns1)
                if mt is None:
                    mt = entry.find('media:thumbnail', media_ns2)
                if mt is not None:
                    image = mt.get('url') or image
            if title and link:
                items.append({"title": title, "link": link, "source": source, "pubDate": pub, "image": normalize_image_url(image)})
    return items

def main():
    all_items = []
    for url in FEEDS:
        xml = fetch(url)
        if not xml:
            if 'rss.cnn.com' in url and url.startswith('https://'):
                alt = 'http://' + url.split('://',1)[1]
                xml = fetch(alt)
            continue
        items = parse_items(xml, source=url.split('/')[2])
        all_items.extend(items)
        try:
            time.sleep(SLEEP_BETWEEN_FEEDS)
        except Exception:
            pass
    # Deduplicate by link
    seen = set()
    deduped = []
    for it in all_items:
        if it['link'] in seen:
            continue
        seen.add(it['link'])
        deduped.append(it)
    # Sort by pubDate (fallback to current time)
    def ts(x):
        return time.time()
    def enrich_images(items, limit=30):
        count = 0
        allow = {
            'www.business-standard.com','economictimes.indiatimes.com','www.moneycontrol.com',
            'www.investing.com','www.coindesk.com','finance.yahoo.com','www.reuters.com','rss.cnn.com',
            'www.investors.com','www.barrons.com'
        }
        for it in items:
            if count >= limit:
                break
            if it.get('image'):
                continue
            try:
                host = it['link'].split('/')[2]
            except Exception:
                host = ''
            if host not in allow:
                continue
            try:
                req = urllib.request.Request(it['link'], headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36',
                    'Accept': 'text/html,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'close',
                    'Referer': 'https://' + host if host else 'https://localhost'
                })
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html = resp.read(120000).decode('utf-8', errors='ignore')
                m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
                if not m:
                    m = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html)
                if not m:
                    m = re.search(r'<meta[^>]+property=["\']og:image:secure_url["\'][^>]+content=["\']([^"\']+)["\']', html)
                if m:
                    it['image'] = normalize_image_url(m.group(1))
                    count += 1
            except Exception:
                continue
        return items
    deduped = enrich_images(deduped, limit=50)
    deduped = deduped[:100]
    # Build local article pages for each item
    for it in deduped:
        try:
            h = hashlib.sha1((it['link']).encode('utf-8')).hexdigest()[:8]
            it['slug'] = slugify(it['title'])+'-'+h
            page_html = fetch_html(it['link'])
            content_html = extract_article_html(page_html)
            write_article_page(it, content_html)
        except Exception:
            it['slug'] = slugify(it['title'])
    data = {"updated": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), "items": deduped}
    out_path = 'assets/data/news.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('[OK] wrote', out_path, 'items:', len(deduped))

if __name__ == '__main__':
    main()
