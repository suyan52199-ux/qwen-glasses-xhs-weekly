#!/usr/bin/env python3
"""
R44: 用 /Users/xiemila/Desktop/4-6月koc、kol笔记效果(2).xlsx 重新计算主池(KOC 600 + KOL 34)数据，
并同步更新 panel-s1g1 与 panel-mega 全量 786 视图。
"""
import re, json, shutil, math
from pathlib import Path
import pandas as pd

ROOT = Path('/Users/xiemila/.qoderwork/workspace/mq6ecbjzd6kpfcgy')
TARGETS = [
    ROOT / 'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    ROOT / 'outputs/KOC铺量内容.html',
]
DESKTOP = Path('/Users/xiemila/Desktop/KOC铺量内容.html')
XLSX = Path('/Users/xiemila/Desktop/4-6月koc、kol笔记效果(2).xlsx')

DIRECTION_ORDER = ['G1横测','选购攻略','S1横测','S1热点520','S1热点618','S1热点场景对比','S1热点明星','S1热点读书日','S1纵测']
ROLES = ['KOC','KOL']


def safe_div(a, b): return a / b if b else 0


def extract_note_id(url):
    if not isinstance(url, str): return ''
    for pat in [r'/explore/([0-9a-f]+)', r'/discovery/item/([0-9a-f]+)']:
        m = re.search(pat, url)
        if m: return m.group(1)
    return ''


def map_direction(direction: str) -> tuple:
    d = str(direction)
    if 'S1vs' in d or 'S1 vs' in d or 'S1纵测' in d:
        return 'S1', 'S1纵测'
    if 'S1竞品多测' in d or ('S1' in d and '横测' in d):
        return 'S1', 'S1横测'
    if 'G1抠图横测' in d or ('G1' in d and '横测' in d):
        return 'G1', 'G1横测'
    if 'G1选购攻略' in d or '选购攻略' in d:
        return 'G1', '选购攻略'
    if '520' in d:
        return 'S1', 'S1热点520'
    if '618' in d:
        return 'S1', 'S1热点618'
    if '场景对比' in d:
        return 'S1', 'S1热点场景对比'
    if '明星' in d:
        return 'S1', 'S1热点明星'
    if '读书日' in d:
        return 'S1', 'S1热点读书日'
    # fallback
    if d.startswith('S1'): return 'S1', 'S1横测'
    if d.startswith('G1'): return 'G1', 'G1横测'
    return 'G1', '选购攻略'


# ── 1. load main pool ──
koc_df = pd.read_excel(XLSX, sheet_name='数据底表').fillna(0)
num_cols = ['总消耗','进店UV','阅读量','互动量','搜索进店uv','GMV','ROI']
for c in num_cols:
    koc_df[c] = pd.to_numeric(koc_df[c], errors='coerce').fillna(0)
# direction is sometimes 0 in duplicated rows; fill from same link with non-zero direction
link_dir = koc_df[koc_df['方向'] != 0].drop_duplicates('发布返链').set_index('发布返链')['方向'].to_dict()
koc_df['方向'] = koc_df.apply(lambda r: link_dir.get(r['发布返链'], r['方向']), axis=1)
# keep one row per link (max cumulative metrics)
koc_df = koc_df.loc[koc_df.groupby('发布返链')['GMV'].idxmax()].reset_index(drop=True)
# drop rows without valid direction/link
koc_df = koc_df[(koc_df['方向'] != 0) & (koc_df['发布返链'].astype(str).str.startswith('http'))].reset_index(drop=True)

main_rows = []
for _, r in koc_df.iterrows():
    prod, dire = map_direction(str(r['方向']))
    url = str(r['发布返链']) if r['发布返链'] else ''
    main_rows.append({
        'product': prod, 'direction': dire, 'role': 'KOC',
        'name': str(r['昵称']) if r['昵称'] else '',
        'count': 1, 'cost': float(r['总消耗']), 'gmv': float(r['GMV']),
        'store': int(r['进店UV']), 'search': int(r['搜索进店uv']),
        'interact': int(r['互动量']), 'reads': int(r['阅读量']),
        'roi': float(r['ROI']), 'url': url, 'noteId': extract_note_id(url),
        'title': f"{dire} | {r['昵称']}",
    })

