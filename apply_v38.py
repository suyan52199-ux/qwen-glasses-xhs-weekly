#!/usr/bin/env python3
"""
R38: 把铺量(634) + 如涵(80) + 金咖(72) 共 786 篇合并为统一视图，
采用 KOC/KOL 模板口径，生成「全量 786 篇」panel 注入主 HTML。
口径：铺量 6.22 + 如涵 6.29 + 金咖 6.29。
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


# ── 1. 主池数据 ──
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

main = {
    'koc': {
        'count': 600,
        'cost': main_data['koc']['s1']['total_cost'] + main_data['koc']['g1']['total_cost'],
        'gmv': main_data['koc']['s1']['total_gmv'] + main_data['koc']['g1']['total_gmv'],
        'store': main_data['koc']['s1']['total_store'] + main_data['koc']['g1']['total_store'],
        'search': main_data['koc']['s1']['total_search'] + main_data['koc']['g1']['total_search'],
        'interact': main_data['koc']['s1']['total_interact'] + main_data['koc']['g1']['total_interact'],
        'reads': main_data['koc']['s1']['total_reads'] + main_data['koc']['g1']['total_reads'],
    },
    'kol': {
        'count': 34,
        'cost': main_data['kol']['g1']['total_cost'],
        'gmv': main_data['kol']['g1']['total_gmv'],
        'store': main_data['kol']['g1']['total_store'],
        'search': main_data['kol']['g1']['total_search'],
        'interact': main_data['kol']['g1']['total_interact'],
        'reads': main_data['kol']['g1']['total_reads'],
    },
    's1': {
        'count': main_data['overall']['s1']['count'],
        'cost': main_data['overall']['s1']['total_cost'],
        'gmv': main_data['overall']['s1']['total_gmv'],
        'store': main_data['overall']['s1']['total_store'],
        'search': main_data['overall']['s1']['total_search'],
        'interact': main_data['overall']['s1']['total_interact'],
        'reads': main_data['overall']['s1']['total_reads'],
    },
    'g1': {
        'count': main_data['overall']['g1']['count'],
        'cost': main_data['overall']['g1']['total_cost'],
        'gmv': main_data['overall']['g1']['total_gmv'],
        'store': main_data['overall']['g1']['total_store'],
        'search': main_data['overall']['g1']['total_search'],
        'interact': main_data['overall']['g1']['total_interact'],
        'reads': main_data['overall']['g1']['total_reads'],
    },
}
for k in main:
    main[k]['roi'] = safe_div(main[k]['gmv'], main[k]['cost'])
    main[k]['avg_cost'] = safe_div(main[k]['cost'], main[k]['count'])
    main[k]['avg_gmv'] = safe_div(main[k]['gmv'], main[k]['count'])
    main[k]['cpe'] = safe_div(main[k]['cost'], main[k]['interact'])
    main[k]['cpm'] = safe_div(main[k]['cost'], main[k]['reads']) * 1000

# ── 2. 如涵数据 ──
rdf = pd.read_excel('/Users/xiemila/Desktop/如涵国补方向6.29数据汇总.xls', header=0)
rdf = rdf.fillna(0)
ruhan_overall = {
    'count': len(rdf),
    'cost': 100000.0,  # 用户修正预算口径
    'gmv': float(rdf['gmv'].sum()),
    'store': int(rdf['进店uv'].sum()),
    'search': int(rdf['搜索uv'].sum()),
    'interact': int(rdf['互动量'].sum()),
    'reads': int(rdf['阅读量'].sum()),
}
ruhan_overall['roi'] = safe_div(ruhan_overall['gmv'], ruhan_overall['cost'])
ruhan_overall['cpe'] = safe_div(ruhan_overall['cost'], ruhan_overall['interact'])
ruhan_overall['cpm'] = safe_div(ruhan_overall['cost'], ruhan_overall['reads']) * 1000
ruhan_overall['avg_cost'] = safe_div(ruhan_overall['cost'], ruhan_overall['count'])
ruhan_overall['avg_gmv'] = safe_div(ruhan_overall['gmv'], ruhan_overall['count'])

ruhan_sg = {}
for prod, g in rdf.groupby('内容方向'):
    prod = prod.upper()
    ruhan_sg[prod] = {
        'count': len(g),
        'cost': ruhan_overall['cost'] * safe_div(int(g['进店uv'].sum()), ruhan_overall['store']) if ruhan_overall['store'] else 0,
        'gmv': float(g['gmv'].sum()),
        'store': int(g['进店uv'].sum()),
        'search': int(g['搜索uv'].sum()),
        'interact': int(g['互动量'].sum()),
        'reads': int(g['阅读量'].sum()),
    }
    ruhan_sg[prod]['roi'] = safe_div(ruhan_sg[prod]['gmv'], ruhan_sg[prod]['cost'])
    ruhan_sg[prod]['avg_gmv'] = safe_div(ruhan_sg[prod]['gmv'], ruhan_sg[prod]['count'])
    ruhan_sg[prod]['cpe'] = safe_div(ruhan_sg[prod]['cost'], ruhan_sg[prod]['interact'])

# ── 3. 金咖数据 ──
with open('outputs/promo_product_split_summary.json') as f:
    jinka_split = json.load(f)
jinka_overall = {
    'count': 72,
    'cost': 50000.0,  # 用户给定预算口径
    'gmv': 320082.29,
    'store': 9383,
    'search': 1694,
    'interact': 3646,
    'reads': 77631,
}
jinka_overall['roi'] = safe_div(jinka_overall['gmv'], jinka_overall['cost'])
jinka_overall['cpe'] = safe_div(jinka_overall['cost'], jinka_overall['interact'])
jinka_overall['cpm'] = safe_div(jinka_overall['cost'], jinka_overall['reads']) * 1000
jinka_overall['avg_gmv'] = safe_div(jinka_overall['gmv'], jinka_overall['count'])

# 用 product split summary 的阅读量占比拆分总预算/GMV/进店/搜索/互动/阅读
jinka_reads_total = sum(v['reads'] for v in jinka_split['S1'].values()) + sum(v['reads'] for v in jinka_split['G1'].values())
jinka_store_total = sum(v['store'] for v in jinka_split['S1'].values()) + sum(v['store'] for v in jinka_split['G1'].values())
jinka_sg = {}
for prod in ['S1', 'G1']:
    reads_share = safe_div(sum(v['reads'] for v in jinka_split[prod].values()), jinka_reads_total)
    store_share = safe_div(sum(v['store'] for v in jinka_split[prod].values()), jinka_store_total)
    jinka_sg[prod] = {
        'count': sum(v['count'] for v in jinka_split[prod].values()),
        'cost': jinka_overall['cost'] * reads_share,
        'gmv': jinka_overall['gmv'] * store_share,
        'store': int(jinka_overall['store'] * store_share),
        'search': int(jinka_overall['search'] * store_share),
        'interact': int(jinka_overall['interact'] * reads_share),
        'reads': int(jinka_overall['reads'] * reads_share),
    }
    jinka_sg[prod]['roi'] = safe_div(jinka_sg[prod]['gmv'], jinka_sg[prod]['cost'])
    jinka_sg[prod]['avg_gmv'] = safe_div(jinka_sg[prod]['gmv'], jinka_sg[prod]['count'])
    jinka_sg[prod]['cpe'] = safe_div(jinka_sg[prod]['cost'], jinka_sg[prod]['interact'])

# ── 4. 合并计算 ──
total = {
    'count': main['koc']['count'] + main['kol']['count'] + ruhan_overall['count'] + jinka_overall['count'],
    'cost': main['koc']['cost'] + main['kol']['cost'] + ruhan_overall['cost'] + jinka_overall['cost'],
    'gmv': main['koc']['gmv'] + main['kol']['gmv'] + ruhan_overall['gmv'] + jinka_overall['gmv'],
    'store': main['koc']['store'] + main['kol']['store'] + ruhan_overall['store'] + jinka_overall['store'],
    'search': main['koc']['search'] + main['kol']['search'] + ruhan_overall['search'] + jinka_overall['search'],
    'interact': main['koc']['interact'] + main['kol']['interact'] + ruhan_overall['interact'] + jinka_overall['interact'],
    'reads': main['koc']['reads'] + main['kol']['reads'] + ruhan_overall['reads'] + jinka_overall['reads'],
}
total['roi'] = safe_div(total['gmv'], total['cost'])
total['cpe'] = safe_div(total['cost'], total['interact'])
total['cpm'] = safe_div(total['cost'], total['reads']) * 1000
total['avg_gmv'] = safe_div(total['gmv'], total['count'])

koc_combined = {
    'count': main['koc']['count'] + ruhan_overall['count'] + jinka_overall['count'],
    'cost': main['koc']['cost'] + ruhan_overall['cost'] + jinka_overall['cost'],
    'gmv': main['koc']['gmv'] + ruhan_overall['gmv'] + jinka_overall['gmv'],
    'store': main['koc']['store'] + ruhan_overall['store'] + jinka_overall['store'],
    'search': main['koc']['search'] + ruhan_overall['search'] + jinka_overall['search'],
    'interact': main['koc']['interact'] + ruhan_overall['interact'] + jinka_overall['interact'],
    'reads': main['koc']['reads'] + ruhan_overall['reads'] + jinka_overall['reads'],
}
koc_combined['roi'] = safe_div(koc_combined['gmv'], koc_combined['cost'])
koc_combined['cpe'] = safe_div(koc_combined['cost'], koc_combined['interact'])
koc_combined['avg_gmv'] = safe_div(koc_combined['gmv'], koc_combined['count'])
koc_combined['with_gmv_pct'] = None  # 暂无

kol_combined = main['kol'].copy()

s1_combined = {
    'count': main['s1']['count'] + ruhan_sg.get('S1', {}).get('count', 0) + jinka_sg['S1']['count'],
    'cost': main['s1']['cost'] + ruhan_sg.get('S1', {}).get('cost', 0) + jinka_sg['S1']['cost'],
    'gmv': main['s1']['gmv'] + ruhan_sg.get('S1', {}).get('gmv', 0) + jinka_sg['S1']['gmv'],
    'store': main['s1']['store'] + ruhan_sg.get('S1', {}).get('store', 0) + jinka_sg['S1']['store'],
    'search': main['s1']['search'] + ruhan_sg.get('S1', {}).get('search', 0) + jinka_sg['S1']['search'],
    'interact': main['s1']['interact'] + ruhan_sg.get('S1', {}).get('interact', 0) + jinka_sg['S1']['interact'],
    'reads': main['s1']['reads'] + ruhan_sg.get('S1', {}).get('reads', 0) + jinka_sg['S1']['reads'],
}
s1_combined['roi'] = safe_div(s1_combined['gmv'], s1_combined['cost'])
s1_combined['avg_gmv'] = safe_div(s1_combined['gmv'], s1_combined['count'])

g1_combined = {
    'count': main['g1']['count'] + ruhan_sg.get('G1', {}).get('count', 0) + jinka_sg['G1']['count'],
    'cost': main['g1']['cost'] + ruhan_sg.get('G1', {}).get('cost', 0) + jinka_sg['G1']['cost'],
    'gmv': main['g1']['gmv'] + ruhan_sg.get('G1', {}).get('gmv', 0) + jinka_sg['G1']['gmv'],
    'store': main['g1']['store'] + ruhan_sg.get('G1', {}).get('store', 0) + jinka_sg['G1']['store'],
    'search': main['g1']['search'] + ruhan_sg.get('G1', {}).get('search', 0) + jinka_sg['G1']['search'],
    'interact': main['g1']['interact'] + ruhan_sg.get('G1', {}).get('interact', 0) + jinka_sg['G1']['interact'],
    'reads': main['g1']['reads'] + ruhan_sg.get('G1', {}).get('reads', 0) + jinka_sg['G1']['reads'],
}
g1_combined['roi'] = safe_div(g1_combined['gmv'], g1_combined['cost'])
g1_combined['avg_gmv'] = safe_div(g1_combined['gmv'], g1_combined['count'])

# ── 5. 方向表格 ──
direction_rows = []
# 主池方向
for row in main_data['s1_dirs'] + main_data['g1_dirs']:
    direction_rows.append({
        '方向': row['内容方向'],
        '产品': 'S1' if row['内容方向'].startswith('S1') else 'G1',
        '来源': '铺量',
        '篇数': row['count'],
        '消耗': row['总消耗'],
        'GMV': row['gmv'],
        'ROI': row['roi'],
        '进店UV': row['进店uv'],
        '搜索UV': row['搜索uv'],
        '互动量': row['互动量'],
    })
# 如涵 / 金咖 按产品汇总
for prod in ['S1', 'G1']:
    r = ruhan_sg.get(prod, {})
    if r.get('count'):
        direction_rows.append({
            '方向': '如涵国补方向',
            '产品': prod,
            '来源': '如涵测试',
            '篇数': r['count'],
            '消耗': r['cost'],
            'GMV': r['gmv'],
            'ROI': r['roi'],
            '进店UV': r['store'],
            '搜索UV': r['search'],
            '互动量': r['interact'],
        })
    j = jinka_sg[prod]
    direction_rows.append({
        '方向': '金咖618促单',
        '产品': prod,
        '来源': '金咖测试',
        '篇数': j['count'],
        '消耗': j['cost'],
        'GMV': j['gmv'],
        'ROI': j['roi'],
        '进店UV': j['store'],
        '搜索UV': j['search'],
        '互动量': j['interact'],
    })
# 排序 ROI 高到低
direction_rows.sort(key=lambda x: x['ROI'], reverse=True)

# ── 6. 生成 HTML ──
metric_card = lambda label, value, unit='', color='#fff': f'''<div class="mega-card"><div class="mega-label">{label}</div><div class="mega-value" style="color:{color}">{value}<span class="mega-unit">{unit}</span></div></div>'''

card_html = f'''
<div class="mega-metrics">
  {metric_card('总笔记数', fmt_num(total['count']), '篇', '#22d3ee')}
  {metric_card('总消耗', fmt_wan(total['cost']), '元', '#f472b6')}
  {metric_card('总GMV', fmt_wan(total['gmv']), '元', '#34d399')}
  {metric_card('整体ROI', fmt_num(total['roi'], 2), '×', '#fbbf24')}
  {metric_card('引流UV', fmt_num(total['store']), '', '#60a5fa')}
  {metric_card('搜索UV', fmt_num(total['search']), '', '#a78bfa')}
  {metric_card('CPE', f"¥{fmt_num(total['cpe'], 1)}", '', '#fb923c')}
  {metric_card('篇均GMV', f"¥{fmt_num(total['avg_gmv'], 0)}", '', '#e879f9')}
</div>
'''

role_html = f'''
<div class="product-row">
  <div class="product-card" style="background: linear-gradient(135deg, #0a1f4d 0%, #1a56db22 100%); border: 1px solid #1a56db;">
    <h3 style="color:#5b9aff">KOC 中腰部铺量 <span class="badge">{fmt_num(koc_combined['count'])}篇 · ROI {koc_combined['roi']:.2f}×</span></h3>
    <p class="sub">铺量 600 篇 + 如涵 80 篇 + 金咖 72 篇 · 统一按 KOC 模板计算</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(koc_combined['cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(koc_combined['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{koc_combined['roi']:.2f}×</div><div class="l">整体ROI</div></div>
      <div class="stat-item"><div class="v">{fmt_num(koc_combined['store'])}</div><div class="l">进店UV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(koc_combined['search'])}</div><div class="l">搜索UV</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(koc_combined['cpe'], 1)}</div><div class="l">CPE</div></div>
    </div>
  </div>
  <div class="product-card" style="background: linear-gradient(135deg, #4d0f1a 0%, #ff6b6b22 100%); border: 1px solid #ff6b6b;">
    <h3 style="color:#ff8a8a">KOL 头部声量 <span class="badge">{fmt_num(kol_combined['count'])}篇 · ROI {kol_combined['roi']:.2f}×</span></h3>
    <p class="sub">铺量 34 篇 · 全在 G1 横测 · 单篇成本 ¥{fmt_num(kol_combined['avg_cost'], 0)}</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(kol_combined['cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(kol_combined['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{kol_combined['roi']:.2f}×</div><div class="l">整体ROI</div></div>
      <div class="stat-item"><div class="v">{fmt_num(kol_combined['store'])}</div><div class="l">进店UV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(kol_combined['search'])}</div><div class="l">搜索UV</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(kol_combined['cpe'], 1)}</div><div class="l">CPE</div></div>
    </div>
  </div>
</div>
'''

product_html = f'''
<div class="product-row">
  <div class="product-card s1">
    <h3>千问 S1 <span class="badge">带屏旗舰款 · {fmt_num(s1_combined['count'])}篇</span></h3>
    <p class="sub">铺量 236 篇 + 如涵 {ruhan_sg.get('S1', {}).get('count', 0)} 篇 + 金咖 {jinka_sg['S1']['count']} 篇</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(s1_combined['cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(s1_combined['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{s1_combined['roi']:.2f}×</div><div class="l">整体ROI</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(s1_combined['avg_gmv'], 0)}</div><div class="l">篇均GMV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(s1_combined['store'])}</div><div class="l">进店UV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(s1_combined['search'])}</div><div class="l">搜索UV</div></div>
    </div>
  </div>
  <div class="product-card g1">
    <h3>千问 G1 <span class="badge">轻量音频款 · {fmt_num(g1_combined['count'])}篇</span></h3>
    <p class="sub">铺量 398 篇 + 如涵 {ruhan_sg.get('G1', {}).get('count', 0)} 篇 + 金咖 {jinka_sg['G1']['count']} 篇</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(g1_combined['cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(g1_combined['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{g1_combined['roi']:.2f}×</div><div class="l">整体ROI</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(g1_combined['avg_gmv'], 0)}</div><div class="l">篇均GMV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(g1_combined['store'])}</div><div class="l">进店UV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(g1_combined['search'])}</div><div class="l">搜索UV</div></div>
    </div>
  </div>
</div>
'''

table_rows_html = ''
for r in direction_rows:
    roi_color = '#34d399' if r['ROI'] >= 10 else ('#fbbf24' if r['ROI'] >= 3 else '#f87171')
    table_rows_html += f'''<tr><td>{r['方向']}</td><td>{r['产品']}</td><td>{r['来源']}</td><td>{r['篇数']}</td><td>¥{fmt_num(r['消耗'], 0)}</td><td>¥{fmt_num(r['GMV'], 0)}</td><td style="color:{roi_color};font-weight:700">{r['ROI']:.2f}×</td><td>{fmt_num(r['进店UV'])}</td><td>{fmt_num(r['搜索UV'])}</td><td>{fmt_num(r['互动量'])}</td></tr>'''

direction_html = f'''
<div class="section">
  <h2 class="section-title">内容方向效率总表（786 篇统一排序）</h2>
  <p class="section-sub">按 ROI 降序，涵盖铺量、如涵、金咖全部方向；测试池按 S1/G1 拆分后并入</p>
  <div class="chart-container" style="overflow-x:auto;">
    <table class="top-table mega-table">
      <thead><tr><th>内容方向</th><th>产品</th><th>来源</th><th>篇数</th><th>消耗</th><th>GMV</th><th>ROI</th><th>进店UV</th><th>搜索UV</th><th>互动量</th></tr></thead>
      <tbody>{table_rows_html}</tbody>
    </table>
  </div>
</div>
'''

kiss_html = '''
<div class="section">
  <h2 class="section-title">全量 786 篇 KISS 结论</h2>
  <div class="kiss-grid">
    <div class="kiss-card kiss-keep">
      <div class="kiss-title">KEEP</div>
      <div class="kiss-v">KOC 仍是效率基本盘，统一口径后 ROI 7.19× 远高于 KOL 2.75×</div>
      <div class="kiss-v">S1 带屏旗舰全量 ROI 8.29×，显著高于 G1 的 5.71×，高客单价+精准种草模型成立</div>
      <div class="kiss-v">S1 纵测 / 读书日借势 / G1 横测 三大方向在全量中仍居 TOP</div>
    </div>
    <div class="kiss-card kiss-improve">
      <div class="kiss-title">IMPROVE</div>
      <div class="kiss-v">测试池（如涵 ROI 3.24×、金咖 6.40×）拉低整体，需优化内容结构与账号选号</div>
      <div class="kiss-v">KOL 34 篇全部押在 G1 横测，应拓展到 S1 已验证的高 ROI 方向</div>
      <div class="kiss-v">S1 热点 618/520/明星方向沉淀短，节点内容需提前 2-4 周前置铺设</div>
    </div>
    <div class="kiss-card kiss-stop">
      <div class="kiss-title">STOP</div>
      <div class="kiss-v">S1 热点明星方向（铺量 39 篇 ROI≈0）继续停投</div>
      <div class="kiss-v">低转化场景体验/选购攻略类控预算，避免无限量铺量</div>
    </div>
    <div class="kiss-card kiss-start">
      <div class="kiss-title">START</div>
      <div class="kiss-v">把金咖「用户评论证言」与 G1 横测打法复制到如涵 S1 方向</div>
      <div class="kiss-v">用测试池（如涵/金咖）做 20% 内容方向实验，验证后导入 80% KOC 铺量</div>
      <div class="kiss-v">建立「铺量+测试」统一周报口径，每周按 786 篇更新</div>
    </div>
  </div>
</div>
'''

panel_html = f'''<div class="panel panel-mega" id="panel-mega" data-panel="mega">
<header><h1>全量 786 篇统一视图</h1><p>铺量 634 篇(KOC 600 + KOL 34) + 新内容测试 152 篇(如涵 80 + 金咖 72) · 统一按 KOC/KOL 模板计算 · 数据口径：铺量 6.22 + 如涵 6.29 + 金咖 6.29</p></header>
<div class="container">
  <div class="section overview-section">
    <h2 class="section-title">第一层：核心指标总览</h2>
    {card_html}
  </div>
  <div class="section">
    <h2 class="section-title">第二层：KOC vs KOL 身份维度</h2>
    {role_html}
  </div>
  <div class="section">
    <h2 class="section-title">第三层：S1 vs G1 产品维度</h2>
    {product_html}
  </div>
  {direction_html}
  {kiss_html}
</div>
</div>'''

# ── 7. 注入 ──
for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')
    # add tab button right after nav tabs open
    btn = '<button class="tab-btn" data-tab="mega"><span class="ic">🌍</span><span class="nm">全量786篇</span></button>'
    if 'data-tab="mega"' not in h:
        h = h.replace('<div class="tabs">', '<div class="tabs">' + btn, 1)
    if 'id="panel-mega"' not in h:
        # insert before first panel
        h = h.replace('<div class="panel panel-s1g1"', panel_html + '\n<div class="panel panel-s1g1"', 1)
    tgt.write_text(h, encoding='utf-8')
    print(f'✓ injected {tgt.relative_to(ROOT)}')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')

# save summary json for reference
summary = {
    'total': {k: v for k, v in total.items()},
    'koc': {k: v for k, v in koc_combined.items()},
    'kol': {k: v for k, v in kol_combined.items()},
    's1': {k: v for k, v in s1_combined.items()},
    'g1': {k: v for k, v in g1_combined.items()},
    'direction_top5': direction_rows[:5],
}
with open('outputs/mega_786_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print('✓ saved outputs/mega_786_summary.json')
