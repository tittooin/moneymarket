import os
import time
from urllib.parse import urljoin

BASE_URL = os.environ.get('SITE_BASE_URL', 'https://moneymarket.blog/')

def collect_html(root):
    pages = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if not f.endswith('.html'):
                continue
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, root).replace('\\', '/')
            url = urljoin(BASE_URL, rel)
            mtime = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(os.path.getmtime(p)))
            pages.append((url, mtime))
    return pages

def write_sitemap(pages, out_path):
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url, mtime in pages:
        lines.append('<url>')
        lines.append('<loc>'+url+'</loc>')
        lines.append('<lastmod>'+mtime+'</lastmod>')
        lines.append('</url>')
    lines.append('</urlset>')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def main():
    pages = collect_html('.')
    write_sitemap(pages, 'sitemap.xml')
    print('[OK] sitemap entries:', len(pages))

if __name__ == '__main__':
    main()