kol_df = pd.read_excel(XLSX, sheet_name='kol（数据截止到6.28）').fillna(0)
num_cols_kol = ['总消耗','进店uv','阅读量','互动量','搜索uv','gmv','roi']
for c in num_cols_kol:
    kol_df[c] = pd.to_numeric(kol_df[c], errors='coerce').fillna(0)
for _, r in kol_df.iterrows():
    url = str(r['内容链接']) if r['内容链接'] else ''
    main_rows.append({
        'product': 'G1', 'direction': 'G1横测', 'role': 'KOL',
        'name': str(r['达人昵称']) if r['达人昵称'] else '',
        'count': 1, 'cost': float(r['总消耗']), 'gmv': float(r['gmv']),
        'store': int(r['进店uv']), 'search': int(r['搜索uv']),
        'interact': int(r['互动量']), 'reads': int(r['阅读量']),
        'roi': float(r['roi']), 'url': url, 'noteId': extract_note_id(url),
        'title': f"G1横测 | {r['达人昵称']}",
    })

main_df = pd.DataFrame(main_rows)

# ── 2. helpers ──
def summary_from(s):
    count = int(s['count'].sum())
    return {
        'count': count,
        'total_cost': round(float(s['cost'].sum()), 3),
        'total_gmv': round(float(s['gmv'].sum()), 3),
        'total_store': int(s['store'].sum()),
        'total_interact': int(s['interact'].sum()),
        'total_search': int(s['search'].sum()),
        'total_reads': int(s['reads'].sum()),
        'roi': round(safe_div(s['gmv'].sum(), s['cost'].sum()), 2),
        'with_gmv': int((s['gmv'] > 0).sum()),
        'with_gmv_pct': round(100 * (s['gmv'] > 0).sum() / count, 1) if count else 0,
        'avg_cost': round(safe_div(s['cost'].sum(), count)),
        'avg_interact': round(safe_div(s['interact'].sum(), count)),
        'avg_store': round(safe_div(s['store'].sum(), count), 1),
        'avg_search': round(safe_div(s['search'].sum(), count), 1),
        'avg_gmv': round(safe_div(s['gmv'].sum(), count)),
        'avg_reads': round(safe_div(s['reads'].sum(), count)),
    }

def add_label(d, label):
    d['label'] = label
    return d

# overall / koc / kol
overall = {'s1': add_label(summary_from(main_df[main_df['product']=='S1']), 'S1'),
           'g1': add_label(summary_from(main_df[main_df['product']=='G1']), 'G1')}
koc = {'s1': add_label(summary_from(main_df[(main_df['role']=='KOC') & (main_df['product']=='S1')]), 'S1·KOC'),
       'g1': add_label(summary_from(main_df[(main_df['role']=='KOC') & (main_df['product']=='G1')]), 'G1·KOC')}
# kol s1 none
kol_s1 = None
kol_g1 = add_label(summary_from(main_df[(main_df['role']=='KOL') & (main_df['product']=='G1')]), 'G1·KOL')
kol = {'s1': kol_s1, 'g1': kol_g1}

kk_summary = {
    'koc_overall': add_label(summary_from(main_df[main_df['role']=='KOC']), 'KOC整体'),
    'kol_overall': add_label(summary_from(main_df[main_df['role']=='KOL']), 'KOL整体'),
    'koc_s1': add_label(summary_from(main_df[(main_df['role']=='KOC') & (main_df['product']=='S1')]), 'S1·KOC'),
    'koc_g1': add_label(summary_from(main_df[(main_df['role']=='KOC') & (main_df['product']=='G1')]), 'G1·KOC'),
    'kol_g1': add_label(summary_from(main_df[(main_df['role']=='KOL') & (main_df['product']=='G1')]), 'G1·KOL'),
}

