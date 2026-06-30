#!/usr/bin/env python3
"""
R42:
1. 用全量 786 篇合并数据更新「S1 vs G1 KOC铺量」panel 的标题与顶部 S1/G1 整体卡片。
2. 优化「全量 786 篇」panel 的方向表排版，拆成 S1/G1 两张表，避免过宽过乱。
3. 保留铺量池方向细分图表，但在其前增加说明。
TARGETS（硬规则）：docs dark + outputs/KOC铺量内容.html + 桌面同步。
"""
import re, json, shutil
from pathlib import Path
import pandas as pd

ROOT = Path('/Users/xiemila/.qoderwork/workspace/mq6ecbjzd6kpfcgy')
TARGETS = [
    ROOT / 'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    ROOT / 'outputs/KOC铺量内容.html',
]
DESKTOP = Path('/Users/xiemila/Desktop/KOC铺量内容.html')


def fmt_num(n, digits=0):
    if digits == 0:
        return f'{int(round(n)):,}'
    return f'{n:,.{digits}f}'


def fmt_wan(n):
    return f'{n/10000:.1f}万'


def safe_div(a, b):
    return a / b if b else 0


def map_main_dir(name: str) -> str:
    if '横测' in name:
        return '横测'
    if '纵测' in name:
        return '纵测'
    if '读书日' in name:
        return '读书日借势'
    if '520' in name:
        return '520热点'
    if '618' in name:
        return '618大促'
    if '场景对比' in name:
        return '场景对比'
    if '明星' in name:
        return '明星热点'
    if '选购攻略' in name:
        return '选购攻略'
    return '其他种草'


# ── 1. rebuild unified rows (same as R40/R41) ──
h_main = TARGETS[0].read_text(encoding='utf-8')
m = re.search(r'function\s+init_s1g1\s*\(', h_main)
i = h_main.index('const DATA = {', m.end())
brace = h_main.find('{', i)
depth = 1
j = brace + 1
while j < len(h_main) and depth > 0:
    if h_main[j] == '{':
        depth += 1
    elif h_main[j] == '}':
        depth -= 1
    j += 1
main_data = json.loads(h_main[brace:j])

rows = []
for row in main_data['s1_dirs']:
    rows.append({
        'product': 'S1', 'direction': map_main_dir(row['内容方向']), 'role': 'KOC',
        'count': row['count'], 'cost': row['总消耗'], 'gmv': row['gmv'],
        'store': row['进店uv'], 'search': row['搜索uv'], 'interact': row['互动量'], 'reads': row['阅读量'],
    })
for row in main_data['g1_dirs']:
    rows.append({
        'product': 'G1', 'direction': map_main_dir(row['内容方向']), 'role': 'KOC',
        'count': row['count'], 'cost': row['总消耗'], 'gmv': row['gmv'],
        'store': row['进店uv'], 'search': row['搜索uv'], 'interact': row['互动量'], 'reads': row['阅读量'],
    })

KOL_G1 = {
    'count': main_data['kol']['g1']['count'], 'cost': main_data['kol']['g1']['total_cost'],
    'gmv': main_data['kol']['g1']['total_gmv'], 'store': main_data['kol']['g1']['total_store'],
    'search': main_data['kol']['g1']['total_search'], 'interact': main_data['kol']['g1']['total_interact'],
    'reads': main_data['kol']['g1']['total_reads'],
}
for row in rows:
    if row['product'] == 'G1' and row['direction'] == '横测' and row['role'] == 'KOC':
        for k in ['count', 'cost', 'gmv', 'store', 'search', 'interact', 'reads']:
            row[k] -= KOL_G1[k]
        break
rows.append({'product': 'G1', 'direction': '横测', 'role': 'KOL', **KOL_G1})

rdf = pd.read_excel('/Users/xiemila/Desktop/【1】如涵国补方向6.29数据汇总.xls', header=0).fillna(0)
for _, r in rdf.iterrows():
    prod = str(r['产品']).upper()
    if prod not in ('S1', 'G1'):
        continue
    rows.append({
        'product': prod, 'direction': str(r['内容方向']).strip() or '国补回搜', 'role': 'KOC',
        'count': 1, 'cost': float(r['总消耗']) if r['总消耗'] else 0, 'gmv': float(r['gmv']) if r['gmv'] else 0,
        'store': int(r['进店uv']) if r['进店uv'] else 0, 'search': int(r['搜索uv']) if r['搜索uv'] else 0,
        'interact': int(r['互动量']) if r['互动量'] else 0, 'reads': int(r['阅读量']) if r['阅读量'] else 0,
    })

