#!/usr/bin/env python3
"""
R43:
1. 修复「全量 786 篇」panel 中 KOC/KOL、S1/G1 卡片被压成一列的问题，恢复桌面端双列并排。
2. 将 panel-s1g1 中第一层 S1 vs G1 的图表数据（local DATA.overall / koc / kol）更新为全量 786 篇口径，
   与顶部卡片一致；方向细分等图表仍保持铺量池 634 篇（已有说明）。
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


def safe_div(a, b): return a / b if b else 0


def map_main_dir(name: str) -> str:
    if '横测' in name: return '横测'
    if '纵测' in name: return '纵测'
    if '读书日' in name: return '读书日借势'
    if '520' in name: return '520热点'
    if '618' in name: return '618大促'
    if '场景对比' in name: return '场景对比'
    if '明星' in name: return '明星热点'
    if '选购攻略' in name: return '选购攻略'
    return '其他种草'


# ── rebuild unified rows ──
h_main = TARGETS[0].read_text(encoding='utf-8')
m = re.search(r'function\s+init_s1g1\s*\(', h_main)
i = h_main.index('const DATA = {', m.end())
brace = h_main.find('{', i)
depth = 1; j = brace + 1
while j < len(h_main) and depth > 0:
    if h_main[j] == '{': depth += 1
    elif h_main[j] == '}': depth -= 1
    j += 1
main_data = json.loads(h_main[brace:j])

rows = []
for row in main_data['s1_dirs']:
    rows.append({'product':'S1','direction':map_main_dir(row['内容方向']),'role':'KOC',
                 'count':row['count'],'cost':row['总消耗'],'gmv':row['gmv'],'store':row['进店uv'],
                 'search':row['搜索uv'],'interact':row['互动量'],'reads':row['阅读量']})
for row in main_data['g1_dirs']:
    rows.append({'product':'G1','direction':map_main_dir(row['内容方向']),'role':'KOC',
                 'count':row['count'],'cost':row['总消耗'],'gmv':row['gmv'],'store':row['进店uv'],
                 'search':row['搜索uv'],'interact':row['互动量'],'reads':row['阅读量']})

KOL_G1 = {'count': main_data['kol']['g1']['count'], 'cost': main_data['kol']['g1']['total_cost'],
          'gmv': main_data['kol']['g1']['total_gmv'], 'store': main_data['kol']['g1']['total_store'],
          'search': main_data['kol']['g1']['total_search'], 'interact': main_data['kol']['g1']['total_interact'],
          'reads': main_data['kol']['g1']['total_reads']}
for row in rows:
    if row['product'] == 'G1' and row['direction'] == '横测' and row['role'] == 'KOC':
        for k in KOL_G1: row[k] -= KOL_G1[k]
        break
rows.append({'product':'G1','direction':'横测','role':'KOL',**KOL_G1})

rdf = pd.read_excel('/Users/xiemila/Desktop/【1】如涵国补方向6.29数据汇总.xls', header=0).fillna(0)
for _, r in rdf.iterrows():
    prod = str(r['产品']).upper()
    if prod not in ('S1','G1'): continue
    rows.append({'product':prod,'direction':str(r['内容方向']).strip() or '国补回搜','role':'KOC','count':1,
                 'cost':float(r['总消耗']) if r['总消耗'] else 0,'gmv':float(r['gmv']) if r['gmv'] else 0,
                 'store':int(r['进店uv']) if r['进店uv'] else 0,'search':int(r['搜索uv']) if r['搜索uv'] else 0,
                 'interact':int(r['互动量']) if r['互动量'] else 0,'reads':int(r['阅读量']) if r['阅读量'] else 0})

jdf = pd.read_excel('/Users/xiemila/Downloads/金咖koc内容.xlsx', header=0).fillna(0)
for _, r in jdf.iterrows():
    prod_raw = str(r['产品'])
    if 'S1' in prod_raw: prod = 'S1'
    elif 'G1' in prod_raw: prod = 'G1'
    else: continue
    rows.append({'product':prod,'direction':str(r['内容方向']).strip(),'role':'KOC','count':1,
                 'cost':float(r['总消耗']) if r['总消耗'] else 0,'gmv':float(r['gmv']) if r['gmv'] else 0,
                 'store':int(r['进店uv']) if r['进店uv'] else 0,'search':int(r['搜索uv']) if r['搜索uv'] else 0,
                 'interact':int(r['互动量']) if r['互动量'] else 0,'reads':int(r['阅读量']) if r['阅读量'] else 0})

df = pd.DataFrame(rows)

# helper to build summary object
def build_summary(s):
    count = int(s['count'].sum())
    return {
        'count': count,
        'total_cost': round(s['cost'].sum(), 2),
        'total_gmv': round(s['gmv'].sum(), 2),
        'total_store': int(s['store'].sum()),
        'total_interact': int(s['interact'].sum()),
        'total_search': int(s['search'].sum()),
        'total_reads': int(s['reads'].sum()),
        'roi': round(safe_div(s['gmv'].sum(), s['cost'].sum()), 2),
        'with_gmv': int((s['gmv'] > 0).sum()),  # aggregated rows count as 1; acceptable for chart
        'with_gmv_pct': round(100 * (s['gmv'] > 0).sum() / count, 1) if count else 0,
        'avg_cost': round(safe_div(s['cost'].sum(), count)),
        'avg_interact': round(safe_div(s['interact'].sum(), count)),
        'avg_store': round(safe_div(s['store'].sum(), count), 1),
        'avg_search': round(safe_div(s['search'].sum(), count), 1),
        'avg_gmv': round(safe_div(s['gmv'].sum(), count)),
        'avg_reads': round(safe_div(s['reads'].sum(), count)),
    }

overall_s1 = build_summary(df[df['product'] == 'S1'])
overall_g1 = build_summary(df[df['product'] == 'G1'])
koc_s1 = build_summary(df[(df['role'] == 'KOC') & (df['product'] == 'S1')])
koc_g1 = build_summary(df[(df['role'] == 'KOC') & (df['product'] == 'G1')])
kol_g1 = build_summary(df[(df['role'] == 'KOL') & (df['product'] == 'G1')])

# maintain labels
def label(d, label_text):
    d['label'] = label_text
    return d

new_overall = {'s1': label(overall_s1, 'S1'), 'g1': label(overall_g1, 'G1')}
new_koc = {'s1': label(koc_s1, 'S1·KOC'), 'g1': label(koc_g1, 'G1·KOC')}
new_kol = {'s1': None, 'g1': label(kol_g1, 'G1·KOL')}

# ── patch HTML ──
for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')

    # 1) update local DATA block overall/koc/kol in init_s1g1
    pat = r'(function init_s1g1\(\)\{try\{const DATA = )(\{.*?\})(;.*?productVs)'
    def data_repl(m):
        try:
            d = json.loads(m.group(2))
        except Exception as e:
            print('json parse err', e)
            return m.group(0)
        d['overall'] = new_overall
        d['koc'] = new_koc
        d['kol'] = new_kol
        return m.group(1) + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + m.group(3)
    h2 = re.sub(pat, data_repl, h, count=1, flags=re.DOTALL)
    if h2 == h:
        print('WARN: local DATA block not replaced in', tgt)
    h = h2

    # 2) fix panel-mega product-row grid and table styles
    old_css = '''/* ── R42 layout fixes ── */
.mega-dir-row { align-items: flex-start; }
.mega-dir-row .chart-container { min-width: 0; }
.mega-dir-row .table-wrap { overflow-x: auto; }
.panel-mega .mega-table td:first-child { min-width: 100px; max-width: 180px; white-space: normal; }
.panel-mega .mega-table th, .panel-mega .mega-table td { font-size: 11px; padding: 7px 5px; }
@media (max-width: 900px) {
  .mega-dir-row { grid-template-columns: 1fr; }
}
'''
    new_css = '''/* ── R43 layout fixes ── */
.panel-mega .product-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.panel-mega .mega-metrics { grid-template-columns: repeat(4, 1fr); }
.mega-dir-row { align-items: flex-start; }
.mega-dir-row .chart-container { min-width: 0; overflow-x: auto; }
.mega-dir-row .table-wrap { overflow-x: auto; }
.panel-mega .mega-table { width: 100%; table-layout: auto; }
.panel-mega .mega-table td:first-child { min-width: 90px; max-width: 160px; white-space: normal; word-break: break-word; }
.panel-mega .mega-table th, .panel-mega .mega-table td { white-space: nowrap; font-size: 11px; padding: 6px 5px; }
.panel-mega .product-card .stats { grid-template-columns: repeat(3, 1fr); gap: 10px; }
@media (max-width: 1100px) {
  .panel-mega .mega-metrics { grid-template-columns: repeat(2, 1fr); }
  .panel-mega .product-row { grid-template-columns: 1fr; }
  .panel-mega .product-card .stats { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 600px) {
  .panel-mega .mega-metrics { grid-template-columns: 1fr; }
  .panel-mega .mega-table th, .panel-mega .mega-table td { font-size: 10px; padding: 5px 4px; }
  .panel-mega .product-card .stats { grid-template-columns: repeat(2, 1fr); }
}
'''
    if '/* ── R43 layout fixes ── */' not in h:
        h = h.replace(old_css, new_css)
        # if old_css not present, insert before </style>
        if '/* ── R43 layout fixes ── */' not in h:
            h = h.replace('</style>', new_css + '</style>', 1)

    # 3) update panel-mega KOC vs KOL section title to full data note
    h = h.replace('<h2 class="section-title">KOC vs KOL 身份维度</h2>',
                  '<h2 class="section-title">KOC vs KOL 身份维度（全量 786 篇）</h2>')

    tgt.write_text(h, encoding='utf-8')
    print(f'✓ patched {tgt.relative_to(ROOT)}')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')

# save verification
with open('outputs/mega_786_s1g1_overall.json', 'w', encoding='utf-8') as f:
    json.dump({'overall': new_overall, 'koc': new_koc, 'kol': new_kol}, f, ensure_ascii=False, indent=2)
