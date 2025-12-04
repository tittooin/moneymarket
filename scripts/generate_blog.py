import os
import json
import random
import sys
from datetime import datetime
import re

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

def vary(options):
    return random.choice(options)

def build_table(headers, rows):
    html = []
    html.append('<div class="card"><table style="width:100%">')
    html.append('<thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead>')
    html.append('<tbody>')
    for r in rows:
        html.append('<tr>'+''.join('<td>'+str(x)+'</td>' for x in r)+'</tr>')
    html.append('</tbody></table></div>')
    return '\n'.join(html)

def slugify_id(text):
    t = re.sub(r'[^a-zA-Z0-9\s-]', '', text or '')
    t = re.sub(r'\s+', '-', t.strip())
    return (t.lower() or 'section')

def build_toc(section_names):
    items = []
    for name in section_names:
        sid = slugify_id(name)
        items.append('<li><a href="#'+sid+'">'+name+'</a></li>')
    return '<nav class="toc" aria-label="Table of Contents"><h2>Table of Contents</h2><ul>'+''.join(items)+'</ul></nav>'

def collect_related_posts(cat, limit=3):
    items = []
    try:
        names = sorted([n for n in os.listdir(POSTS_DIR) if n.endswith('.html')], reverse=True)
        for name in names:
            fp = os.path.join(POSTS_DIR, name)
            with open(fp, 'r', encoding='utf-8') as f:
                s = f.read()
            m = re.search(r'data-title="([^"]+)"', s)
            t = (m.group(1) if m else '')
            if match_category(t) == cat:
                items.append((t, '/blog/posts/'+name))
            if len(items) >= limit:
                break
    except Exception:
        pass
    return items

def build_link_block(cat, slug, title):
    labels = {
        '/tools/emi.html': 'EMI Calculator',
        '/tools/income-tax.html': 'Income Tax Calculator',
        '/tools/sip.html': 'SIP Calculator',
        '/tools/fd-rd.html': 'FD / RD Calculator',
        '/blog/index.html': 'Blog Home',
        '/credit-cards/index.html': 'Credit Cards',
        '/loans/index.html': 'Loans',
        '/investments/index.html': 'Investments',
        '/tax/index.html': 'Tax'
    }
    internal = []
    external = []
    if cat == 'loan':
        internal = ['/loans/index.html','/tools/emi.html','/tools/income-tax.html']
        external = [('Reserve Bank of India', 'https://www.rbi.org.in/')]
    elif cat == 'credit':
        internal = ['/credit-cards/index.html','/tools/income-tax.html','/tools/emi.html']
        external = [('Reserve Bank of India', 'https://www.rbi.org.in/')]
    elif cat == 'tax':
        internal = ['/tax/index.html','/tools/income-tax.html','/blog/index.html']
        external = [('Income Tax Department', 'https://incometax.gov.in/')]
    elif cat == 'invest':
        internal = ['/investments/index.html','/tools/sip.html','/tools/fd-rd.html']
        external = [('SEBI', 'https://www.sebi.gov.in/')]
    else:
        internal = ['/blog/index.html','/tools/emi.html','/tools/income-tax.html','/tools/sip.html']
        external = [('Reserve Bank of India', 'https://www.rbi.org.in/'), ('Income Tax Department', 'https://incometax.gov.in/')]
    rel_posts = collect_related_posts(cat, 3)
    html = []
    html.append('<div class="card">')
    html.append('<h3>Recommended Links</h3>')
    if internal:
        html.append('<p>' + ' • '.join('<a href="'+u+'">'+labels.get(u,u)+'</a>' for u in internal) + '</p>')
    if external:
        html.append('<p>' + ' • '.join('<a href="'+u+'" target="_blank" rel="nofollow noopener">'+n+'</a>' for n,u in external) + '</p>')
    if rel_posts:
        html.append('<ul>' + ''.join('<li><a href="'+link+'">'+t+'</a></li>' for t,link in rel_posts) + '</ul>')
    html.append('</div>')
    return '\n'.join(html)

