import re
import glob
import os
from datetime import datetime

os.chdir("reports")

# ── 解析大盘复盘 ──────────────────────────────────────────
def parse_market(md):
    date = re.search(r'(\d{4}-\d{2}-\d{2})', md)
    date = date.group(1) if date else datetime.now().strftime('%Y-%m-%d')

    indices = []
    for m in re.finditer(r'\*\*(.+?)\*\*.*?(\d[\d,]+\.?\d*)\s*\(([↑↓][^\)]+)\)', md):
        name, val, chg = m.group(1), m.group(2), m.group(3)
        cls = 'up' if '↑' in chg else 'down'
        indices.append((name, val, chg, cls))

    vol = re.search(r'两市成交额.*?(\d+亿)', md)
    vol = vol.group(1) if vol else '--'

    up = re.search(r'上涨家数.*?(\d+)', md)
    dn = re.search(r'下跌家数.*?(\d+)', md)
    up = up.group(1) if up else '--'
    dn = dn.group(1) if dn else '--'

    return date, indices, vol, up, dn

# ── 解析个股报告 ──────────────────────────────────────────
def parse_stocks(md):
    summary = {'buy': 0, 'hold': 0, 'sell': 0, 'total': 0}
    sm = re.search(r'共分析\s*\*\*(\d+)\*\*', md)
    if sm:
        summary['total'] = int(sm.group(1))
    bm = re.search(r'买入:(\d+)', md)
    hm = re.search(r'观望:(\d+)', md)
    sem = re.search(r'卖出:(\d+)', md)
    if bm: summary['buy'] = int(bm.group(1))
    if hm: summary['hold'] = int(hm.group(1))
    if sem: summary['sell'] = int(sem.group(1))

    # 先从摘要行提取评分
    score_map = {}
    for m in re.finditer(r'[🟢🟡🔴⚪]\s*\*\*(.+?)\((\d+)\)\*\*.*?评分\s*(\d+)', md):
        name = m.group(1).strip()
        score_map[name] = int(m.group(3))

    stocks = []
    # 按 ## emoji 股票名 (代码) 分块，支持 🟡🟢🔴⚪
    headers = re.findall(r'## ([🟡🟢🔴⚪]) (.+?) \((\d+)\)', md)
    blocks = re.split(r'\n## [🟡🟢🔴⚪].+?\n', md)

    for i, header in enumerate(headers):
        emoji, name, code = header
        block = blocks[i+1] if i+1 < len(blocks) else ''

        # 信号判断 — 支持⚪观望
        if emoji == '🟢':
            sig_cls, sig_label = 'buy', '买入'
        elif emoji == '🔴':
            sig_cls, sig_label = 'sell', '卖出'
        else:
            sig_cls, sig_label = 'hold', '观望'

        # 评分 — 先从摘要取，再从块内取
        score = score_map.get(name, None)
        if score is None:
            score_m = re.search(r'评分\s*(\d+)', block)
            score = int(score_m.group(1)) if score_m else 50

        # 评分颜色
        if score >= 65:
            score_color = '#3fb950'
        elif score <= 35:
            score_color = '#f85149'
        else:
            score_color = '#e3b341'

        # 一句话决策（支持 > **一句话决策**: 格式）
        decision_m = re.search(r'一句话决策\*?\*?[：:]\*?\*?\s*(.+)', block)
        decision = decision_m.group(1).strip().strip('*') if decision_m else '暂无分析'
        if '分析过程出错' in decision or 'All LLM' in decision:
            decision = '等待下次分析结果'
        if len(decision) > 80:
            decision = decision[:80] + '...'

        # 关键数据
        close_m = re.search(r'\|\s*([\d.]+)\s*\|.*?\|\s*([\d.+-]+%)\s*\|', block)
        close = close_m.group(1) if close_m else '--'
        change = close_m.group(2) if close_m else '--'
        change_color = '#3fb950' if close_m and '+' in close_m.group(2) else '#f85149' if close_m and '-' in close_m.group(2) else '#e6edf3'

        stocks.append({
            'name': name, 'code': code,
            'sig_cls': sig_cls, 'sig_label': sig_label,
            'score': score, 'score_color': score_color,
            'decision': decision,
            'close': close, 'change': change, 'change_color': change_color,
        })

    return summary, stocks

# ── 读取文件 ──────────────────────────────────────────────
market_md = ''
for f in sorted(glob.glob('market_review_*.md'), reverse=True)[:1]:
    market_md = open(f, encoding='utf-8').read()

report_md = ''
for f in sorted(glob.glob('report_*.md'), reverse=True)[:1]:
    report_md = open(f, encoding='utf-8').read()

date, indices, vol, up_cnt, dn_cnt = parse_market(market_md) if market_md else (datetime.now().strftime('%Y-%m-%d'), [], '--', '--', '--')
summary, stocks = parse_stocks(report_md) if report_md else ({'buy':0,'hold':0,'sell':0,'total':0}, [])