# s1_dirs / g1_dirs
def build_dirs(product):
    sub = main_df[(main_df['product']==product) & (main_df['role']=='KOC')]
    agg = sub.groupby('direction').agg({'count':'sum','cost':'sum','gmv':'sum','store':'sum','interact':'sum','search':'sum','reads':'sum'}).reset_index()
    rows = []
    for _, r in agg.iterrows():
        count = int(r['count'])
        if count == 0: continue
        rows.append({
            '内容方向': r['direction'],
            '总消耗': round(float(r['cost']), 3),
            'gmv': round(float(r['gmv']), 3),
            '进店uv': int(r['store']),
            '互动量': int(r['interact']),
            '搜索uv': int(r['search']),
            '阅读量': int(r['reads']),
            'count': count,
            'roi': round(safe_div(r['gmv'], r['cost']), 2),
            'avg_interact': round(safe_div(r['interact'], count)),
            'avg_store': round(safe_div(r['store'], count), 1),
            'avg_search': round(safe_div(r['search'], count), 1),
            'avg_gmv': round(safe_div(r['gmv'], count)),
            'avg_cost': round(safe_div(r['cost'], count)),
        })
    # keep defined direction order
    order = [d for d in DIRECTION_ORDER if d.startswith(product)]
    rows = sorted(rows, key=lambda x: order.index(x['内容方向']) if x['内容方向'] in order else 99)
    return rows

s1_dirs = build_dirs('S1')
g1_dirs = build_dirs('G1')

# top lists
def build_top(product, by, n=10):
    sub = main_df[main_df['product']==product].copy()
    sub = sub.sort_values(by, ascending=False).head(n)
    out = []
    for _, r in sub.iterrows():
        out.append({
            'name': r['name'], 'direction': r['direction'], 'product': r['product'], 'source': r['role'],
            'url': r['url'], 'noteId': r['noteId'], 'title': r['title'],
            'roi': round(float(r['roi']), 2), 'gmv': round(float(r['gmv']), 2),
            'cost': round(float(r['cost']), 3), 'interact': float(r['interact']), 'store': float(r['store']),
        })
    return out

s1_top_roi = build_top('S1', 'roi')
s1_top_gmv = build_top('S1', 'gmv')
s1_top_interact = build_top('S1', 'interact')
s1_top_store = build_top('S1', 'store')
g1_top_roi = build_top('G1', 'roi')
g1_top_gmv = build_top('G1', 'gmv')
g1_top_interact = build_top('G1', 'interact')
g1_top_store = build_top('G1', 'store')

# heatmaps
agg_role_dir = main_df.groupby(['role','direction']).agg({'count':'sum','cost':'sum','gmv':'sum'}).reset_index()
heatmap_roi = []
heatmap_gmv = []
for _, r in agg_role_dir.iterrows():
    if r['direction'] not in DIRECTION_ORDER: continue
    ri = ROLES.index(r['role'])
    di = DIRECTION_ORDER.index(r['direction'])
    roi = round(safe_div(r['gmv'], r['cost']), 2)
    heatmap_roi.append([ri, di, roi, int(r['count'])])
    heatmap_gmv.append([ri, di, round(float(r['gmv']), 2), int(r['count'])])

# sankey for panel-s1g1: role -> product -> direction -> outcome
outcome_nodes = ['高ROI(≥10x)', '中ROI(3-10x)', '低ROI(<3x)']
sankey_nodes = [{'name':'KOC'},{'name':'KOL'},{'name':'S1'},{'name':'G1'}]
for d in DIRECTION_ORDER:
    sankey_nodes.append({'name':d})
for o in outcome_nodes:
    sankey_nodes.append({'name':o})
sankey_links = []
# role -> product
for (role, prod), g in main_df.groupby(['role','product']):
    cnt = int(g['count'].sum())
    if cnt: sankey_links.append({'source':role,'target':prod,'value':cnt})
# product -> direction
for (prod, dire), g in main_df.groupby(['product','direction']):
    cnt = int(g['count'].sum())
    if cnt: sankey_links.append({'source':prod,'target':dire,'value':cnt})
