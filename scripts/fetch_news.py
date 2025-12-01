import json
import time
import urllib.request
import xml.etree.ElementTree as ET
import re

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
            items.append({"title": title, "link": link, "source": source, "pubDate": pub, "image": image})
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
                items.append({"title": title, "link": link, "source": source, "pubDate": pub, "image": image})
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
                    it['image'] = m.group(1)
                    count += 1
            except Exception:
                continue
        return items
    deduped = enrich_images(deduped, limit=50)
    deduped = deduped[:100]
    data = {"updated": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), "items": deduped}
    out_path = 'assets/data/news.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('[OK] wrote', out_path, 'items:', len(deduped))

if __name__ == '__main__':
    main()