jdf = pd.read_excel('/Users/xiemila/Downloads/金咖koc内容.xlsx', header=0).fillna(0)
for _, r in jdf.iterrows():
    prod_raw = str(r['产品'])
    if 'S1' in prod_raw:
        prod = 'S1'
    elif 'G1' in prod_raw:
        prod = 'G1'
    else:
        continue
    rows.append({
        'product': prod, 'direction': str(r['内容方向']).strip(), 'role': 'KOC',
        'count': 1, 'cost': float(r['总消耗']) if r['总消耗'] else 0, 'gmv': float(r['gmv']) if r['gmv'] else 0,
        'store': int(r['进店uv']) if r['进店uv'] else 0, 'search': int(r['搜索uv']) if r['搜索uv'] else 0,
        'interact': int(r['互动量']) if r['互动量'] else 0, 'reads': int(r['阅读量']) if r['阅读量'] else 0,
    })

df_rows = pd.DataFrame(rows)
agg_dict = {'count': 'sum', 'cost': 'sum', 'gmv': 'sum', 'store': 'sum', 'search': 'sum', 'interact': 'sum', 'reads': 'sum'}

def make_total(s):
    d = s.to_dict()
    for k in ('store', 'search', 'interact', 'reads'):
        d[k] = int(d[k])
    return d

total = make_total(df_rows.agg(agg_dict))
role_df = df_rows.groupby('role').agg(agg_dict).reset_index()
role = {}
for _, r in role_df.iterrows():
    rec = make_total(r); rec.pop('role')
    role[r['role']] = rec
    rec['roi'] = safe_div(rec['gmv'], rec['cost'])
prod_df = df_rows.groupby('product').agg(agg_dict).reset_index()
prod = {}
for _, r in prod_df.iterrows():
    rec = make_total(r); rec.pop('product')
    prod[r['product']] = rec
    rec['roi'] = safe_div(rec['gmv'], rec['cost'])

s1_kol_count = int(df_rows[(df_rows['product']=='S1') & (df_rows['role']=='KOL')]['count'].sum())
g1_kol_count = int(df_rows[(df_rows['product']=='G1') & (df_rows['role']=='KOL')]['count'].sum())
s1_koc_count = int(df_rows[(df_rows['product']=='S1') & (df_rows['role']=='KOC')]['count'].sum())
g1_koc_count = int(df_rows[(df_rows['product']=='G1') & (df_rows['role']=='KOC')]['count'].sum())

# ── 2. build split direction tables for mega panel ──
dir_df = df_rows.groupby(['product', 'direction', 'role']).agg(agg_dict).reset_index()
direction_rows = []
for _, r in dir_df.iterrows():
    rec = make_total(r)
    rec.update({'product': r['product'], 'direction': r['direction'], 'role': r['role']})
    rec['roi'] = safe_div(rec['gmv'], rec['cost'])
    direction_rows.append(rec)

def table_rows_for(prod):
    rows_prod = [r for r in direction_rows if r['product'] == prod and r['count'] > 0]
    rows_prod.sort(key=lambda x: x['roi'], reverse=True)
    html = ''
    for r in rows_prod:
        roi_color = '#34d399' if r['roi'] >= 10 else ('#fbbf24' if r['roi'] >= 3 else '#f87171')
        role_badge = '<span class="badge" style="background:#1a56db33;color:#5b9aff">KOC</span>' if r['role'] == 'KOC' else '<span class="badge" style="background:#ff6b6b33;color:#ff8a8a">KOL</span>'
        html += f'''<tr><td>{r['direction']}</td><td>{role_badge}</td><td>{fmt_num(int(r['count']))}</td><td>¥{fmt_num(r['cost'],0)}</td><td>¥{fmt_num(r['gmv'],0)}</td><td style="color:{roi_color};font-weight:700">{r['roi']:.2f}×</td><td>{fmt_num(int(r['store']))}</td><td>{fmt_num(int(r['search']))}</td></tr>'''
    return html