# direction -> outcome (use direction ROI)
for dire, g in main_df.groupby('direction'):
    cnt = int(g['count'].sum())
    if cnt == 0: continue
    roi = safe_div(g['gmv'].sum(), g['cost'].sum())
    if roi >= 10: out = '高ROI(≥10x)'
    elif roi >= 3: out = '中ROI(3-10x)'
    else: out = '低ROI(<3x)'
    sankey_links.append({'source':dire,'target':out,'value':cnt})

# title_analysis
titles = []
for _, r in main_df.iterrows():
    titles.append({
        'name': r['name'], 'direction': r['direction'], 'product': r['product'], 'source': r['role'],
        'url': r['url'], 'noteId': r['noteId'], 'gmv': round(float(r['gmv']), 2), 'roi': round(float(r['roi']), 2),
        'cost': round(float(r['cost']), 3), 'interact': float(r['interact']), 'store': float(r['store']),
        'title': r['title'], 'images': [], 'cover': None, 'note_type': 'image',
        'elements': {k: False for k in ['否定/警告词','数字','竖线分隔','问句','品牌名','品类词','对比/横评','真实感','强情绪','推荐句式','emoji','痛点词','价格词','功效词','场景词']},
    })
top_s1_gmv = sorted([t for t in titles if t['product']=='S1'], key=lambda x: x['gmv'], reverse=True)[:5]
top_g1_gmv = sorted([t for t in titles if t['product']=='G1'], key=lambda x: x['gmv'], reverse=True)[:5]
title_analysis = {'titles': titles, 'top_titles_s1_gmv': top_s1_gmv, 'top_titles_g1_gmv': top_g1_gmv}

new_data = {
    'overall': overall,
    'koc': koc,
    'kol': kol,
    's1_dirs': s1_dirs,
    'g1_dirs': g1_dirs,
    's1_top_roi': s1_top_roi,
    's1_top_gmv': s1_top_gmv,
    's1_top_interact': s1_top_interact,
    's1_top_store': s1_top_store,
    'g1_top_roi': g1_top_roi,
    'g1_top_gmv': g1_top_gmv,
    'g1_top_interact': g1_top_interact,
    'g1_top_store': g1_top_store,
    'heatmap_directions': DIRECTION_ORDER,
    'heatmap_roles': ROLES,
    'heatmap_roi': heatmap_roi,
    'heatmap_gmv': heatmap_gmv,
    'sankey_nodes': sankey_nodes,
    'sankey_links': sankey_links,
    'kk_summary': kk_summary,
    'title_analysis': title_analysis,
}

# ── 3. full 786 merge with test pools ──
ruhan_df = pd.read_excel('/Users/xiemila/Desktop/【1】如涵国补方向6.29数据汇总.xls', header=0).fillna(0)
jinka_df = pd.read_excel('/Users/xiemila/Downloads/金咖koc内容.xlsx', header=0).fillna(0)

def add_test_rows(df, source, default_dir):
    out = []
    for _, r in df.iterrows():
        prod_raw = str(r.get('产品','')).upper()
        prod = None
        if 'S1' in prod_raw: prod = 'S1'
        elif 'G1' in prod_raw: prod = 'G1'
        if prod is None: continue
        dire = str(r.get('内容方向', default_dir)).strip() or default_dir
        out.append({
            'product': prod, 'direction': dire, 'role': 'KOC',
            'count': 1, 'cost': float(r.get('总消耗',0)) if r.get('总消耗') else 0,
            'gmv': float(r.get('gmv',0)) if r.get('gmv') else 0,
            'store': int(r.get('进店uv',0)) if r.get('进店uv') else 0,
            'search': int(r.get('搜索uv',0)) if r.get('搜索uv') else 0,
            'interact': int(r.get('互动量',0)) if r.get('互动量') else 0,
            'reads': int(r.get('阅读量',0)) if r.get('阅读量') else 0,
        })
    return out

mega_rows = main_rows.copy()
for r in mega_rows:
    # ensure numeric
    for k in ['cost','gmv','store','search','interact','reads','count','roi']:
        if k not in r: r[k] = 0
    r['source'] = 'main'
mega_rows.extend(add_test_rows(ruhan_df, 'ruhan', '国补回搜'))
mega_rows.extend(add_test_rows(jinka_df, 'jinka', '参数横向对比'))
mega_df = pd.DataFrame(mega_rows)

