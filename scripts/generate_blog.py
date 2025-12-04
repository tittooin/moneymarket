import os
import json
import random
from datetime import datetime

TOPICS_PATH = os.path.join('data', 'topics.json')
POSTS_DIR = os.path.join('blog', 'posts')
INDEX_PATH = os.path.join('blog', 'index.html')

def load_topics():
    with open(TOPICS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def pick_topic(topics):
    return random.choice(topics)

def build_body(title):
    parts = []
    parts.append('<article class="section">')
    parts.append('<h1>'+title+'</h1>')
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
    parts.append('<div class="cta-row"><a href="https://www.finline.in/?fla=267" target="_blank" rel="nofollow noopener"><img src="https://www.finline.in/assets/v3/img/finline-logo.png" height="30" alt="Finline"></a></div>')
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

def build_html(title, meta):
    head = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/assets/css/styles.css"><link rel="canonical" href="'+meta['canonical']+'"></head>'
    body_open = '<body data-title="'+title+'" data-meta="'+meta['description']+'"><header id="header"></header><main class="container layout"><div>'
    body_close = '</div><aside><div class="sidebar-ad ad">Sidebar Ad Placement</div></aside></main><footer id="footer"></footer><script src="/assets/js/main.js" defer></script></body></html>'
    return head + body_open + build_body(title) + body_close

def write_post(topic):
    now = datetime.utcnow().strftime('%Y-%m-%d-%H%M')
    slug = topic['slug'] + '-' + now
    path = os.path.join(POSTS_DIR, slug + '.html')
    can = '/blog/posts/'+slug+'.html'
    meta = {
        'canonical': can,
        'description': 'A practical guide for Indian readers on '+topic['title'].lower()+'.'
    }
    html = build_html(topic['title'], meta)
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

def main():
    topics = load_topics()
    topic = pick_topic(topics)
    slug, path = write_post(topic)
    update_index(slug, topic['title'])
    print('Generated', path)

if __name__ == '__main__':
    main()

