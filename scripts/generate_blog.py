import os
import json
import random
from datetime import datetime

TOPICS_PATH = os.path.join('data', 'topics.json')
POSTS_DIR = os.path.join('blog', 'posts')
INDEX_PATH = os.path.join('blog', 'index.html')
AFFILIATES_PATH = os.path.join('data', 'affiliates.json')
TOPIC_IMAGES_PATH = os.path.join('data', 'topic_images.json')

def load_topics():
    with open(TOPICS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def pick_topic(topics):
    return random.choice(topics)

def load_json_safe(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def match_category(title):
    t = title.lower()
    if any(k in t for k in ['credit card','rewards','cashback','travel']):
        return 'credit'
    if any(k in t for k in ['loan','emi','home loan','personal loan']):
        return 'loan'
    if any(k in t for k in ['tax','itr','income tax','gst']):
        return 'tax'
    if any(k in t for k in ['investment','sip','fd','rd','apps']):
        return 'invest'
    return 'general'

def find_image_for_topic(slug, title):
    imgs = load_json_safe(TOPIC_IMAGES_PATH) or {}
    if slug in imgs:
        return imgs[slug]
    ep = os.getenv('IMAGE_SEARCH_ENDPOINT','')
    if ep:
        try:
            import urllib.request
            import urllib.parse
            q = urllib.parse.quote(title)
            req = urllib.request.Request(ep+'?q='+q, headers={'Accept':'application/json'})
            resp = urllib.request.urlopen(req, timeout=8)
            data = json.loads(resp.read().decode('utf-8'))
            if isinstance(data, dict):
                url = data.get('url') or (data.get('results') or [{}])[0].get('url')
                if url:
                    return url
        except Exception:
            pass
    return 'https://source.unsplash.com/1200x675/?finance,india'

def build_figure(img_url, title):
    alt = title
    fig = []
    fig.append('<figure class="card">')
    fig.append('<img src="'+img_url+'" alt="'+alt+'" loading="lazy" referrerpolicy="no-referrer">')
    fig.append('<figcaption style="color:#9ca3af">Illustrative image</figcaption>')
    fig.append('</figure>')
    return '\n'.join(fig)

def build_body(title, slug):
    parts = []
    parts.append('<article class="section">')
    parts.append('<h1>'+title+'</h1>')
    parts.append(build_figure(find_image_for_topic(slug, title), title))
    parts.append('<p>This guide is written for Indian readers who prefer simple, practical explanations with real examples. It avoids jargon and focuses on clarity you can use today. If you are planning a loan, choosing a credit card, filing taxes, or setting up investments, the goal is to help you take the next step confidently.</p>')
    parts.append('<div class="in-article-ad ad">In-Article Ad Placement</div>')
    sections = [
        ('Why this matters', 8),
        ('Quick fundamentals', 8),
        ('Step-by-step walkthrough', 12),
        ('Real examples', 12),
        ('Mistakes to avoid', 10),
        ('Smart tips', 10),
        ('Deep dive', 18),
        ('FAQs', 15),
        ('Summary you can act on', 6)
    ]
    for (name, para_count) in sections:
        parts.append('<h2>'+name+'</h2>')
        for i in range(para_count):
            parts.append('<p>'+paragraph(title, name, i)+'</p>')
    parts.append('<div class="cta-row"><a class="ghost" href="/tools/emi.html">Use EMI Calculator</a><a class="ghost" href="/tools/income-tax.html">Estimate Income Tax</a><a class="ghost" href="/tools/sip.html">Project SIP Maturity</a></div>')
    parts.append(build_affiliate_block(title))
    parts.append('</article>')
    return '\n'.join(parts)

def paragraph(title, section, i):
    base = (
        'When you approach "'+title+'", focus on small, concrete steps instead of trying to solve everything at once. '
        'Start with the numbers you can verify today—income, fixed costs, interest rates, fees—and then estimate variable parts conservatively. '
        'Use the relevant calculator to test a few scenarios, and write down what changes your result the most. '
        'Prefer simple rules that you can explain to a friend: one number for affordability, one number for savings, one number for risk. '
        'If a decision still feels tricky, pause and reframe: what outcome will still be okay even if things go a little worse than you expect? '
        'That mindset helps you pick options you can sustain without stress.'
    )
    addon = (
        ' In India, lenders and apps publish terms that look similar at a glance but differ in fine print—processing fees, annual charges, GST, waiver conditions, reset dates. '
        'Read the actual schedule or charge table and plug those into the calculators. '
        'For cards, check benefit caps by month and category; for loans, confirm whether EMI or tenure changes at resets; for SIPs, verify exit loads and tax treatment. '
        'Across all choices, prefer transparency over promises.'
    )
    return base + addon

def faq_ld(title):
    qas = [
        {"q":"What should I check first?","a":"Start with verified numbers and use calculators to test scenarios."},
        {"q":"How do I compare options fairly?","a":"Include fees, taxes and caps; compare total cost and comfort."},
        {"q":"What is a safe next step?","a":"Pick actions you can sustain even if outcomes turn slightly worse."}
    ]
    items = []
    for qa in qas:
        items.append({"@type":"Question","name":qa["q"],"acceptedAnswer":{"@type":"Answer","text":qa["a"]}})
    return json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":items})

def build_html(title, meta, slug):
    head = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/assets/css/styles.css"><link rel="canonical" href="'+meta['canonical']+'"></head>'
    body_open = '<body data-title="'+title+'" data-meta="'+meta['description']+'"><header id="header"></header><main class="container layout"><div>'
    faq_script = '<script type="application/ld+json">'+faq_ld(title)+'</script>'
    body_close = '</div><aside><div class="sidebar-ad ad">Sidebar Ad Placement</div></aside></main><footer id="footer"></footer>'+faq_script+'<script src="/assets/js/main.js" defer></script></body></html>'
    return head + body_open + build_body(title, slug) + body_close

def write_post(topic):
    now = datetime.utcnow().strftime('%Y-%m-%d-%H%M')
    slug = topic['slug'] + '-' + now
    path = os.path.join(POSTS_DIR, slug + '.html')
    can = '/blog/posts/'+slug+'.html'
    meta = {
        'canonical': can,
        'description': 'A practical guide for Indian readers on '+topic['title'].lower()+'.'
    }
    html = build_html(topic['title'], meta, topic['slug'])
    os.makedirs(POSTS_DIR, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    return slug, path

def update_index(slug, title):
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    card = '<div class="card"><h3><a href="/blog/posts/'+slug+'.html">'+title+'</a></h3><p>New analysis and implementations.</p></div>'
    content = content.replace('</div></section>', card + '</div></section>')
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def build_affiliate_block(title):
    afs = load_json_safe(AFFILIATES_PATH) or []
    cat = match_category(title)
    picks = []
    for a in afs:
        mk = [k for k in a.get('match_keywords', [])]
        if any(k in title.lower() for k in mk):
            picks.append(a)
    if not picks:
        return ''
    rows = []
    rows.append('<div class="card">')
    for a in picks[:2]:
        rel = ' rel="nofollow noopener"' if a.get('nofollow') else ''
        img = ''
        if a.get('image_url'):
            img = '<div class="cta-row"><a href="'+a['link']+'" target="_blank"'+rel+'><img src="'+a['image_url']+'" height="30" alt="'+a.get('title','')+'"></a></div>'
        rows.append('<h3><a href="'+a['link']+'" target="_blank"'+rel+'>'+a.get('title','Affiliate')+'</a></h3>')
        if img:
            rows.append(img)
        rows.append('<div class="cta-row"><a class="ghost" href="'+a['link']+'" target="_blank"'+rel+'>'+a.get('cta_text','Learn More')+'</a></div>')
    rows.append('</div>')
    return '\n'.join(rows)

def main():
    topics = load_topics()
    topic = pick_topic(topics)
    slug, path = write_post(topic)
    update_index(slug, topic['title'])
    print('Generated', path)

if __name__ == '__main__':
    main()