# mega aggregates
mega_total = summary_from(mega_df)
mega_role = {role: summary_from(mega_df[mega_df['role']==role]) for role in ROLES}
mega_product = {prod: summary_from(mega_df[mega_df['product']==prod]) for prod in ['S1','G1']}
# ensure ints
for k in mega_total:
    if isinstance(mega_total[k], float) and k not in ['roi','with_gmv_pct','total_cost','total_gmv']:
        mega_total[k] = int(mega_total[k])

# ── 4. patch HTML ──
for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')

    # A) replace panel-s1g1 local DATA block
    pat = r'(function init_s1g1\(\)\{try\{const DATA = )(\{.*?\})(;\s*function switchTopTab)'
    def data_repl(m):
        # verify old keys count
        try:
            old = json.loads(m.group(2))
        except Exception as e:
            print('parse err', e); return m.group(0)
        # update keys
        old.update(new_data)
        return m.group(1) + json.dumps(old, ensure_ascii=False, separators=(',', ':')) + m.group(3)
    h2 = re.sub(pat, data_repl, h, count=1, flags=re.DOTALL)
    if h2 == h:
        print('WARN: panel-s1g1 DATA not replaced in', tgt)
    h = h2

    # B) update panel-s1g1 header data截止
    h = h.replace('数据截止6.22', '数据截止6.28')

    # C) rebuild panel-mega static HTML and replace whole block
    def fmt_num(n, d=0):
        return f'{int(round(n)):,}' if d == 0 else f'{n:,.{d}f}'
    def fmt_wan(n): return f'{n/10000:.1f}万'
    def safe_div(a,b): return a/b if b else 0

    budget = 950000
    total = mega_total
    role = mega_role
    prod = mega_product
    s1_koc = int(mega_df[(mega_df['product']=='S1') & (mega_df['role']=='KOC')]['count'].sum())
    g1_koc = int(mega_df[(mega_df['product']=='G1') & (mega_df['role']=='KOC')]['count'].sum())
    g1_kol = int(mega_df[(mega_df['product']=='G1') & (mega_df['role']=='KOL')]['count'].sum())

    # direction tables
    dir_agg = mega_df.groupby(['product','direction','role']).agg({'count':'sum','cost':'sum','gmv':'sum','store':'sum','search':'sum'}).reset_index()
    def table_html(prod_name):
        sub = dir_agg[(dir_agg['product']==prod_name) & (dir_agg['count']>0)].copy()
        sub['roi'] = sub.apply(lambda r: safe_div(r['gmv'], r['cost']), axis=1)
        sub = sub.sort_values('roi', ascending=False)
        rows_html = ''
        for _, r in sub.iterrows():
            roi = r['roi']
            color = '#34d399' if roi >= 10 else ('#fbbf24' if roi >= 3 else '#f87171')
            badge = '<span class="badge" style="background:#1a56db33;color:#5b9aff">KOC</span>' if r['role']=='KOC' else '<span class="badge" style="background:#ff6b6b33;color:#ff8a8a">KOL</span>'
            rows_html += f'<tr><td>{r["direction"]}</td><td>{badge}</td><td>{fmt_num(int(r["count"]))}</td><td>¥{fmt_num(int(r["cost"]))}</td><td>¥{fmt_num(int(r["gmv"]))}</td><td style="color:{color};font-weight:700">{roi:.2f}×</td><td>{fmt_num(int(r["store"]))}</td><td>{fmt_num(int(r["search"]))}</td></tr>'
        return rows_html

    new_mega_panel = f'''<div class="panel panel-mega" id="panel-mega" data-panel="mega">
<header><h1>全量 786 篇统一视图</h1><p>总预算 ¥95万 · 786 条内容 · KOL {fmt_num(role['KOL']['count'])} 条 · KOC {fmt_num(role['KOC']['count'])} 条 · S1 {fmt_num(prod['S1']['count'])} 条 · G1 {fmt_num(prod['G1']['count'])} 条</p></header>
<div class="container">
  <div class="section overview-section">
    <h2 class="section-title" style="border-left-color:#fbbf24">全量 786 篇 · 总览</h2>
    <p class="section-sub">总预算 ¥950,000 · 786 条内容 · KOL {fmt_num(role['KOL']['count'])} 条 · KOC {fmt_num(role['KOC']['count'])} 条 · S1 {fmt_num(prod['S1']['count'])} 条 · G1 {fmt_num(prod['G1']['count'])} 条</p>
    <div class="mega-metrics">
      <div class="mega-card"><div class="mega-label">累计GMV</div><div class="mega-value" style="color:#34d399">{fmt_wan(total['total_gmv'])}<span class="mega-unit">元</span></div></div>
      <div class="mega-card"><div class="mega-label">预算 ROI</div><div class="mega-value" style="color:#fbbf24">{total['roi']:.2f}<span class="mega-unit">×</span></div></div>
      <div class="mega-card"><div class="mega-label">实际消耗</div><div class="mega-value" style="color:#f472b6">{fmt_wan(total['total_cost'])}<span class="mega-unit">元</span></div></div>
      <div class="mega-card"><div class="mega-label">预算执行率</div><div class="mega-value" style="color:#60a5fa">{100*total['total_cost']/budget:.1f}<span class="mega-unit">%</span></div></div>
      <div class="mega-card"><div class="mega-label">累计引流UV</div><div class="mega-value" style="color:#22d3ee">{fmt_num(total['total_store'])}<span class="mega-unit"></span></div></div>
      <div class="mega-card"><div class="mega-label">累计搜索UV</div><div class="mega-value" style="color:#a78bfa">{fmt_num(total['total_search'])}<span class="mega-unit"></span></div></div>
      <div class="mega-card"><div class="mega-label">总互动量</div><div class="mega-value" style="color:#fb923c">{fmt_num(total['total_interact'])}<span class="mega-unit"></span></div></div>
      <div class="mega-card"><div class="mega-label">总阅读量</div><div class="mega-value" style="color:#e879f9">{fmt_num(total['total_reads'])}<span class="mega-unit"></span></div></div>
    </div>
  </div>
  <div class="section">
    <h2 class="section-title">KOC vs KOL 身份维度（全量 786 篇）</h2>
    <div class="product-row">
      <div class="product-card" style="background: linear-gradient(135deg, #0a1f4d 0%, #1a56db22 100%); border: 1px solid #1a56db;">
        <h3 style="color:#5b9aff">KOC <span class="badge">{fmt_num(role['KOC']['count'])}篇 · ROI {role['KOC']['roi']:.2f}×</span></h3>
        <p class="sub">实际消耗 ¥{fmt_num(role['KOC']['total_cost'])} · GMV ¥{fmt_num(role['KOC']['total_gmv'])} · 引流 {fmt_num(role['KOC']['total_store'])} · 搜索 {fmt_num(role['KOC']['total_search'])}</p>
        <div class="stats">
          <div class="stat-item"><div class="v">{fmt_wan(role['KOC']['total_cost'])}</div><div class="l">实际消耗</div></div>
          <div class="stat-item"><div class="v">{fmt_wan(role['KOC']['total_gmv'])}</div><div class="l">总GMV</div></div>
          <div class="stat-item"><div class="v">{role['KOC']['roi']:.2f}×</div><div class="l">实际ROI</div></div>
          <div class="stat-item"><div class="v">¥{role['KOC']['avg_cost']:.1f}</div><div class="l">CPE</div></div>
          <div class="stat-item"><div class="v">{fmt_num(role['KOC']['avg_gmv'])}</div><div class="l">篇均GMV</div></div>
          <div class="stat-item"><div class="v">{fmt_num(role['KOC']['total_store'])}</div><div class="l">引流UV</div></div>
        </div>
      </div>
      <div class="product-card" style="background: linear-gradient(135deg, #4d0f1a 0%, #ff6b6b22 100%); border: 1px solid #ff6b6b;">
        <h3 style="color:#ff8a8a">KOL <span class="badge">{fmt_num(role['KOL']['count'])}篇 · ROI {role['KOL']['roi']:.2f}×</span></h3>
        <p class="sub">实际消耗 ¥{fmt_num(role['KOL']['total_cost'])} · GMV ¥{fmt_num(role['KOL']['total_gmv'])} · 引流 {fmt_num(role['KOL']['total_store'])} · 搜索 {fmt_num(role['KOL']['total_search'])}</p>
        <div class="stats">
          <div class="stat-item"><div class="v">{fmt_wan(role['KOL']['total_cost'])}</div><div class="l">实际消耗</div></div>
          <div class="stat-item"><div class="v">{fmt_wan(role['KOL']['total_gmv'])}</div><div class="l">总GMV</div></div>
          <div class="stat-item"><div class="v">{role['KOL']['roi']:.2f}×</div><div class="l">实际ROI</div></div>
          <div class="stat-item"><div class="v">¥{role['KOL']['avg_cost']:.1f}</div><div class="l">CPE</div></div>
          <div class="stat-item"><div class="v">{fmt_num(role['KOL']['avg_gmv'])}</div><div class="l">篇均GMV</div></div>
          <div class="stat-item"><div class="v">{fmt_num(role['KOL']['total_store'])}</div><div class="l">引流UV</div></div>
        </div>
      </div>
    </div>
  </div>
  <div class="section">
    <h2 class="section-title">S1 vs G1 产品维度</h2>
    <div class="product-row">
      <div class="product-card s1">
        <h3>千问 S1 <span class="badge">{fmt_num(prod['S1']['count'])}篇 · ROI {prod['S1']['roi']:.2f}×</span></h3>
        <p class="sub">实际消耗 ¥{fmt_num(prod['S1']['total_cost'])} · GMV ¥{fmt_num(prod['S1']['total_gmv'])} · 引流 {fmt_num(prod['S1']['total_store'])} · 搜索 {fmt_num(prod['S1']['total_search'])}</p>
        <div class="stats">
          <div class="stat-item"><div class="v">{fmt_wan(prod['S1']['total_cost'])}</div><div class="l">实际消耗</div></div>
          <div class="stat-item"><div class="v">{fmt_wan(prod['S1']['total_gmv'])}</div><div class="l">总GMV</div></div>
          <div class="stat-item"><div class="v">{prod['S1']['roi']:.2f}×</div><div class="l">实际ROI</div></div>
          <div class="stat-item"><div class="v">¥{fmt_num(prod['S1']['avg_gmv'])}</div><div class="l">篇均GMV</div></div>
          <div class="stat-item"><div class="v">{fmt_num(prod['S1']['total_store'])}</div><div class="l">引流UV</div></div>
          <div class="stat-item"><div class="v">{fmt_num(prod['S1']['total_search'])}</div><div class="l">搜索UV</div></div>
        </div>
      </div>
      <div class="product-card g1">
        <h3>千问 G1 <span class="badge">{fmt_num(prod['G1']['count'])}篇 · ROI {prod['G1']['roi']:.2f}×</span></h3>
        <p class="sub">实际消耗 ¥{fmt_num(prod['G1']['total_cost'])} · GMV ¥{fmt_num(prod['G1']['total_gmv'])} · 引流 {fmt_num(prod['G1']['total_store'])} · 搜索 {fmt_num(prod['G1']['total_search'])}</p>
        <div class="stats">
          <div class="stat-item"><div class="v">{fmt_wan(prod['G1']['total_cost'])}</div><div class="l">实际消耗</div></div>
          <div class="stat-item"><div class="v">{fmt_wan(prod['G1']['total_gmv'])}</div><div class="l">总GMV</div></div>
          <div class="stat-item"><div class="v">{prod['G1']['roi']:.2f}×</div><div class="l">实际ROI</div></div>
          <div class="stat-item"><div class="v">¥{fmt_num(prod['G1']['avg_gmv'])}</div><div class="l">篇均GMV</div></div>
          <div class="stat-item"><div class="v">{fmt_num(prod['G1']['total_store'])}</div><div class="l">引流UV</div></div>
          <div class="stat-item"><div class="v">{fmt_num(prod['G1']['total_search'])}</div><div class="l">搜索UV</div></div>
        </div>
      </div>
    </div>
  </div>
  <div class="section">
    <h2 class="section-title">内容方向效率总表（按产品线拆分）</h2>
    <p class="section-sub">全量 786 篇统一聚合，S1/G1 分别按 ROI 降序；表格可横向滑动</p>
    <div class="product-row mega-dir-row">
      <div class="chart-container">
        <h3>S1 内容方向效率（{fmt_num(prod['S1']['count'])}篇）</h3>
        <div class="table-wrap">
          <table class="top-table mega-table">
            <thead><tr><th>方向</th><th>身份</th><th>篇数</th><th>消耗</th><th>GMV</th><th>ROI</th><th>进店</th><th>搜索</th></tr></thead>
            <tbody>{table_html('S1')}</tbody>
          </table>
        </div>
      </div>
      <div class="chart-container">
        <h3>G1 内容方向效率（{fmt_num(prod['G1']['count'])}篇）</h3>
        <div class="table-wrap">
          <table class="top-table mega-table">
            <thead><tr><th>方向</th><th>身份</th><th>篇数</th><th>消耗</th><th>GMV</th><th>ROI</th><th>进店</th><th>搜索</th></tr></thead>
            <tbody>{table_html('G1')}</tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
  <div class="section">
    <h2 class="section-title">全量 786 篇 KISS 结论</h2>
    <div class="kiss-grid">
      <div class="kiss-card kiss-keep">
        <div class="kiss-title">KEEP</div>
        <div class="kiss-v">KOC 仍是效率基本盘：统一后 {fmt_num(role['KOC']['count'])} 篇，实际 ROI {role['KOC']['roi']:.2f}×，远高于 KOL {role['KOL']['roi']:.2f}×</div>
        <div class="kiss-v">S1 高客单模型成立：{fmt_num(prod['S1']['count'])} 篇 ROI {prod['S1']['roi']:.2f}×，显著高于 G1 {prod['G1']['roi']:.2f}×</div>
        <div class="kiss-v">纵测、读书日借势、G1 横测继续规模化复制</div>
      </div>
      <div class="kiss-card kiss-improve">
        <div class="kiss-title">IMPROVE</div>
        <div class="kiss-v">KOL {fmt_num(role['KOL']['count'])} 篇全部压在 G1 横测，应扩展到 S1 高 ROI 方向</div>
        <div class="kiss-v">节点类内容沉淀周期短，需提前 2-4 周前置铺设</div>
        <div class="kiss-v">测试池内容结构和账号选号还有优化空间</div>
      </div>
      <div class="kiss-card kiss-stop">
        <div class="kiss-title">STOP</div>
        <div class="kiss-v">S1 明星热点方向继续停投</div>
        <div class="kiss-v">低 ROI 场景体验/选购攻略类控预算，避免无限铺量</div>
      </div>
      <div class="kiss-card kiss-start">
        <div class="kiss-title">START</div>
        <div class="kiss-v">把高 ROI 方向（纵测/读书日/用户证言）从 S1 复制到 G1</div>
        <div class="kiss-v">用 20% 预算做新方向测试，验证后导入 80% KOC 铺量</div>
        <div class="kiss-v">建立「786 篇全量统一周报」口径，每周按预算 95w 更新</div>
      </div>
    </div>
  </div>
</div>
</div>'''
    # replace old panel-mega block
    pattern = r'<div class="panel panel-mega" id="panel-mega" data-panel="mega">.*?</div>\s*</div>\s*</div>\s*(?=<div class="panel panel-s1g1")'
    h = re.sub(pattern, new_mega_panel, h, count=1, flags=re.DOTALL)

    tgt.write_text(h, encoding='utf-8')
    print(f'✓ patched {tgt.relative_to(ROOT)}')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')

# save summary
with open('outputs/mega_786_summary_v44.json', 'w', encoding='utf-8') as f:
    json.dump({'total': mega_total, 'role': mega_role, 'product': mega_product}, f, ensure_ascii=False, indent=2)