def build_para_random(title, cat):
    o = [
        'Most households save more by planning purchases as small projects rather than impulse buys.',
        'Good decisions start with verified numbers and realistic assumptions.',
        'Clarity arrives when you write down exact costs, timelines and care routines.'
    ]
    m = [
        'Track one‑time price, shipping, GST, and any seasonal discount to compute total landed cost.',
        'Use a simple lifespan estimate with care and warranty to spread cost per year.',
        'Compare alternatives on durability, safety, and replacement cycle — not only sticker price.'
    ]
    i = [
        'Indian card programs cap rewards by category and month; check those caps before using offers.',
        'Retail events change terms quickly; always re‑check effective rates and fees at checkout.',
        'Household goals work best when the monthly budget includes a small buffer for maintenance and replacements.'
    ]
    c = {
        'loan': ['If you plan to finance, compute EMI and total interest, and confirm you still prefer the item after seeing the full cost.','Prepayments done early save the most; align them to bonuses so the EMI never feels heavy.'],
        'credit': ['Pay total due every cycle to keep rewards meaningful; revolving destroys value quickly.','Use category‑aligned cards to earn points where you spend most, then redeem at high‑value partners.'],
        'tax': ['Keep invoices and warranty docs; if for business use, confirm input tax credits and compliance rules.','Understand GST on different categories and how returns reflect them.'],
        'invest': ['Treat durability as a defensive investment that lowers replacements and waste.','Focus on long horizons; value compounds when you avoid frequent breakage and repurchases.'],
        'general': ['Plan purchases with a simple checklist: need, budget, lifespan, care, and resale or donation options.','Prefer transparent pricing and documentation over flashy claims.']
    }
    lines = [random.choice(o), random.choice(m), random.choice(i), random.choice(c.get(cat,'general'))]
    return ' '.join(lines)

def ensure_word_count(paragraphs, title, cat, target=5200):
    def wc(ls):
        return sum(len(p.split()) for p in ls)
    while wc(paragraphs) < target:
        paragraphs.append(build_para_random(title, cat))
    return paragraphs

def loan_example():
    P = 1000000
    r = 0.095/12
    n = 240
    emi = P*r*((1+r)**n)/(((1+r)**n)-1)
    total = emi*n
    interest = total-P
    return P, round(emi,2), round(total,2), round(interest,2)

def credit_spend_example():
    cats = [('Groceries',12000),('Fuel',4000),('Dining',3000),('Online',6000),('Travel',8000)]
    yearly = sum(x for _,x in cats)*12
    return cats, yearly

def tax_example():
    salary = 1200000
    sec80c = 150000
    sec80d = 25000
    nps = 50000
    taxable = salary - sec80c - sec80d - nps
    return salary, taxable

def sip_example():
    monthly = 5000
    rate = 0.12/12
    months = 180
    fv = monthly*(((1+rate)**months-1)/rate)*(1+rate)
    invested = monthly*months
    gain = fv-invested
    return monthly, months, round(fv,2), invested, round(gain,2)

