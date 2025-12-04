import os
import json
import re
import hashlib
from datetime import datetime

OUT_DIR = os.path.join('news','originals')

def slugify(text):
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text or '')
    text = re.sub(r'\s+', '-', text.strip())
    return (text.lower()[:80] or 'news')

def keywords_from_headline(h):
    if not h:
        return ''
    words = [w for w in re.split(r'[\s,\-:|]+', h) if w and w.lower() not in {'the','and','or','a','an','of','for','to','in','on','with','by','from','as'}]
    return ' '.join(words[:6])

def unique_headline(headline):
    kw = keywords_from_headline(headline)
    return (kw + ' — Markets & Investors Explained').strip()

def meta_title(headline):
    return ('Finance Update: ' + keywords_from_headline(headline)).strip()[:60]

def meta_desc(desc, headline):
    base = (desc or '')
    base = re.sub(r'<[^>]+>', ' ', base)
    base = ' '.join(base.split())
    if not base:
        base = 'Detailed finance analysis in simple Hinglish with market impact, investor takeaways and context.'
    return base[:160]

def build_paragraphs(headline, summary):
    kw = keywords_from_headline(headline)
    summ = summary or ''
    summ = ' '.join(re.sub(r'<[^>]+>', ' ', summ).split())
    opening = f"Aaj ki headline: {kw}. Ye development markets ke liye kyun important hai? Simple words mein samjhte hain — kya hua, kya impact ho sakta hai, aur investors ko kya dekhna chahiye."
    main = f"Story ka core kya hai: iss update ka direct link profitability, liquidity, aur sentiment se aata hai. Company/sector level par pricing, demand cycles, aur regulation ke mix ki wajah se near-term volatility dekhne ko mil sakti hai. Hinglish style mein seedha point: jo numbers aur guidelines aayi hain, unka real-world effect portfolio decisions par padta hai."
    ctx = f"Background samajhna zaroori hai: pichhle quarters ke trends, policy stance (RBI/Fed), aur industry-specific catalysts ke basis par ye move expected/unexpected dono ho sakta hai. History batati hai ki jab {kw} jaisi headlines aati hain, to market participants pehle risk ko quantify karte hain, phir allocation readjust karte hain."
    impact = f"Markets/Investors impact: equities, debt, aur commodities par ripple effect aata hai. Short-term mein positioning aur flows change hote hain; long-term mein fundamentals dominate karte hain. Retail investors ke liye: goal-based SIPs, drawdown management, aur diversification pe focus rakho. Traders ke liye: risk budgets aur stop-loss discipline maintain karo."
    analysis = f"Humari interpretation: is development ko binary tarah se mat dekho. Scenarios banao — best, base, worst. Cash flows, margins, aur valuations ko saath mein read karo. Agar {kw} ke around uncertainty high lag rahi hai, to staggered entries aur evidence-based updates better rehte hain."
    more = f"Simple explanation: numbers aur narratives ko mix karke clarity milti hai. Agar summary mein {summ[:140]} mention hua hai, to usse context milta hai, lekin article rewriting hamesha fresh language mein hai — koi sentence copy nahi, sirf concept explain."
    concl = f"Conclusion: headlines fast aati hain, lekin process slow aur disciplined rehna chahiye. Investors ko apni risk appetite ke hisaab se steps lene chahiye: objectives set karo, allocations define karo, periodic reviews rakho. Market noise ko filter karke, data-driven approach follow karo."
    return opening, main, ctx, impact, analysis, more, concl

