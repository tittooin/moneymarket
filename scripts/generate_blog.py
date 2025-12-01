import os
import datetime as dt
import re

POSTS_DIR = os.path.join('blog','posts')

def slugify(text):
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    return text.lower()

def make_post(title, body_html):
    date = dt.date.today().isoformat()
    slug = slugify(title) + '-' + dt.datetime.now().strftime('%H%M')
    path = os.path.join(POSTS_DIR, slug+'.html')
    os.makedirs(POSTS_DIR, exist_ok=True)
    meta_title = title
    meta_desc = (body_html[:240]).replace('\n',' ').replace('<','').replace('>','')
    html = []
    html.append('<!doctype html>')
    html.append('<html lang="en">')
    html.append('<head>')
    html.append('<meta charset="utf-8">')
    html.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    html.append('<link rel="canonical" href="/blog/posts/'+slug+'.html">')
    html.append('<link rel="preload" href="/assets/css/styles.css" as="style" onload="this.rel=\'stylesheet\'">')
    html.append('<script src="/assets/js/main.js" defer></script>')
    html.append('</head>')
    html.append('<body data-title="'+meta_title+'" data-meta="'+meta_desc+'">')
    html.append('<div id="header"></div>')
    html.append('<main class="container">')
    html.append('<section class="section">')
    html.append('<h1>'+title+'</h1>')
    html.append(body_html)
    html.append('</section>')
    html.append('<div class="in-article-ad ad"></div>')
    html.append('</main>')
    html.append('<div id="footer"></div>')
    html.append('</body>')
    html.append('</html>')
    with open(path,'w',encoding='utf-8') as f:
        f.write('\n'.join(html))
    return path

def section(title, paragraphs):
    s = '<h2>'+title+'</h2>'
    for p in paragraphs:
        s += '<p>'+p+'</p>'
    return s

def long_content(topic, words=5200):
    base = []
    intro = 'This daily analysis explores developments in Indian and global markets, interest rates, corporate earnings, taxation, banking and digital finance. It highlights actionable insights, risk factors, and implementation checklists to navigate investments and personal finance decisions.'
    base.append(section('Overview', [intro]))
    para = 'Policy updates and macro signals influence sector rotations across autos, banks, PSU, IT, pharma and energy. We examine liquidity, credit growth, and global cues from the US Fed, BoE and RBI, translating them into practical asset allocation strategies.'
    base.append(section('Macro Signals', [para]*6))
    para2 = 'Earnings revisions and margin trajectories determine leadership in midcaps vs largecaps. We break down balance sheets, cash flows, and valuations, mapping catalysts like capex, order books, pricing power, and regulatory changes to time entries and exits.'
    base.append(section('Earnings And Valuations', [para2]*6))
    para3 = 'Personal finance implementations cover tax-smart investing, emergency buffers, insurance adequacy, efficient loan repayment, and goal-based SIP ladders. We offer formulas, worked examples, and periodic review routines for disciplined compounding.'
    base.append(section('Personal Finance Implementations', [para3]*6))
    para4 = 'Crypto, digital payments, and fintech rails evolve rapidly. We assess on-chain signals, stablecoin flows, CBDC pilots, and compliance best-practices. We treat high-volatility assets with strict risk budgets and scenario testing.'
    base.append(section('Digital Finance And Crypto', [para4]*6))
    para5 = 'Actionable checklist: define objectives, quantify risk, set allocations, automate contributions, monitor drawdowns, rebalance on thresholds, and avoid leverage spirals. Log decisions and post-mortems to improve process quality over outcomes.'
    base.append(section('Actionable Checklist', [para5]*6))
    faq = [
        ('Is this financial advice?', 'This is educational analysis. Consult a licensed advisor for personalized recommendations.'),
        ('How do I size positions?', 'Use risk budgets, stop-losses, and diversification across uncorrelated assets. Focus on process, not predictions.'),
        ('What is a good SIP routine?', 'Automate monthly contributions, align funds to goals, and review annually for rebalancing and tax-efficiency.'),
    ]
    faq_html = '<h2>FAQs</h2>'
    for q,a in faq:
        faq_html += '<h3>'+q+'</h3><p>'+a+'</p>'
    base.append(faq_html)
    body = ''.join(base)
    while len(body.split()) < words:
        body += section('Market Diary', ['Sector highlights, flows, and catalysts across equities, debt, commodities, and currencies.']*8)
    return body

def update_blog_index(slug, title):
    index_path = os.path.join('blog','index.html')
    try:
        with open(index_path,'r',encoding='utf-8') as f:
            html = f.read()
    except Exception:
        return
    card = '<a class="card" href="/blog/posts/'+slug+'.html"><div>'+title+'</div></a>'
    if card in html:
        return
    parts = html.split('</section>')
    if len(parts) < 2:
        return
    head, tail = parts[0], '</section>'.join(parts[1:])
    inject_at = head.find('<div class="grid"')
    if inject_at == -1:
        return
    head_after = head[:inject_at] + head[inject_at:]
    head_after = head_after.replace('</div></div>', card+'</div></div>', 1)
    new_html = head_after + '</section>' + tail
    with open(index_path,'w',encoding='utf-8') as f:
        f.write(new_html)

def main():
    now = dt.datetime.now()
    t1 = 'Daily Finance Roundup '+now.strftime('%Y-%m-%d')
    t2 = 'Policy And Markets Update '+now.strftime('%Y-%m-%d')
    for t in [t1,t2]:
        body = long_content(t, words=5200)
        path = make_post(t, body)
        slug = os.path.splitext(os.path.basename(path))[0]
        update_blog_index(slug, t)
    print('[OK] generated posts:', t1, '|', t2)

if __name__ == '__main__':
    main()