def section_paragraphs(slug, title):
    cat = match_category(title)
    paras = []
    if cat=='loan':
        P, emi, total, interest = loan_example()
        paras.extend([
            'EMI depends on principal, interest and tenure. For a ₹ '+str(P)+' loan at about 9.5% for 20 years, EMI is roughly ₹ '+str(emi)+'. Total payment ₹ '+str(total)+' with interest near ₹ '+str(interest)+'.',
            'Keep FOIR under ~40–45% and hold a 3–6 month buffer. Affordability is more important than a slightly lower rate.',
            'Prepay early when possible; it reduces future interest the most and can shorten tenure without stress.',
            'Compare effective APR including processing fees and insurance. Do balance transfer only if net savings are meaningful and quick.'
        ])
        paras.extend([
            vary(['Fixed vs floating: understand reset frequency and how EMI or tenure changes; plan prepayments around resets.',
                  'A strong bureau score and healthy debt‑to‑income unlock better pricing and smoother documentation.']),
            'Checklist: documents, FOIR, insurance, fees, amortization, prepayment clauses, statement cycle.'
        ])
    elif cat=='credit':
        cats, yearly = credit_spend_example()
        rows = [(c,'₹ '+str(a)) for c,a in cats]
        table = build_table(['Category','Monthly Spend'], rows)
        paras.extend([
            'Rewards depend on category caps and program rules. Map monthly spends and pick cards that amplify top categories.',
            'Always pay total due by due date. Revolving is expensive; avoid interest and fees via reminders and auto‑debit.',
            'Welcome bonuses have minimum spends within windows. Track them with calendar alerts to avoid missing thresholds.',
            'With this mix, yearly spend is about ₹ '+str(yearly)+'. Compute reward rate after caps and redemption to judge real value.'
        ])
        paras.append(table)
        paras.append('Evaluate fuel waivers, lounge access, forex markup, EMI conversion fees and service quality beyond headline rates.')
    elif cat=='tax':
        salary, taxable = tax_example()
        paras.extend([
            'Choose regime after computing both outcomes. New regime simplifies slabs; old regime rewards deductions. Decide using exact numbers.',
            'Example salary ₹ '+str(salary)+'. After typical deductions, taxable could be ~₹ '+str(taxable)+'. Compare slab outcomes using the calculator.',
            'Keep Form 16, 26AS, AIS/TIS, rent receipts, medical bills and investment proofs organized. Documentation drives accuracy.',
            'Plan early: spread Section 80C, track HRA, claim NPS 80CCD(1B), and align declarations to proofs.'
        ])
    elif cat=='invest':
        m, months, fv, inv, gain = sip_example()
        paras.extend([
            'SIP builds discipline via small monthly steps. With ₹ '+str(m)+' for '+str(months)+' months at realistic returns, corpus can reach about ₹ '+str(fv)+'.',
            'Rupee cost averaging reduces timing risk. Focus on horizon and allocation; use direct plans to cut costs and review via XIRR.',
            'Keep emergency funds separate and align risk to goals; avoid chasing short‑term performance.',
            'Tax treatment matters; understand equity/debt rules and rebalance yearly to control risk.'
        ])
    else:
        paras.extend([
            'Start with verified numbers. Budget honestly, track fixed and variable costs, then test scenarios in calculators.',
            'Prefer small steps you can sustain. Automation and reminders cut errors; keep buffers and review monthly.'
        ])
    return paras

def build_body(title, slug):
    parts = []
    parts.append('<article class="section">')
    parts.append('<h1>'+title+'</h1>')
    parts.append(build_figure(find_image_for_topic(slug, title), title))
    parts.append('<p>This guide is written for Indian readers who prefer clear, practical explanations with real examples. It avoids jargon and keeps things actionable for everyday decisions.</p>')
    parts.append('<div class="in-article-ad ad">In-Article Ad Placement</div>')
    outline = [
        'Why this matters','Quick fundamentals','Step-by-step walkthrough','Real examples','Mistakes to avoid','Smart tips','Deep dive','FAQs','Summary you can act on'
    ]
    parts.append(build_toc(outline))
    core = section_paragraphs(slug, title)
    cat = match_category(title)
    base = core + core + core
    paragraphs = ensure_word_count(base, title, cat, 5200)
    per = max(8, len(paragraphs)//len(outline))
    for i, name in enumerate(outline):
        sid = slugify_id(name)
        parts.append('<h2 id="'+sid+'">'+name+'</h2>')
        start = i*per
        end = (i+1)*per
        chunk = paragraphs[start:end]
        if not chunk:
            chunk = core
        for p in chunk:
            parts.append('<p>'+p+'</p>')
    parts.append('<div class="cta-row"><a class="ghost" href="/tools/emi.html">Use EMI Calculator</a><a class="ghost" href="/tools/income-tax.html">Estimate Income Tax</a><a class="ghost" href="/tools/sip.html">Project SIP Maturity</a></div>')
    parts.append(build_link_block(cat, slug, title))
    parts.append(build_affiliate_block(title))
    parts.append('</article>')
    return '\n'.join(parts)

def generate_all(topics):
    for topic in topics:
        slug, path = write_post(topic)
        update_index(slug, topic['title'])
        print('Generated', path)

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

def article_ld(title, canonical, img_url):
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "image": img_url,
        "mainEntityOfPage": canonical,
        "datePublished": datetime.utcnow().isoformat()+"Z",
        "author": {"@type":"Organization","name":"MoneyMarket"}
    }
    return json.dumps(data)