def write_article(item):
    os.makedirs(OUT_DIR, exist_ok=True)
    title = item.get('title','')
    summary = ''
    source = item.get('source','')
    link = item.get('link','')
    image = (item.get('image') or 'https://source.unsplash.com/1200x675/?markets,finance')
    h = hashlib.sha1((link or title).encode('utf-8')).hexdigest()[:8]
    slug_base = slugify(title)
    slug = slug_base+'-'+h
    mt = meta_title(title)
    md = meta_desc(summary, title)
    h1 = unique_headline(title)
    opening, main, ctx, impact, analysis, more, concl = build_paragraphs(title, summary)
    sections = [
        ('Opening','opening'),
        ('Main Story','main-story'),
        ('Context & Background','context-background'),
        ('Market/Investor Impact','market-investor-impact'),
        ('Analysis','analysis'),
        ('Simple Explanation','simple-explanation'),
        ('Conclusion','conclusion')
    ]
    lines = []
    lines.append('<!doctype html>')
    lines.append('<html lang="en">')
    lines.append('<head>')
    lines.append('<meta charset="utf-8">')
    lines.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    lines.append('<meta name="title" content="'+mt+'">')
    lines.append('<meta name="description" content="'+md+'">')
    lines.append('<meta property="og:title" content="'+mt+'">')
    lines.append('<meta property="og:description" content="'+md+'">')
    lines.append('<meta property="og:url" content="/news/originals/'+slug+'.html">')
    lines.append('<meta property="og:image" content="'+image+'">')
    lines.append('<link rel="stylesheet" href="/assets/css/styles.css">')
    lines.append('<link rel="canonical" href="/news/originals/'+slug+'.html">')
    lines.append('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7510164795562884" crossorigin="anonymous"></script>')
    lines.append('<script src="/assets/js/main.js" defer></script>')
    lines.append('</head>')
    lines.append('<body data-title="'+mt+'" data-meta="'+md+'">')
    lines.append('<div id="header"></div>')
    lines.append('<main class="container">')
    lines.append('<section class="section">')
    lines.append('<h1>'+h1+'</h1>')
    lines.append('<figure class="card"><img src="'+image+'" alt="'+h1+'" loading="lazy" referrerpolicy="no-referrer"><figcaption style="color:#9ca3af">News image</figcaption></figure>')
    # Table of contents
    lines.append('<nav class="toc" aria-label="Table of Contents"><h2>Table of Contents</h2><ul>'+'\n'.join('<li><a href="#'+sid+'">'+nm+'</a></li>' for nm,sid in sections)+'</ul></nav>')
    lines.append('<h2 id="opening">Opening</h2>')
    lines.append('<p>'+opening+'</p>')
    lines.append('<h2 id="main-story">Main Story</h2>')
    lines.append('<p>'+main+'</p>')
    lines.append('<h2 id="context-background">Context & Background</h2>')
    lines.append('<p>'+ctx+'</p>')
    lines.append('<h2 id="market-investor-impact">Market/Investor Impact</h2>')
    lines.append('<p>'+impact+'</p>')
    lines.append('<h2 id="analysis">Analysis</h2>')
    lines.append('<p>'+analysis+'</p>')
    lines.append('<h2 id="simple-explanation">Simple Explanation</h2>')
    lines.append('<p>'+more+'</p>')
    lines.append('<h2 id="conclusion">Conclusion</h2>')
    lines.append('<p>'+concl+'</p>')
    lines.append('<div class="card"><h3>Helpful Links</h3><p><a href="/blog/index.html">Blog Home</a> • <a href="/tools/emi.html">EMI Calculator</a> • <a href="/tools/income-tax.html">Income Tax Calculator</a> • <a href="/tools/sip.html">SIP Calculator</a></p></div>')
    lines.append('<p>Source: <a href="'+link+'" target="_blank" rel="nofollow noopener">'+(source or 'external link')+'</a></p>')
    lines.append('</section>')
    lines.append('</main>')
    lines.append('<div id="footer"></div>')
    # Article JSON-LD
    lines.append('<script type="application/ld+json">'+json.dumps({
        "@context":"https://schema.org",
        "@type":"Article",
        "headline": mt,
        "image": image,
        "mainEntityOfPage": '/news/originals/'+slug+'.html',
        "datePublished": datetime.utcnow().isoformat()+"Z",
        "author": {"@type":"Organization","name":"MoneyMarket"}
    })+'</script>')
    lines.append('</body>')
    lines.append('</html>')
    out_path = os.path.join(OUT_DIR, slug+'.html')
    with open(out_path,'w',encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return slug

def main():
    data_path = os.path.join('assets','data','news.json')
    try:
        with open(data_path,'r',encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        print('[ERR] news.json not found')
        return
    items = data.get('items', [])
    count = 0
    for it in items[:60]:
        slug = write_article(it)
        it['orig_slug'] = slug
        count += 1
    with open(data_path,'w',encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('[OK] generated originals:', count)

if __name__ == '__main__':
    main()