# ── 生成 HTML ─────────────────────────────────────────────
def index_row(name, val, chg, cls):
    color = '#3fb950' if cls == 'up' else '#f85149'
    return f'<div class="market-item"><span class="label">{name}</span><span class="value" style="color:{color}">{val} {chg}</span></div>'

indices_html = '\n'.join(index_row(*i) for i in indices) if indices else ''
indices_html += f'''
<div class="market-item"><span class="label">两市成交额</span><span class="value" style="color:#e3b341">{vol}</span></div>
<div class="market-item"><span class="label">上涨/下跌</span><span class="value">{up_cnt} / {dn_cnt}</span></div>
'''

def card_html(s):
    border_color = '#3fb950' if s['sig_cls']=='buy' else '#f85149' if s['sig_cls']=='sell' else '#e3b341'
    badge_bg = '#0d2f17' if s['sig_cls']=='buy' else '#2d0f0f' if s['sig_cls']=='sell' else '#2d2208'
    close_html = f'<div class="close-price"><span style="color:{s["change_color"]}">{s["close"]} {s["change"]}</span></div>' if s['close'] != '--' else ''
    return f'''
<div class="card" style="border-left:4px solid {border_color}">
  <div class="card-header">
    <div>
      <div class="stock-name">{s['name']}</div>
      <div class="stock-code">{s['code']}</div>
    </div>
    <div style="text-align:right">
      <span class="signal-badge" style="background:{badge_bg};color:{border_color};border:1px solid {border_color}">{s['sig_label']}</span>
      {close_html}
    </div>
  </div>
  <div class="score-bar">
    <span class="score-label">评分</span>
    <div class="bar-bg"><div class="bar-fill" style="width:{s['score']}%;background:{s['score_color']}"></div></div>
    <span style="font-size:0.8rem;color:{s['score_color']};min-width:24px">{s['score']}</span>
  </div>
  <div class="decision">{s['decision']}</div>
</div>'''

cards_html = '\n'.join(card_html(s) for s in stocks)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{date} 决策仪表盘</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#e6edf3;font-family:'PingFang SC','Microsoft YaHei',sans-serif;padding:20px}}
.header{{text-align:center;padding:24px 0 20px;border-bottom:1px solid #21262d}}
.header h1{{font-size:1.6rem;font-weight:700;color:#f0f6fc;letter-spacing:2px}}
.header .sub{{color:#8b949e;font-size:0.85rem;margin-top:6px}}
.market-bar{{display:flex;gap:16px;margin:16px 0;padding:12px 16px;background:#161b22;border-radius:8px;border:1px solid #21262d;flex-wrap:wrap}}
.market-item{{display:flex;flex-direction:column;gap:2px}}
.market-item .label{{font-size:0.75rem;color:#8b949e}}
.market-item .value{{font-size:0.95rem;font-weight:600;color:#e6edf3}}
.summary{{display:flex;gap:12px;justify-content:center;margin:14px 0}}
.sum-item{{padding:6px 18px;border-radius:20px;font-size:0.85rem;font-weight:600}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-top:16px}}
.card{{background:#161b22;border:1px solid #21262d;border-radius:10px;padding:16px}}
.card-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}}
.stock-name{{font-size:1.05rem;font-weight:700;color:#f0f6fc}}
.stock-code{{font-size:0.75rem;color:#8b949e;margin-top:2px}}
.signal-badge{{padding:3px 10px;border-radius:20px;font-size:0.75rem;font-weight:600;display:inline-block}}
.close-price{{font-size:0.8rem;margin-top:4px;text-align:right}}
.score-bar{{display:flex;align-items:center;gap:8px;margin:8px 0}}
.score-label{{font-size:0.75rem;color:#8b949e;width:30px}}
.bar-bg{{flex:1;height:6px;background:#21262d;border-radius:3px}}
.bar-fill{{height:100%;border-radius:3px}}
.decision{{font-size:0.85rem;color:#c9d1d9;margin-top:10px;padding:8px 10px;background:#0d1117;border-radius:6px;border-left:3px solid #30363d;line-height:1.5}}
.footer{{text-align:center;color:#484f58;font-size:0.75rem;margin-top:24px;padding-top:16px;border-top:1px solid #21262d}}
@media(max-width:600px){{.grid{{grid-template-columns:1fr}}.market-bar{{gap:10px}}}}
</style>
</head>
<body>
<div class="header">
  <h1>⚔ {date} 决策仪表盘</h1>
  <div class="sub">共分析 {summary['total']} 只股票 | AI 驱动智能分析</div>
</div>
<div class="market-bar">
{indices_html}
</div>
<div class="summary">
  <span class="sum-item" style="background:#0d2f17;color:#3fb950">买入 {summary['buy']}</span>
  <span class="sum-item" style="background:#2d2208;color:#e3b341">观望 {summary['hold']}</span>
  <span class="sum-item" style="background:#2d0f0f;color:#f85149">卖出 {summary['sell']}</span>
</div>
<div class="grid">
{cards_html}
</div>
<div class="footer">由 daily_stock_analysis 自动生成 · {date}</div>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"index.html generated — {len(stocks)} stocks, buy:{summary['buy']} hold:{summary['hold']} sell:{summary['sell']}")
