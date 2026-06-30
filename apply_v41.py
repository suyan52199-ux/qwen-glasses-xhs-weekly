#!/usr/bin/env python3
"""
R41:
1. 修复「全量 786 篇」panel 排版/溢出问题。
2. 用统一后的 786 篇数据重做主池桑基图：身份 → 产品 → 方向 → 转化效果。
3. 保留内容分析、标题分析 section 不动。
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


# ── 1. rebuild unified rows (same as R40) ──
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
rows.append({'product': 'G1', 'direction': '横测', 'role': 'KOL', **KOL_G1})

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

df_rows = pd.DataFrame(rows)

# ── 2. build unified sankey: role -> product -> (product·direction) -> outcome ──
nodes = [{'name': 'KOC'}, {'name': 'KOL'}, {'name': 'S1'}, {'name': 'G1'}]
links = []

# role -> product
for (role, prod), g in df_rows.groupby(['role', 'product']):
    cnt = int(g['count'].sum())
    if cnt:
        links.append({'source': role, 'target': prod, 'value': cnt})

# product -> product·direction
for (prod, direction), g in df_rows.groupby(['product', 'direction']):
    cnt = int(g['count'].sum())
    if cnt:
        node_name = f'{prod} · {direction}'
        nodes.append({'name': node_name})
        links.append({'source': prod, 'target': node_name, 'value': cnt})

# direction -> outcome based on direction ROI
outcome_nodes = ['高ROI(≥10x)', '中ROI(3-10x)', '低ROI(<3x)']
for o in outcome_nodes:
    nodes.append({'name': o})

for (prod, direction), g in df_rows.groupby(['product', 'direction']):
    cnt = int(g['count'].sum())
    if cnt == 0:
        continue
    roi = safe_div(g['gmv'].sum(), g['cost'].sum())
    if roi >= 10:
        outcome = '高ROI(≥10x)'
    elif roi >= 3:
        outcome = '中ROI(3-10x)'
    else:
        outcome = '低ROI(<3x)'
    links.append({'source': f'{prod} · {direction}', 'target': outcome, 'value': cnt})

new_sankey = {'nodes': nodes, 'links': links}

# ── 3. patch HTML ──
for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')

    # replace sankey_nodes / sankey_links in main DATA block
    m = re.search(r'function\s+init_s1g1\s*\(', h)
    data_start = h.index('const DATA = {', m.end())
    brace = h.find('{', data_start)
    depth = 1
    j = brace + 1
    while j < len(h) and depth > 0:
        if h[j] == '{':
            depth += 1
        elif h[j] == '}':
            depth -= 1
        j += 1
    d = json.loads(h[brace:j])
    d['sankey_nodes'] = new_sankey['nodes']
    d['sankey_links'] = new_sankey['links']
    new_data_block = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
    h = h[:brace] + new_data_block + h[j:]

    # update sankey section title & conclusion to unified
    old_title = '<h3>身份 → 产品 → 方向 → 转化效果（笔记数流向）</h3>'
    new_title = '<h3>身份 → 产品 → 方向 → 转化效果（786 篇笔记数流向）</h3>'
    h = h.replace(old_title, new_title)

    old_conclusion = '''<div class="conclusion-box"><h4>桑基图结论</h4><ul><li><strong>KOC 是绝对主力</strong>：600 篇 KOC 中 S1 236 篇、G1 364 篇，KOL 仅 34 篇且全部流向 G1 横测</li><li><strong>S1 读书日借势是高 ROI 爆点</strong>：28 篇全部落入「高 ROI(≥10x)」，是效率最高的内容方向</li><li><strong>G1 横测流量最大但 ROI 分层严重</strong>：271 篇中一部分进入高 ROI，另一部分进入中/低 ROI，说明账号质量/标题结构差异大</li><li><strong>低 ROI 占比不容忽视</strong>：明星热点、场景对比等方向多数流向中低 ROI，需要控量或优化内容</li></ul></div></div><!-- ═══════ 气泡图 ═══════ -->'''
    new_conclusion = '''<div class="conclusion-box"><h4>桑基图结论</h4><ul><li><strong>全量 786 篇统一视角</strong>：KOC 752 篇是主力，KOL 34 篇全部流向 G1；S1 343 篇、G1 443 篇，G1 内容量更大但 S1 高 ROI 方向更集中</li><li><strong>S1 纵测 + 读书日借势继续是高 ROI 爆点</strong>：两条管道均流入「高 ROI(≥10x)」，是决策末端最高效内容</li><li><strong>G1 横测流量最大但 ROI 分层严重</strong>：大量笔记流向中/低 ROI，说明账号质量与内容结构差异大，需要筛号+标题优化</li><li><strong>测试池并入后国补回搜/各类对比方向以中低 ROI 为主</strong>：验证后应只把高 ROI 模板复制到铺量，低 ROI 方向控预算</li></ul></div></div><!-- ═══════ 气泡图 ═══════ -->'''
    h = h.replace(old_conclusion, new_conclusion)

    # add CSS to prevent overflow in mega panel
    extra_css = '''
/* ── R41 layout fixes ── */
.panel-mega .chart-container { max-width: 100%; box-sizing: border-box; overflow-x: auto; }
.panel-mega .mega-table { width: 100%; table-layout: auto; }
.panel-mega .mega-table th, .panel-mega .mega-table td { white-space: nowrap; font-size: 11px; padding: 8px 6px; }
.panel-mega .mega-table td:first-child { white-space: normal; min-width: 120px; }
.panel-mega .product-card .stats { grid-template-columns: repeat(3, 1fr); }
@media (max-width: 900px) {
  .panel-mega .mega-metrics { grid-template-columns: repeat(2, 1fr); }
  .panel-mega .product-row { grid-template-columns: 1fr; }
  .panel-mega .product-card .stats { grid-template-columns: repeat(2, 1fr); }
  .panel-mega .mega-table th, .panel-mega .mega-table td { font-size: 10px; padding: 6px 4px; }
}
@media (max-width: 600px) {
  .panel-mega .mega-metrics { grid-template-columns: 1fr; }
  .panel-mega .product-card .stats { grid-template-columns: 1fr 1fr; }
}
'''
    if '/* ── R41 layout fixes ── */' not in h:
        h = h.replace('</style>', extra_css + '</style>', 1)

    tgt.write_text(h, encoding='utf-8')
    print(f'✓ patched {tgt.relative_to(ROOT)}')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')

with open('outputs/mega_786_sankey.json', 'w', encoding='utf-8') as f:
    json.dump(new_sankey, f, ensure_ascii=False, indent=2)
print('✓ saved outputs/mega_786_sankey.json')