table_s1 = table_rows_for('S1')
table_g1 = table_rows_for('G1')

direction_html = f'''
<div class="section">
  <h2 class="section-title">内容方向效率总表（按产品线拆分）</h2>
  <p class="section-sub">全量 786 篇统一聚合，S1/G1 分别按 ROI 降序；表格可横向滑动</p>
  <div class="product-row mega-dir-row">
    <div class="chart-container">
      <h3>S1 内容方向效率（{fmt_num(prod['S1']['count'])}篇）</h3>
      <div class="table-wrap">
        <table class="top-table mega-table">
          <thead><tr><th>方向</th><th>身份</th><th>篇数</th><th>消耗</th><th>GMV</th><th>ROI</th><th>进店</th><th>搜索</th></tr></thead>
          <tbody>{table_s1}</tbody>
        </table>
      </div>
    </div>
    <div class="chart-container">
      <h3>G1 内容方向效率（{fmt_num(prod['G1']['count'])}篇）</h3>
      <div class="table-wrap">
        <table class="top-table mega-table">
          <thead><tr><th>方向</th><th>身份</th><th>篇数</th><th>消耗</th><th>GMV</th><th>ROI</th><th>进店</th><th>搜索</th></tr></thead>
          <tbody>{table_g1}</tbody>
        </table>
      </div>
    </div>
  </div>
</div>
'''

