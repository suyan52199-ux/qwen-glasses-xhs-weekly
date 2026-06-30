#!/usr/bin/env python3
"""
R39: 全量 786 篇完全合并，不再区分铺量/测试。
按 KOC/KOL 身份 + S1/G1 产品 + 统一内容方向重新计算并更新 mega panel。
口径：铺量 6.22 + 如涵 6.29 + 金咖 6.29；测试池并入对应身份/产品。
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


def classify_direction(title: str) -> str:
    t = str(title).lower()
    # product-agnostic direction classification
    if '读书' in title or '阅读' in title:
        return '读书日借势'
    if '520' in title:
        return '520热点'
    if '618' in title or '大促' in title or '必入清单' in title or '挑花眼' in title:
        return '618大促'
    if '国补' in title or '补贴' in title or '抄底' in title or '捡漏' in title:
        return '国补攻略'
    if '场景对比' in title or '场景' in title and ('对比' in title or 'vs' in title):
        return '场景对比'
    if '明星' in title or '代言' in title or '同款' in title and '明星' in title:
        return '明星热点'
    if '选购' in title or '攻略' in title and not any(k in t for k in ['横测', '横评', 'vs', '纵测']):
        return '选购攻略'
    # 纵测：同品牌产品线内对决
    if any(k in title for k in ['千问S1和G1', 'S1和G1', 'S1 vs G1', '夸克S1', '千问S1']):
        # If it also looks like 横测 (multiple brands), classify as 横测
        if '横测' in title or '横评' in title or '对比' in title and ('vs' in title or '和' in title):
            return '横测'
        if '千问S1和G1' in title or 'S1和G1' in title or 'S1 vs G1' in title:
            return '纵测'
    if any(k in title for k in ['横测', '横评', '对比', 'vs', '怎么选', '多款', '几款', '闭眼选', '测评', '红黑榜']):
        return '横测'
    if any(k in title for k in ['踩雷', '避坑', '别乱买', '红黑榜', '坑', '乱买', '别被骗']):
        return '避坑种草'
    if any(k in title for k in ['真实体验', '实测', '入手', '真香', '后悔', '开箱', '无广', '戴一周', '太绝了', '值吗']):
        return '用户证言'
    if any(k in title for k in ['功能', '配置', '续航', '翻译', '参数', '硬核', '办公', '学习', '旅行', '拍照', '出差', '演讲', '汇报', '学生党']):
        return '功能卖点'
    if any(k in title for k in ['场景', '生活', '日常', '职场', '户外', '出行', '打工人', '创业', '治愈']):
        return '场景体验'
    return '其他种草'


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

rows = []  # each row: product, direction, role, count, cost, gmv, store, search, interact, reads

# 主池 KOC 方向
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

# 主池 G1 横测需要拆出 KOL 部分（主池方向聚合包含全部 KOC+KOL）
KOL_G1 = {
    'count': main_data['kol']['g1']['count'],
    'cost': main_data['kol']['g1']['total_cost'],
    'gmv': main_data['kol']['g1']['total_gmv'],
    'store': main_data['kol']['g1']['total_store'],
    'search': main_data['kol']['g1']['total_search'],
    'interact': main_data['kol']['g1']['total_interact'],
    'reads': main_data['kol']['g1']['total_reads'],
}
# 从 G1 横测中扣除 KOL，剩余为 KOC
for row in rows:
    if row['product'] == 'G1' and row['direction'] == '横测' and row['role'] == 'KOC':
        for k in ['count','cost','gmv','store','search','interact','reads']:
            row[k] -= KOL_G1[k]
        break

# 单独加入 KOL 行
rows.append({
    'product': 'G1',
    'direction': '横测',
    'role': 'KOL',
    **KOL_G1
})

# ── 2. 如涵数据 ──
rdf = pd.read_excel('/Users/xiemila/Desktop/如涵国补方向6.29数据汇总.xls', header=0).fillna(0)
ruhan_budget = 100000.0
ruhan_actual_cost = float(rdf['总消耗'].sum())
for _, r in rdf.iterrows():
    title = str(r['达人昵称']) if pd.notna(r['达人昵称']) else ''  # xls 无标题列，用昵称代替做方向归类参考
    # 重新用 product 列
    prod = str(r['内容方向']).upper()
    if prod not in ('S1', 'G1'):
        continue
    actual_cost = float(r['总消耗']) if r['总消耗'] else 0
    allocated_cost = safe_div(actual_cost, ruhan_actual_cost) * ruhan_budget if ruhan_actual_cost else 0
    rows.append({
        'product': prod,
        'direction': classify_direction(title),
        'role': 'KOC',
        'count': 1,
        'cost': allocated_cost,
        'gmv': float(r['gmv']) if r['gmv'] else 0,
        'store': int(r['进店uv']) if r['进店uv'] else 0,
        'search': int(r['搜索uv']) if r['搜索uv'] else 0,
        'interact': int(r['互动量']) if r['互动量'] else 0,
        'reads': int(r['阅读量']) if r['阅读量'] else 0,
    })

# ── 3. 金咖数据 ──
jdf = pd.read_excel('/Users/xiemila/Downloads/金咖618节点KOC促单汇总.xlsx', sheet_name='蒲公英源表', header=2).fillna(0)
jinka_budget = 50000.0
jinka_total_gmv = 320082.29
# proxies
jdf['cost_proxy'] = pd.to_numeric(jdf['博主报价'], errors='coerce').fillna(0) + pd.to_numeric(jdf['服务费金额'], errors='coerce').fillna(0)
jdf['reads'] = pd.to_numeric(jdf['阅读量'], errors='coerce').fillna(0)
jdf['interact'] = pd.to_numeric(jdf['互动量'], errors='coerce').fillna(0)
jdf['store_proxy'] = pd.to_numeric(jdf.iloc[:, 123], errors='coerce').fillna(0) + pd.to_numeric(jdf.iloc[:, 125], errors='coerce').fillna(0)
jdf['search_proxy'] = pd.to_numeric(jdf.iloc[:, 125], errors='coerce').fillna(0)

jinka_total_cost_proxy = jdf['cost_proxy'].sum()
jinka_total_store_proxy = jdf['store_proxy'].sum()

for _, r in jdf.iterrows():
    coop = str(r['合作名称'])
    if 'S1' in coop:
        prod = 'S1'
    elif 'G1' in coop:
        prod = 'G1'
    else:
        continue
    title = str(r['笔记标题'])
    allocated_cost = safe_div(r['cost_proxy'], jinka_total_cost_proxy) * jinka_budget if jinka_total_cost_proxy else 0
    allocated_gmv = safe_div(r['store_proxy'], jinka_total_store_proxy) * jinka_total_gmv if jinka_total_store_proxy else 0
    rows.append({
        'product': prod,
        'direction': classify_direction(title),
        'role': 'KOC',
        'count': 1,
        'cost': allocated_cost,
        'gmv': allocated_gmv,
        'store': int(r['store_proxy']),
        'search': int(r['search_proxy']),
        'interact': int(r['interact']),
        'reads': int(r['reads']),
    })

# ── 4. 聚合 ──
import pandas as pd
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

# overall
total = df_rows.agg(agg_dict).to_dict()
total['store'] = int(total['store'])
total['search'] = int(total['search'])
total['interact'] = int(total['interact'])
total['reads'] = int(total['reads'])
total['roi'] = safe_div(total['gmv'], total['cost'])
total['cpe'] = safe_div(total['cost'], total['interact'])
total['avg_gmv'] = safe_div(total['gmv'], total['count'])

# by role
role_df = df_rows.groupby('role').agg(agg_dict).reset_index()
role = {r['role']: {k: (int(v) if k in ('store','search','interact','reads') else v) for k,v in r.items() if k!='role'} for _, r in role_df.iterrows()}
for r in role.values():
    r['roi'] = safe_div(r['gmv'], r['cost'])
    r['cpe'] = safe_div(r['cost'], r['interact'])
    r['avg_gmv'] = safe_div(r['gmv'], r['count'])

# by product
prod_df = df_rows.groupby('product').agg(agg_dict).reset_index()
prod = {r['product']: {k: (int(v) if k in ('store','search','interact','reads') else v) for k,v in r.items() if k!='product'} for _, r in prod_df.iterrows()}
for r in prod.values():
    r['roi'] = safe_div(r['gmv'], r['cost'])
    r['avg_gmv'] = safe_div(r['gmv'], r['count'])

# by product + direction + role
dir_df = df_rows.groupby(['product', 'direction', 'role']).agg(agg_dict).reset_index()
direction_rows = []
for _, r in dir_df.iterrows():
    rec = {k: (int(v) if k in ('store','search','interact','reads') else v) for k,v in r.items() if k not in ('product','direction','role')}
    rec.update({'product': r['product'], 'direction': r['direction'], 'role': r['role']})
    rec['roi'] = safe_div(rec['gmv'], rec['cost'])
    rec['avg_gmv'] = safe_div(rec['gmv'], rec['count'])
    rec['cpe'] = safe_div(rec['cost'], rec['interact']) if rec['interact'] else 0
    direction_rows.append(rec)
direction_rows.sort(key=lambda x: x['roi'], reverse=True)


# ── 5. 生成 HTML ──
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
    <h3 style="color:#5b9aff">KOC 中腰部 <span class="badge">{fmt_num(role['KOC']['count'])}篇 · ROI {role['KOC']['roi']:.2f}×</span></h3>
    <p class="sub">铺量 600 篇 + 如涵 80 篇 + 金咖 72 篇 · 全部按 KOC 统一口径</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(role['KOC']['cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(role['KOC']['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{role['KOC']['roi']:.2f}×</div><div class="l">整体ROI</div></div>
      <div class="stat-item"><div class="v">{fmt_num(role['KOC']['store'])}</div><div class="l">进店UV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(role['KOC']['search'])}</div><div class="l">搜索UV</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(role['KOC']['cpe'], 1)}</div><div class="l">CPE</div></div>
    </div>
  </div>
  <div class="product-card" style="background: linear-gradient(135deg, #4d0f1a 0%, #ff6b6b22 100%); border: 1px solid #ff6b6b;">
    <h3 style="color:#ff8a8a">KOL 头部 <span class="badge">{fmt_num(role['KOL']['count'])}篇 · ROI {role['KOL']['roi']:.2f}×</span></h3>
    <p class="sub">铺量 34 篇 · 全在 G1 · 统一按 KOL 口径</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(role['KOL']['cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(role['KOL']['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{role['KOL']['roi']:.2f}×</div><div class="l">整体ROI</div></div>
      <div class="stat-item"><div class="v">{fmt_num(role['KOL']['store'])}</div><div class="l">进店UV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(role['KOL']['search'])}</div><div class="l">搜索UV</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(role['KOL']['cpe'], 1)}</div><div class="l">CPE</div></div>
    </div>
  </div>
</div>
'''

product_html = f'''
<div class="product-row">
  <div class="product-card s1">
    <h3>千问 S1 <span class="badge">带屏旗舰款 · {fmt_num(prod['S1']['count'])}篇</span></h3>
    <p class="sub">KOC + KOL 全量合并 · 不再区分铺量/测试</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(prod['S1']['cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(prod['S1']['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{prod['S1']['roi']:.2f}×</div><div class="l">整体ROI</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(prod['S1']['avg_gmv'], 0)}</div><div class="l">篇均GMV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(prod['S1']['store'])}</div><div class="l">进店UV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(prod['S1']['search'])}</div><div class="l">搜索UV</div></div>
    </div>
  </div>
  <div class="product-card g1">
    <h3>千问 G1 <span class="badge">轻量音频款 · {fmt_num(prod['G1']['count'])}篇</span></h3>
    <p class="sub">KOC + KOL 全量合并 · 不再区分铺量/测试</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(prod['G1']['cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(prod['G1']['gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{prod['G1']['roi']:.2f}×</div><div class="l">整体ROI</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(prod['G1']['avg_gmv'], 0)}</div><div class="l">篇均GMV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(prod['G1']['store'])}</div><div class="l">进店UV</div></div>
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
    table_rows_html += f'''<tr><td>{r['direction']}</td><td>{r['product']}</td><td>{role_badge}</td><td>{r['count']}</td><td>¥{fmt_num(r['cost'], 0)}</td><td>¥{fmt_num(r['gmv'], 0)}</td><td style="color:{roi_color};font-weight:700">{r['roi']:.2f}×</td><td>{fmt_num(r['store'])}</td><td>{fmt_num(r['search'])}</td><td>{fmt_num(r['interact'])}</td></tr>'''

direction_html = f'''
<div class="section">
  <h2 class="section-title">内容方向效率总表（全量合并后按 ROI 排序）</h2>
  <p class="section-sub">不再区分铺量/测试，统一按 S1/G1 + KOC/KOL + 内容方向聚合</p>
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
      <div class="kiss-v">KOC 仍是效率基本盘：统一后 {role['KOC']['count']} 篇，ROI {role['KOC']['roi']:.2f}×，远高于 KOL {role['KOL']['roi']:.2f}×</div>
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
      <div class="kiss-v">建立「786 篇全量统一周报」口径，每周按 KOC/KOL + S1/G1 + 方向更新</div>
    </div>
  </div>
</div>
'''

panel_html = f'''<div class="panel panel-mega" id="panel-mega" data-panel="mega">
<header><h1>全量 786 篇统一视图</h1><p>铺量 + 如涵 + 金咖完全合并 · 统一按 KOC/KOL + S1/G1 + 内容方向计算 · 数据口径：铺量 6.22 + 如涵 6.29 + 金咖 6.29</p></header>
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

# ── 6. 注入 ──
for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')
    # ensure tab button exists
    btn = '<button class="tab-btn" data-tab="mega"><span class="ic">🌍</span><span class="nm">全量786篇</span></button>'
    if 'data-tab="mega"' not in h:
        h = h.replace('<div class="tabs">', '<div class="tabs">' + btn, 1)
    # remove existing panel-mega
    if 'id="panel-mega"' in h:
        # remove from <div class="panel panel-mega" ... to the next <div class="panel panel-"
        start = h.find('<div class="panel panel-mega"')
        next_panel = h.find('<div class="panel panel-', start + 1)
        h = h[:start] + h[next_panel:]
    # insert new panel before panel-s1g1
    h = h.replace('<div class="panel panel-s1g1"', panel_html + '\n<div class="panel panel-s1g1"', 1)
    # ensure mega CSS
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
    'total': {k: v for k, v in total.items()},
    'role': {k: {kk: vv for kk, vv in v.items()} for k, v in role.items()},
    'product': {k: {kk: vv for kk, vv in v.items()} for k, v in prod.items()},
    'direction_top10': direction_rows[:10],
}
with open('outputs/mega_786_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print('✓ saved outputs/mega_786_summary.json')
