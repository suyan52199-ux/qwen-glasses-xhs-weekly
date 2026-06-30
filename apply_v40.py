#!/usr/bin/env python3
"""
R40:
1. 删除原有的「铺量内容 · 目标完成情况」+「测试内容 · 目标完成情况」模块。
2. 用最前面新的总览替换：预算 95w / 786 条 / KOL34 / KOC752 / S1&G1 拆分 / 引流/搜索/GMV/ROI。
3. 用新的如涵/金咖文件重新计算并重建「全量 786 篇」panel。
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

TOTAL_BUDGET = 950000.0


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


# ── 1. load main pool data ──
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

# main pool KOC directions
for row in main_data['s1_dirs']:
    rows.append({
        'product': 'S1',
        'direction': map_main_dir(row['内容方向']),
        'role': 'KOC',
        'count': row['count'],
        'cost': row['总消耗'],
        'gmv': row['gmv'],
        'store': row['进店uv'],
        'search': row['搜索uv'],
        'interact': row['互动量'],
        'reads': row['阅读量'],
    })
for row in main_data['g1_dirs']:
    rows.append({
        'product': 'G1',
        'direction': map_main_dir(row['内容方向']),
        'role': 'KOC',
        'count': row['count'],
        'cost': row['总消耗'],
        'gmv': row['gmv'],
        'store': row['进店uv'],
        'search': row['搜索uv'],
        'interact': row['互动量'],
        'reads': row['阅读量'],
    })

# split KOL from G1 横测
KOL_G1 = {
    'count': main_data['kol']['g1']['count'],
    'cost': main_data['kol']['g1']['total_cost'],
    'gmv': main_data['kol']['g1']['total_gmv'],
    'store': main_data['kol']['g1']['total_store'],
    'search': main_data['kol']['g1']['total_search'],
    'interact': main_data['kol']['g1']['total_interact'],
    'reads': main_data['kol']['g1']['total_reads'],
}
for row in rows:
    if row['product'] == 'G1' and row['direction'] == '横测' and row['role'] == 'KOC':
        for k in ['count', 'cost', 'gmv', 'store', 'search', 'interact', 'reads']:
            row[k] -= KOL_G1[k]
        break
rows.append({
    'product': 'G1', 'direction': '横测', 'role': 'KOL', **KOL_G1
})

# ── 2. new ruhan data ──
rdf = pd.read_excel('/Users/xiemila/Desktop/【1】如涵国补方向6.29数据汇总.xls', header=0).fillna(0)
for _, r in rdf.iterrows():
    prod = str(r['产品']).upper()
    if prod not in ('S1', 'G1'):
        continue
    rows.append({
        'product': prod,
        'direction': str(r['内容方向']).strip() or '国补回搜',
        'role': 'KOC',
        'count': 1,
        'cost': float(r['总消耗']) if r['总消耗'] else 0,
        'gmv': float(r['gmv']) if r['gmv'] else 0,
        'store': int(r['进店uv']) if r['进店uv'] else 0,
        'search': int(r['搜索uv']) if r['搜索uv'] else 0,
        'interact': int(r['互动量']) if r['互动量'] else 0,
        'reads': int(r['阅读量']) if r['阅读量'] else 0,
    })

# ── 3. new jinka data ──
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
        'product': prod,
        'direction': str(r['内容方向']).strip(),
        'role': 'KOC',
        'count': 1,
        'cost': float(r['总消耗']) if r['总消耗'] else 0,
        'gmv': float(r['gmv']) if r['gmv'] else 0,
        'store': int(r['进店uv']) if r['进店uv'] else 0,
        'search': int(r['搜索uv']) if r['搜索uv'] else 0,
        'interact': int(r['互动量']) if r['互动量'] else 0,
        'reads': int(r['阅读量']) if r['阅读量'] else 0,
    })

# ── 4. aggregate ──
df_rows = pd.DataFrame(rows)
agg_dict = {
    'count': 'sum',
    'cost': 'sum',
    'gmv': 'sum',
    'store': 'sum',
    'search': 'sum',
    'interact': 'sum',
    'reads': 'sum',
}

def make_total(s):
    d = s.to_dict()
    for k in ('store', 'search', 'interact', 'reads'):
        d[k] = int(d[k])
    return d

total = make_total(df_rows.agg(agg_dict))
total['roi'] = safe_div(total['gmv'], TOTAL_BUDGET)
total['cost'] = total['cost']  # actual cost

role_df = df_rows.groupby('role').agg(agg_dict).reset_index()
role = {}
for _, r in role_df.iterrows():
    rec = make_total(r)
    rec.pop('role')
    role[r['role']] = rec
    rec['roi'] = safe_div(rec['gmv'], rec['cost'])
    rec['avg_gmv'] = safe_div(rec['gmv'], rec['count'])
    rec['cpe'] = safe_div(rec['cost'], rec['interact'])

prod_df = df_rows.groupby('product').agg(agg_dict).reset_index()
prod = {}
for _, r in prod_df.iterrows():
    rec = make_total(r)
    rec.pop('product')
    prod[r['product']] = rec
    rec['roi'] = safe_div(rec['gmv'], rec['cost'])
    rec['avg_gmv'] = safe_div(rec['gmv'], rec['count'])
    rec['cpe'] = safe_div(rec['cost'], rec['interact'])

# direction rows grouped by product+direction+role
dir_df = df_rows.groupby(['product', 'direction', 'role']).agg(agg_dict).reset_index()
direction_rows = []
for _, r in dir_df.iterrows():
    rec = make_total(r)
    rec.update({'product': r['product'], 'direction': r['direction'], 'role': r['role']})
    rec['roi'] = safe_div(rec['gmv'], rec['cost'])
    rec['avg_gmv'] = safe_div(rec['gmv'], rec['count'])
    rec['cpe'] = safe_div(rec['cost'], rec['interact']) if rec['interact'] else 0
    direction_rows.append(rec)
direction_rows.sort(key=lambda x: x['roi'], reverse=True)

# ── 5. build HTML ──
metric_card = lambda label, value, unit='', color='#fff': f'''<div class="mega-card"><div class="mega-label">{label}</div><div class="mega-value" style="color:{color}">{value}<span class="mega-unit">{unit}</span></div></div>'''

overview_html = f'''
<div class="section overview-section">
  <h2 class="section-title" style="border-left-color:#fbbf24">全量 786 篇 · 总览</h2>
  <p class="section-sub">总预算 ¥{fmt_num(TOTAL_BUDGET)} · 786 条内容 · KOL {fmt_num(role['KOL']['count'])} 条 · KOC {fmt_num(role['KOC']['count'])} 条 · S1 {fmt_num(prod['S1']['count'])} 条 · G1 {fmt_num(prod['G1']['count'])} 条</p>
  <div class="mega-metrics">
    {metric_card('累计GMV', fmt_wan(total['gmv']), '元', '#34d399')}
    {metric_card('预算 ROI', fmt_num(total['roi'], 2), '×', '#fbbf24')}
    {metric_card('实际消耗', fmt_wan(total['cost']), '元', '#f472b6')}
    {metric_card('预算执行率', f"{safe_div(total['cost'], TOTAL_BUDGET)*100:.1f}", '%', '#60a5fa')}
    {metric_card('累计引流UV', fmt_num(total['store']), '', '#22d3ee')}
    {metric_card('累计搜索UV', fmt_num(total['search']), '', '#a78bfa')}
    {metric_card('总互动量', fmt_num(total['interact']), '', '#fb923c')}
    {metric_card('总阅读量', fmt_num(total['reads']), '', '#e879f9')}
  </div>
</div>
'''

role_html = f'''
<div class="product-row">
  <div class="product-card" style="background: linear-gradient(135deg, #0a1f4d 0%, #1a56db22 100%); border: 1px solid #1a56db;">
    <h3 style="color:#5b9aff">KOC <span class="badge">{fmt_num(role['KOC']['count'])}篇 · ROI {role['KOC']['roi']:.2f}×</span></h3>
    <p class="sub">实际消耗 ¥{fmt_num(role['KOC']['cost'], 0)} · GMV ¥{fmt_num(role['KOC']['gmv'], 0)} · 引流 {fmt_num(role['KOC']['store'])} · 搜索 {fmt_num(role['KOC']['search'])}</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(role['KOC']['cost'])}</div><div class="l">实际消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(role['KOC']['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{role['KOC']['roi']:.2f}×</div><div class="l">实际ROI</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(role['KOC']['cpe'], 1)}</div><div class="l">CPE</div></div>
      <div class="stat-item"><div class="v">{fmt_num(role['KOC']['avg_gmv'], 0)}</div><div class="l">篇均GMV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(role['KOC']['store'])}</div><div class="l">引流UV</div></div>
    </div>
  </div>
  <div class="product-card" style="background: linear-gradient(135deg, #4d0f1a 0%, #ff6b6b22 100%); border: 1px solid #ff6b6b;">
    <h3 style="color:#ff8a8a">KOL <span class="badge">{fmt_num(role['KOL']['count'])}篇 · ROI {role['KOL']['roi']:.2f}×</span></h3>
    <p class="sub">实际消耗 ¥{fmt_num(role['KOL']['cost'], 0)} · GMV ¥{fmt_num(role['KOL']['gmv'], 0)} · 引流 {fmt_num(role['KOL']['store'])} · 搜索 {fmt_num(role['KOL']['search'])}</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(role['KOL']['cost'])}</div><div class="l">实际消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(role['KOL']['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{role['KOL']['roi']:.2f}×</div><div class="l">实际ROI</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(role['KOL']['cpe'], 1)}</div><div class="l">CPE</div></div>
      <div class="stat-item"><div class="v">{fmt_num(role['KOL']['avg_gmv'], 0)}</div><div class="l">篇均GMV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(role['KOL']['store'])}</div><div class="l">引流UV</div></div>
    </div>
  </div>
</div>
'''

product_html = f'''
<div class="product-row">
  <div class="product-card s1">
    <h3>千问 S1 <span class="badge">{fmt_num(prod['S1']['count'])}篇 · ROI {prod['S1']['roi']:.2f}×</span></h3>
    <p class="sub">实际消耗 ¥{fmt_num(prod['S1']['cost'], 0)} · GMV ¥{fmt_num(prod['S1']['gmv'], 0)} · 引流 {fmt_num(prod['S1']['store'])} · 搜索 {fmt_num(prod['S1']['search'])}</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(prod['S1']['cost'])}</div><div class="l">实际消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(prod['S1']['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{prod['S1']['roi']:.2f}×</div><div class="l">实际ROI</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(prod['S1']['avg_gmv'], 0)}</div><div class="l">篇均GMV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(prod['S1']['store'])}</div><div class="l">引流UV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(prod['S1']['search'])}</div><div class="l">搜索UV</div></div>
    </div>
  </div>
  <div class="product-card g1">
    <h3>千问 G1 <span class="badge">{fmt_num(prod['G1']['count'])}篇 · ROI {prod['G1']['roi']:.2f}×</span></h3>
    <p class="sub">实际消耗 ¥{fmt_num(prod['G1']['cost'], 0)} · GMV ¥{fmt_num(prod['G1']['gmv'], 0)} · 引流 {fmt_num(prod['G1']['store'])} · 搜索 {fmt_num(prod['G1']['search'])}</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(prod['G1']['cost'])}</div><div class="l">实际消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(prod['G1']['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{prod['G1']['roi']:.2f}×</div><div class="l">实际ROI</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(prod['G1']['avg_gmv'], 0)}</div><div class="l">篇均GMV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(prod['G1']['store'])}</div><div class="l">引流UV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(prod['G1']['search'])}</div><div class="l">搜索UV</div></div>
    </div>
  </div>
</div>
'''

table_rows_html = ''
for r in direction_rows:
    if r['count'] == 0:
        continue
    roi_color = '#34d399' if r['roi'] >= 10 else ('#fbbf24' if r['roi'] >= 3 else '#f87171')
    role_badge = '<span class="badge" style="background:#1a56db33;color:#5b9aff">KOC</span>' if r['role'] == 'KOC' else '<span class="badge" style="background:#ff6b6b33;color:#ff8a8a">KOL</span>'
    table_rows_html += f'''<tr><td>{r['direction']}</td><td>{r['product']}</td><td>{role_badge}</td><td>{fmt_num(int(r['count']))}</td><td>¥{fmt_num(r['cost'], 0)}</td><td>¥{fmt_num(r['gmv'], 0)}</td><td style="color:{roi_color};font-weight:700">{r['roi']:.2f}×</td><td>{fmt_num(int(r['store']))}</td><td>{fmt_num(int(r['search']))}</td><td>{fmt_num(int(r['interact']))}</td></tr>'''

direction_html = f'''
<div class="section">
  <h2 class="section-title">内容方向效率总表（全量合并后按 ROI 排序）</h2>
  <p class="section-sub">铺量 + 如涵 + 金咖统一聚合，按 S1/G1 + KOC/KOL + 内容方向排序</p>
  <div class="chart-container" style="overflow-x:auto;">
    <table class="top-table mega-table">
      <thead><tr><th>内容方向</th><th>产品</th><th>身份</th><th>篇数</th><th>消耗</th><th>GMV</th><th>ROI</th><th>进店UV</th><th>搜索UV</th><th>互动量</th></tr></thead>
      <tbody>{table_rows_html}</tbody>
    </table>
  </div>
</div>
'''

kiss_html = f'''
<div class="section">
  <h2 class="section-title">全量 786 篇 KISS 结论</h2>
  <div class="kiss-grid">
    <div class="kiss-card kiss-keep">
      <div class="kiss-title">KEEP</div>
      <div class="kiss-v">KOC 仍是效率基本盘：统一后 {role['KOC']['count']} 篇，实际 ROI {role['KOC']['roi']:.2f}×，远高于 KOL {role['KOL']['roi']:.2f}×</div>
      <div class="kiss-v">S1 高客单模型成立：{prod['S1']['count']} 篇 ROI {prod['S1']['roi']:.2f}×，显著高于 G1 {prod['G1']['roi']:.2f}×</div>
      <div class="kiss-v">纵测、读书日借势、G1 横测 继续规模化复制</div>
    </div>
    <div class="kiss-card kiss-improve">
      <div class="kiss-title">IMPROVE</div>
      <div class="kiss-v">KOL 34 篇全部压在 G1 横测，应扩展到 S1 高 ROI 方向（纵测/读书日借势）</div>
      <div class="kiss-v">节点类内容（520/618/明星）沉淀周期短，需提前 2-4 周前置铺设</div>
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
'''

panel_html = f'''<div class="panel panel-mega" id="panel-mega" data-panel="mega">
<header><h1>全量 786 篇统一视图</h1><p>总预算 ¥95万 · 786 条内容 · KOL {fmt_num(role['KOL']['count'])} 条 · KOC {fmt_num(role['KOC']['count'])} 条 · S1 {fmt_num(prod['S1']['count'])} 条 · G1 {fmt_num(prod['G1']['count'])} 条</p></header>
<div class="container">
  {overview_html}
  <div class="section">
    <h2 class="section-title">KOC vs KOL 身份维度</h2>
    {role_html}
  </div>
  <div class="section">
    <h2 class="section-title">S1 vs G1 产品维度</h2>
    {product_html}
  </div>
  {direction_html}
  {kiss_html}
</div>
</div>'''

# ── 6. inject ──
for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')
    # 1) remove old 铺量/测试 target completion block
    start = h.find('<!-- ═══ NEW: 项目概括 + 目标完成情况 ═══ -->')
    if start != -1:
        end = h.find('<!-- ═══ 总览：S1 vs G1 ═══ -->', start)
        if end == -1:
            end = h.find('<!-- ═══ S1 细分 ═══ -->', start)
        h = h[:start] + h[end:]
    # 2) ensure tab button
    btn = '<button class="tab-btn" data-tab="mega"><span class="ic">🌍</span><span class="nm">全量786篇</span></button>'
    if 'data-tab="mega"' not in h:
        h = h.replace('<div class="tabs">', '<div class="tabs">' + btn, 1)
    # 3) remove existing panel-mega and insert new
    if 'id="panel-mega"' in h:
        pm_start = h.find('<div class="panel panel-mega"')
        pm_end = h.find('<div class="panel panel-s1g1"', pm_start)
        h = h[:pm_start] + h[pm_end:]
    h = h.replace('<div class="panel panel-s1g1"', panel_html + '\n<div class="panel panel-s1g1"', 1)
    # 4) ensure mega CSS
    MEGA_CSS = '''
/* ── mega 786 panel ── */
.mega-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 18px 0; }
.mega-card { background: rgba(15,23,42,0.72); border: 1px solid rgba(148,163,184,0.12); border-radius: 12px; padding: 16px; text-align: center; }
.mega-label { font-size: 12px; color: #94a3b8; margin-bottom: 8px; }
.mega-value { font-size: 28px; font-weight: 700; line-height: 1.2; }
.mega-unit { font-size: 13px; color: #94a3b8; margin-left: 4px; font-weight: 500; }
.mega-table { font-size: 12px; }
.mega-table th { background: rgba(255,255,255,0.06); color: #94a3b8; }
.mega-table td { padding: 10px 8px; }
@media (max-width: 900px) { .mega-metrics { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .mega-metrics { grid-template-columns: 1fr; } }
'''
    if '.mega-metrics' not in h:
        h = h.replace('</style>', MEGA_CSS + '</style>', 1)
    tgt.write_text(h, encoding='utf-8')
    print(f'✓ rebuilt {tgt.relative_to(ROOT)}')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')

summary = {
    'budget': TOTAL_BUDGET,
    'total': total,
    'role': {k: {kk: vv for kk, vv in v.items()} for k, v in role.items()},
    'product': {k: {kk: vv for kk, vv in v.items()} for k, v in prod.items()},
    'direction_top10': direction_rows[:10],
}
with open('outputs/mega_786_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print('✓ saved outputs/mega_786_summary.json')