# ── 3. patch HTML ──
for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')

    # A) update panel-s1g1 header to total numbers
    old_header = '<header><h1>千问 S1 vs G1 KOC铺量效率分析</h1><p>4-6月 · 主力铺量634篇(KOC 600+KOL 34) + 新内容测试152篇(如涵80+金咖72) · 数据截止6.22</p></header>'
    new_header = f'<header><h1>千问 S1 vs G1 全量效率分析</h1><p>4-6月 · 全量 786 篇(KOC {fmt_num(role["KOC"]["count"])} + KOL {fmt_num(role["KOL"]["count"])}) · S1 {fmt_num(prod["S1"]["count"])}篇 · G1 {fmt_num(prod["G1"]["count"])}篇 · 铺量+如涵+金咖统一口径</p></header>'
    h = h.replace(old_header, new_header)

    # B) update first S1/G1 product cards in panel-s1g1
    old_cards = '''<div class="product-row"><div class="product-card s1"><h3>千问 S1 <span class="badge">带屏旗舰款 · 236篇</span></h3><p class="sub">100% KOC执行 · 无KOL投放 · 整体ROI 9.25</p><div class="stats"><div class="stat-item"><div class="v">¥32.1万</div><div class="l">总消耗</div></div><div class="stat-item"><div class="v">¥296.7万</div><div class="l">总GMV</div></div><div class="stat-item"><div class="v">9.25x</div><div class="l">整体ROI</div></div><div class="stat-item"><div class="v">61,286</div><div class="l">进店UV</div></div><div class="stat-item"><div class="v">13,629</div><div class="l">搜索UV</div></div><div class="stat-item"><div class="v">¥12,574</div><div class="l">篇均GMV</div></div></div></div><div class="product-card g1"><h3>千问 G1 <span class="badge">轻量音频款 · 398篇</span></h3><p class="sub">KOC 364篇 + KOL 34篇 · 整体ROI 5.18</p><div class="stats"><div class="stat-item"><div class="v">¥57.1万</div><div class="l">总消耗</div></div><div class="stat-item"><div class="v">¥296.4万</div><div class="l">总GMV</div></div><div class="stat-item"><div class="v">5.18x</div><div class="l">整体ROI</div></div><div class="stat-item"><div class="v">48,649</div><div class="l">进店UV</div></div><div class="stat-item"><div class="v">13,248</div><div class="l">搜索UV</div></div><div class="stat-item"><div class="v">¥7,448</div><div class="l">篇均GMV</div></div></div></div></div>'''

    s1_roi = prod['S1']['roi']
    g1_roi = prod['G1']['roi']
    new_cards = f'''<div class="product-row"><div class="product-card s1"><h3>千问 S1 <span class="badge">带屏旗舰款 · {fmt_num(prod['S1']['count'])}篇</span></h3><p class="sub">KOC {fmt_num(s1_koc_count)}篇{f' + KOL {fmt_num(s1_kol_count)}篇' if s1_kol_count else ''} · 整体ROI {s1_roi:.2f}</p><div class="stats"><div class="stat-item"><div class="v">{fmt_wan(prod['S1']['cost'])}</div><div class="l">总消耗</div></div><div class="stat-item"><div class="v">{fmt_wan(prod['S1']['gmv'])}</div><div class="l">总GMV</div></div><div class="stat-item"><div class="v">{s1_roi:.2f}x</div><div class="l">整体ROI</div></div><div class="stat-item"><div class="v">{fmt_num(prod['S1']['store'])}</div><div class="l">进店UV</div></div><div class="stat-item"><div class="v">{fmt_num(prod['S1']['search'])}</div><div class="l">搜索UV</div></div><div class="stat-item"><div class="v">¥{fmt_num(safe_div(prod['S1']['gmv'], prod['S1']['count']),0)}</div><div class="l">篇均GMV</div></div></div></div><div class="product-card g1"><h3>千问 G1 <span class="badge">轻量音频款 · {fmt_num(prod['G1']['count'])}篇</span></h3><p class="sub">KOC {fmt_num(g1_koc_count)}篇 + KOL {fmt_num(g1_kol_count)}篇 · 整体ROI {g1_roi:.2f}</p><div class="stats"><div class="stat-item"><div class="v">{fmt_wan(prod['G1']['cost'])}</div><div class="l">总消耗</div></div><div class="stat-item"><div class="v">{fmt_wan(prod['G1']['gmv'])}</div><div class="l">总GMV</div></div><div class="stat-item"><div class="v">{g1_roi:.2f}x</div><div class="l">整体ROI</div></div><div class="stat-item"><div class="v">{fmt_num(prod['G1']['store'])}</div><div class="l">进店UV</div></div><div class="stat-item"><div class="v">{fmt_num(prod['G1']['search'])}</div><div class="l">搜索UV</div></div><div class="stat-item"><div class="v">¥{fmt_num(safe_div(prod['G1']['gmv'], prod['G1']['count']),0)}</div><div class="l">篇均GMV</div></div></div></div></div>'''
    h = h.replace(old_cards, new_cards)

    # C) replace mega panel direction table with split tables
    # find the direction section in panel-mega and replace it
    pattern = r'<div class="section">\s*<h2 class="section-title">内容方向效率总表[^<]*</h2>\s*<p class="section-sub">[^<]*</p>\s*<div class="chart-container" style="overflow-x:auto;">\s*<table class="top-table mega-table">.*?</table>\s*</div>\s*</div>'
    h = re.sub(pattern, direction_html, h, flags=re.DOTALL)

    # D) add note before S1 direction细分 section that铺量 charts are铺量-only
    note = '''<div class="callout-decay" style="margin: 16px 0;"><strong>说明：</strong>以下「S1 内容方向细分」「G1 内容方向细分」等图表仍基于铺量池 634 篇的原始方向明细；786 篇全量合并视图请切「🌍 全量 786 篇」tab。</div>'''
    marker = '<!-- ═══ S1 细分 ═══ -->'
    if note not in h:
        h = h.replace(marker, note + marker)

    # E) extra CSS for split tables and layout
    extra_css = '''
/* ── R42 layout fixes ── */
.mega-dir-row { align-items: flex-start; }
.mega-dir-row .chart-container { min-width: 0; }
.mega-dir-row .table-wrap { overflow-x: auto; }
.panel-mega .mega-table td:first-child { min-width: 100px; max-width: 180px; white-space: normal; }
.panel-mega .mega-table th, .panel-mega .mega-table td { font-size: 11px; padding: 7px 5px; }
@media (max-width: 900px) {
  .mega-dir-row { grid-template-columns: 1fr; }
}
'''
    if '/* ── R42 layout fixes ── */' not in h:
        h = h.replace('</style>', extra_css + '</style>', 1)

    tgt.write_text(h, encoding='utf-8')
    print(f'✓ patched {tgt.relative_to(ROOT)}')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')
