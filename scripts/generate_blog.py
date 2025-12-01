import os
import datetime as dt
import re
import json

POSTS_DIR = os.path.join('blog','posts')

def slugify(text):
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    return text.lower()

def news_highlights(limit=5):
    try:
        with open(os.path.join('assets','data','news.json'),'r',encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return ''
    items = data.get('items') or []
    html = '<h2>Daily Highlights</h2>'
    count = 0
    for it in items:
        if count >= limit:
            break
        title = it.get('title') or ''
        link = it.get('link') or ''
        src = it.get('source') or ''
        date = it.get('pubDate') or ''
        img = it.get('image') or ''
        card = '<div class="card">'
        if img:
            card += '<img class="thumb" src="'+img+'" alt="'+title+'">'
        card += '<a href="'+link+'" rel="nofollow noopener" target="_blank">'+title+'</a>'
        meta = (src+' • '+date).strip()
        card += '<p>'+meta+'</p>'
        card += '</div>'
        html += card
        count += 1
    return html

def make_post(title, body_html):
    date = dt.date.today().isoformat()
    slug = slugify(title) + '-' + dt.datetime.now().strftime('%H%M')
    path = os.path.join(POSTS_DIR, slug+'.html')
    os.makedirs(POSTS_DIR, exist_ok=True)
    meta_title = title
    text = re.sub(r'<[^>]+>', ' ', body_html)
    text = ' '.join(text.split())
    meta_desc = text[:240]
    html = []
    html.append('<!doctype html>')
    html.append('<html lang="en">')
    html.append('<head>')
    html.append('<meta charset="utf-8">')
    html.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    html.append('<link rel="canonical" href="/blog/posts/'+slug+'.html">')
    html.append('<link rel="preload" href="/assets/css/styles.css" as="style" onload="this.rel=\'stylesheet\'">')
    html.append('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7510164795562884" crossorigin="anonymous"></script>')
    html.append('<script src="/assets/js/main.js" defer></script>')
    html.append('</head>')
    html.append('<body data-title="'+meta_title+'" data-meta="'+meta_desc+'">')
    html.append('<div id="header"></div>')
    html.append('<main class="container">')
    html.append('<section class="section">')
    html.append('<h1>'+title+'</h1>')
    html.append(news_highlights())
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

def fill_words(body, words):
    while len(body.split()) < words:
        body += section('Market Diary', ['Sector highlights, flows, and catalysts across equities, debt, commodities, and currencies.']*8)
    return body

def content_roundup():
    base = []
    base.append(section('Overview', ['Daily analysis across markets, macro, earnings, and personal finance implementations for India.']))
    base.append(section('Macro Signals', ['Policy shifts, liquidity and rates drive sector rotations across autos, banks, PSU, IT, pharma and energy.']*6))
    base.append(section('Earnings And Valuations', ['Balance sheets, cash flows and order books shape leadership in midcaps vs largecaps.']*6))
    base.append(section('Personal Finance Implementations', ['Tax-smart investing, buffers, insurance adequacy, efficient loan repayment, and SIP ladders.']*6))
    base.append(section('Digital Finance And Crypto', ['On-chain signals, CBDC pilots, stablecoin flows and compliance best-practices.']*6))
    base.append(section('Actionable Checklist', ['Define objectives, quantify risk, set allocations, automate, rebalance and review decisions.']*6))
    faq_html = '<h2>FAQs</h2>'
    faq_html += '<h3>Is this financial advice?</h3><p>This is educational analysis. Consult a licensed advisor for personalized recommendations.</p>'
    faq_html += '<h3>What is a good SIP routine?</h3><p>Automate monthly contributions, align funds to goals, and review annually for rebalancing and tax-efficiency.</p>'
    base.append(faq_html)
    return ''.join(base)

def content_sector(sector):
    base = []
    base.append(section('Sector Overview: '+sector, ['Drivers, competitive landscape, capital cycles and regulatory backdrop influencing performance.']))
    base.append(section('Earnings And Margins', ['Order books, pricing power, input costs and capacity utilization determine earnings trajectories.']*6))
    base.append(section('Valuation And Flows', ['Multiples relative to history and peers, domestic/institutional flows, and catalysts.']*6))
    base.append(section('Risk And Scenarios', ['Regulatory shifts, funding stress, demand cyclicality, FX and policy outcomes.']*6))
    base.append(section('Implementation', ['Entry/exit frameworks, position sizing, and tracking KPIs to validate theses.']*6))
    return ''.join(base)

def content_tax():
    base = []
    base.append(section('Policy Updates', ['Recent changes in income tax, GST, TDS/TCS and compliance timelines.']*6))
    base.append(section('Planning', ['Optimize deductions, exemptions, HRA, 80C/80D/80G, and use tax-efficient instruments.']*6))
    base.append(section('Compliance', ['Returns, advance tax, audit thresholds, invoicing and documentation routines.']*6))
    base.append(section('Case Studies', ['Worked examples and formulas with salaried, business and investor profiles.']*6))
    return ''.join(base)

def content_sip():
    base = []
    base.append(section('SIP Basics', ['Compounding, rupee-cost averaging, and goal-aligned portfolios.']*6))
    base.append(section('Portfolio Design', ['Equity/debt mix, factor exposures, and rebalancing thresholds.']*6))
    base.append(section('Execution', ['Automate contributions, review annually, manage drawdowns and avoid leverage.']*6))
    base.append(section('Examples', ['Worked examples across horizons: child education, home purchase, retirement.']*6))
    return ''.join(base)

def content_psu_banks():
    base = []
    base.append(section('PSU Banks Overview', ['Balance sheet strength, NPA trends, credit growth and capital adequacy underpin performance.']))
    base.append(section('Earnings Drivers', ['Loan mix, yield compression, cost of funds, fee income and provisioning cycles.']*6))
    base.append(section('Valuation And Flows', ['Multiples vs history and peers, domestic/institutional flows and government catalysts.']*6))
    base.append(section('Risk And Governance', ['Asset quality, interest rate sensitivity, governance, and regulatory developments.']*6))
    base.append(section('Implementation', ['Entry frameworks, risk budgeting, position sizing and exit disciplines.']*6))
    return ''.join(base)

def content_auto_monthly_dispatch():
    base = []
    base.append(section('Auto Monthly Dispatch Overview', ['OEM volumes, segment mix, exports and inventory trends inform near-term momentum.']))
    base.append(section('Pricing And Input Costs', ['Commodity baskets, discounts, model cycles and supply chain dynamics.']*6))
    base.append(section('Channels And Financing', ['Dealer health, retail registrations, financing availability and rate impacts.']*6))
    base.append(section('Valuation And Triggers', ['Order books, launches, margins and regulatory changes affecting volumes.']*6))
    base.append(section('Implementation', ['Data tracking routines, thesis validation KPIs and timing entries/exits.']*6))
    return ''.join(base)

def content_tax_breakouts():
    base = []
    base.append(section('Latest Tax Rule Breakouts', ['Recent notifications across income tax, GST, TDS/TCS and compliance windows.']*6))
    base.append(section('What Changed', ['Scope, thresholds, rates and documentation implications for individuals and businesses.']*6))
    base.append(section('How To Implement', ['Checklist-driven steps, examples and formula applications to remain compliant and efficient.']*6))
    base.append(section('FAQs', ['Clarifications on common edge cases encountered in filings and reconciliations.']*6))
    return ''.join(base)

def update_blog_index(slug, title):
    index_path = os.path.join('blog','index.html')
    try:
        with open(index_path,'r',encoding='utf-8') as f:
            html = f.read()
    except Exception:
        return
    card = '<div class="card"><h3><a href="/blog/posts/'+slug+'.html">'+title+'</a></h3><p>New analysis and implementations.</p></div>'
    if card in html:
        return
    start = html.find('<section class="section">')
    end = html.find('</section>', start+1)
    if start == -1 or end == -1:
        return
    first = html[start:end]
    grid_start = first.find('<div class="grid">')
    if grid_start == -1:
        return
    grid_close = first.rfind('</div>')
    if grid_close == -1:
        return
    before = html[:start]
    inside = first[:grid_close] + card + first[grid_close:]
    after = html[end:]
    new_html = before + inside + after
    with open(index_path,'w',encoding='utf-8') as f:
        f.write(new_html)

def main():
    now = dt.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    t1 = 'Daily Finance Roundup '+date_str
    sectors = ['Autos','Banks','PSU','IT','Pharma','Energy']
    rot = ['Sector', 'Tax', 'SIP', 'PSU', 'AutosDispatch', 'TaxBreakouts']
    sel = rot[now.timetuple().tm_yday % len(rot)]
    if sel == 'Sector':
        sector = sectors[now.timetuple().tm_yday % len(sectors)]
        t2 = 'Sector Deep Dive: '+sector+' '+date_str
        body2 = content_sector(sector)
        body2 = fill_words(body2, 5200)
    elif sel == 'Tax':
        t2 = 'Tax Changes And Planning '+date_str
        body2 = content_tax()
        body2 = fill_words(body2, 5200)
    elif sel == 'SIP':
        t2 = 'SIP Strategies And Portfolio Design '+date_str
        body2 = content_sip()
        body2 = fill_words(body2, 5200)
    elif sel == 'PSU':
        t2 = 'PSU Bank Updates '+date_str
        body2 = content_psu_banks()
        body2 = fill_words(body2, 5200)
    elif sel == 'AutosDispatch':
        t2 = 'Auto Monthly Dispatches '+date_str
        body2 = content_auto_monthly_dispatch()
        body2 = fill_words(body2, 5200)
    else:
        t2 = 'Tax Rule Breakouts '+date_str
        body2 = content_tax_breakouts()
        body2 = fill_words(body2, 5200)
    body1 = content_roundup()
    body1 = fill_words(body1, 5200)
    for t, b in [(t1, body1), (t2, body2)]:
        path = make_post(t, b)
        slug = os.path.splitext(os.path.basename(path))[0]
        update_blog_index(slug, t)
    print('[OK] generated posts:', t1, '|', t2)

if __name__ == '__main__':
    main()