def build_html(title, meta, slug):
    img = find_image_for_topic(slug, title)
    head = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="title" content="'+title+'"><meta name="description" content="'+meta['description']+'"><meta property="og:title" content="'+title+'"><meta property="og:description" content="'+meta['description']+'"><meta property="og:url" content="'+meta['canonical']+'"><meta property="og:image" content="'+img+'"><link rel="stylesheet" href="/assets/css/styles.css"><link rel="canonical" href="'+meta['canonical']+'"></head>'
    body_open = '<body data-title="'+title+'" data-meta="'+meta['description']+'"><header id="header"></header><main class="container layout"><div>'
    faq_script = '<script type="application/ld+json">'+faq_ld(title)+'</script>'
    article_script = '<script type="application/ld+json">'+article_ld(title, meta['canonical'], img)+'</script>'
    body_close = '</div><aside><div class="sidebar-ad ad">Sidebar Ad Placement</div></aside></main><footer id="footer"></footer>'+faq_script+article_script+'<script src="/assets/js/main.js" defer></script></body></html>'
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
    grid = '<div class="grid">'
    if grid in content:
        content = content.replace(grid, grid + card, 1)
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
        if a.get('promo_text'):
            rows.append('<p>'+a.get('promo_text')+'</p>')
        if img:
            rows.append(img)
        rows.append('<div class="cta-row"><a class="ghost" href="'+a['link']+'" target="_blank"'+rel+'>'+a.get('cta_text','Learn More')+'</a></div>')
    rows.append('</div>')
    return '\n'.join(rows)

def upgrade_existing_posts():
    try:
        for name in os.listdir(POSTS_DIR):
            if not name.endswith('.html'):
                continue
            fp = os.path.join(POSTS_DIR, name)
            with open(fp,'r',encoding='utf-8') as f:
                s = f.read()
            changed = False
            # Add meta title/description from body data attributes
            if '<meta name="title"' not in s or '<meta name="description"' not in s:
                m_title = re.search(r'<body[^>]*data-title="([^"]+)"', s)
                m_desc = re.search(r'<body[^>]*data-meta="([^"]+)"', s)
                title = (m_title.group(1) if m_title else '')
                desc = (m_desc.group(1) if m_desc else '')
                s = s.replace('<head>', '<head>\n<meta name="title" content="'+title+'">\n<meta name="description" content="'+desc+'">', 1)
                # Open Graph minimal
                can = re.search(r'<link rel="canonical" href="([^"]+)"', s)
                can_url = (can.group(1) if can else '')
                s = s.replace('<head>', '<head>\n<meta property="og:title" content="'+title+'">\n<meta property="og:description" content="'+desc+'">\n<meta property="og:url" content="'+can_url+'">', 1)
                changed = True
            # Table of Contents and H2 ids
            if '<nav class="toc"' not in s:
                heads = re.findall(r'<h2>([^<]+)</h2>', s)
                if heads:
                    toc = build_toc(heads)
                    s = s.replace('</h1>', '</h1>'+toc, 1)
                    for h in heads:
                        sid = slugify_id(h)
                        s = s.replace('<h2>'+h+'</h2>', '<h2 id="'+sid+'">'+h+'</h2>')
                    changed = True
            # Recommended Links block
            if 'Recommended Links' not in s:
                m_title = re.search(r'<body[^>]*data-title="([^"]+)"', s)
                title = (m_title.group(1) if m_title else '')
                cat = match_category(title)
                block = build_link_block(cat, '', title)
                s_new = re.sub(r'(<div class="cta-row">[\s\S]*?</div>)', r'\1'+block, s, count=1)
                if s_new != s:
                    s = s_new
                    changed = True
            if changed:
                with open(fp,'w',encoding='utf-8') as f:
                    f.write(s)
    except Exception:
        pass

def main():
    topics = load_topics()
    if len(sys.argv)>1:
        if sys.argv[1]=='all':
            generate_all(topics)
            return
        if sys.argv[1]=='one' and len(sys.argv)>2:
            sel = sys.argv[2]
            for t in topics:
                if t['slug']==sel:
                    s, p = write_post(t)
                    update_index(s, t['title'])
                    print('Generated', p)
                    return
        if sys.argv[1]=='upgrade':
            upgrade_existing_posts()
            print('Upgraded SEO for existing posts')
            return
    topic = pick_topic(topics)
    slug, path = write_post(topic)
    update_index(slug, topic['title'])
    print('Generated', path)

if __name__ == '__main__':
    main()
