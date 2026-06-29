#!/usr/bin/env python3
"""
R34: 在金咖（panel-promo）和如涵（panel-ruhan）数据模块中补充「内容标题方向效率分析」：
横测 / 纵测（千问S1 vs G1、千问S1 vs 夸克S1、千问G1 vs 夸克G1）/ 用户证言 / 价格促销 / 其他。
同时提供「标准模块样例」标题卡片，方便汇报时让大家快速看懂类型。
TARGETS（硬规则）：docs dark + outputs/KOC铺量内容.html
"""
import re, json, shutil
from pathlib import Path
from collections import defaultdict
import pandas as pd

ROOT = Path('/Users/xiemila/.qoderwork/workspace/mq6ecbjzd6kpfcgy')
TARGETS = [
    ROOT / 'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    ROOT / 'outputs/KOC铺量内容.html',
]
DESKTOP = Path('/Users/xiemila/Desktop/KOC铺量内容.html')

# ── classification ──
ALL_DIRS = [
    '横测',
    '纵测·千问S1 vs 千问G1',
    '纵测·千问S1 vs 夸克S1',
    '纵测·千问G1 vs 夸克G1',
    '用户证言',
    '价格促销',
    '其他',
]

def classify(title: str) -> str:
    t = title.lower()
    has_qw = '千问' in title
    has_kk = '夸克' in title
    has_s1 = 's1' in t or 'S1' in title
    has_g1 = 'g1' in t or 'G1' in title
    if has_qw and has_s1 and has_g1:
        return '纵测·千问S1 vs 千问G1'
    if has_qw and has_kk and has_s1:
        return '纵测·千问S1 vs 夸克S1'
    if has_qw and has_kk and has_g1:
        return '纵测·千问G1 vs 夸克G1'
    h_keys = ['横测', '横评', '对比', 'vs', '怎么选', '红黑榜', '选购', '多款', '几款', '必入清单', '闭眼选', '抄作业', '测评']
    if any(k in t for k in h_keys):
        return '横测'
    if any(k in t for k in ['真实体验', '实测', '入手', '真香', '后悔', '开箱', '无广', '戴一周', '太绝了', '真实']):
        return '用户证言'
    if any(k in t for k in ['618', '国补', '史低', '价格', '性价比', '省钱', '补贴', '底价', '捡漏', '抄底', '好价']):
        return '价格促销'
    return '其他'

def num(x):
    try:
        return float(x) if pd.notna(x) else 0.0
    except Exception:
        return 0.0

# ── Jinka (72篇) ──
jdf = pd.read_excel('/Users/xiemila/Downloads/金咖618节点KOC促单汇总.xlsx', sheet_name='蒲公英源表', header=2)
j_notes = []
for _, r in jdf.iterrows():
    title = str(r.iloc[5]).strip() if pd.notna(r.iloc[5]) else ''
    if not title or title == 'nan':
        continue
    coop = str(r.iloc[13]) if pd.notna(r.iloc[13]) else ''
    product = 'S1' if 'S1' in coop else ('G1' if 'G1' in coop else '?')
    cost = num(r.iloc[16]) + num(r.iloc[17])
    j_notes.append({
        'title': title,
        'product': product,
        'cost': cost,
        'reads': num(r.iloc[21]),
        'interact': num(r.iloc[28]),
        'store': num(r.iloc[123]),
        'search': num(r.iloc[125]),
    })
J_TOTAL_GMV = 320082.29
J_TOTAL_STORE = 9383.0
for n in j_notes:
    n['direction'] = classify(n['title'])
    n['est_gmv'] = (n['store'] / J_TOTAL_STORE * J_TOTAL_GMV) if J_TOTAL_STORE > 0 else 0.0
    n['est_roi'] = n['est_gmv'] / n['cost'] if n['cost'] > 0 else 0.0

# ── Ruhan (80篇) ──
r_notes = json.load(open('outputs/ruhan_titles.json', encoding='utf-8'))
for n in r_notes:
    n['direction'] = classify(n['title'])
    n['cost'] = num(n.get('总消耗'))
    n['reads'] = num(n.get('阅读量'))
    n['interact'] = num(n.get('互动量'))
    n['store'] = num(n.get('进店uv'))
    n['search'] = num(n.get('搜索uv'))
    n['gmv'] = num(n.get('gmv'))
    n['roi'] = num(n.get('roi'))

# ── aggregate helpers ──
def agg(notes, value_keys, gmv_key, roi_key):
    groups = {d: {'count': 0, 'cost': 0.0, 'reads': 0.0, 'interact': 0.0, 'store': 0.0, 'search': 0.0, 'gmv': 0.0} for d in ALL_DIRS}
    for n in notes:
        g = groups[n['direction']]
        g['count'] += 1
        for k in ['cost', 'reads', 'interact', 'store', 'search']:
            g[k] += n[k]
        g['gmv'] += n.get(gmv_key, 0.0)
    for g in groups.values():
        g['roi'] = g['gmv'] / g['cost'] if g['cost'] > 0 else 0.0
        g['cpe'] = g['cost'] / g['interact'] if g['interact'] > 0 else 0.0
        g['cpm'] = g['cost'] / g['reads'] * 1000 if g['reads'] > 0 else 0.0
        g['store_rate'] = g['store'] / g['reads'] * 100 if g['reads'] > 0 else 0.0
        g['cost_per_store'] = g['cost'] / g['store'] if g['store'] > 0 else 0.0
        g['cost_per_search'] = g['cost'] / g['search'] if g['search'] > 0 else 0.0
    return groups

j_groups = agg(j_notes, None, 'est_gmv', 'est_roi')
r_groups = agg(r_notes, None, 'gmv', 'roi')

# ── sample titles per direction ──
def pick_samples(notes, direction, sort_key, k=3):
    arr = [n for n in notes if n['direction'] == direction]
    arr.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
    return [n['title'] for n in arr[:k]]

j_samples = {d: pick_samples(j_notes, d, 'store') for d in ALL_DIRS}
r_samples = {d: pick_samples(r_notes, d, 'gmv') for d in ALL_DIRS}

# fallback formula cards for empty directions
FORMULA = {
    '横测': '「3款热门AI眼镜横评｜普通人闭眼选不踩坑」',
    '纵测·千问S1 vs 千问G1': '「千问S1和G1怎么选？一篇看懂」',
    '纵测·千问S1 vs 夸克S1': '「千问S1 vs 夸克S1｜带屏AI眼镜深度对比」',
    '纵测·千问G1 vs 夸克G1': '「千问G1和夸克G1谁更值得入」',
    '用户证言': '「后悔没早入！千问G1实用性直接拉满」',
    '价格促销': '「618国补抄底｜千问AI眼镜底价入手攻略」',
    '其他': '「职场开挂神器｜千问AI眼镜S1」',
}

def format_num(x):
    if x is None: return '-'
    if x == 0: return '0'
    if isinstance(x, float):
        if x >= 10000:
            return f'{x/10000:.1f}万'
        if x >= 1000:
            return f'{x:,.0f}'
        return f'{x:.1f}' if x != int(x) else str(int(x))
    return str(x)

# ── HTML generation ──
DIRECTION_COLORS = {
    '横测': '#3b82f6',
    '纵测·千问S1 vs 千问G1': '#8b5cf6',
    '纵测·千问S1 vs 夸克S1': '#a855f7',
    '纵测·千问G1 vs 夸克G1': '#d946ef',
    '用户证言': '#10b981',
    '价格促销': '#f59e0b',
    '其他': '#64748b',
}

def build_module(title: str, subtitle: str, groups: dict, samples: dict, gmv_label: str, roi_label: str):
    cards = []
    for d in ALL_DIRS:
        g = groups[d]
        color = DIRECTION_COLORS[d]
        sample_list = samples[d]
        if not sample_list:
            sample_list = [FORMULA[d]]
        sample_html = ''.join(f'<div class="tda-sample-title">“{t}”</div>' for t in sample_list)
        cards.append(f'''
        <div class="tda-card" style="--tda-color:{color}">
          <div class="tda-card-head">
            <span class="tda-dot" style="background:{color}"></span>
            <span class="tda-card-name">{d}</span>
            <span class="tda-card-count">{g['count']} 篇</span>
          </div>
          <div class="tda-metric-row">
            <div><b>{format_num(g['roi'])}×</b><span>{roi_label}</span></div>
            <div><b>¥{format_num(g['cpe'])}</b><span>CPE</span></div>
            <div><b>{format_num(g['store_rate'])}%</b><span>阅读→进店</span></div>
            <div><b>¥{format_num(g['cost_per_store'])}</b><span>进店成本</span></div>
          </div>
          <div class="tda-sample">
            <div class="tda-sample-label">标准模块样例</div>
            {sample_html}
          </div>
        </div>''')

    table_rows = []
    for d in ALL_DIRS:
        g = groups[d]
        table_rows.append(f'''
        <tr>
          <td><span class="tda-dot-inline" style="background:{DIRECTION_COLORS[d]}"></span>{d}</td>
          <td>{g['count']}</td>
          <td>¥{format_num(g['cost'])}</td>
          <td>{format_num(g['reads'])}</td>
          <td>{format_num(g['interact'])}</td>
          <td>{format_num(g['store'])}</td>
          <td>{format_num(g['search'])}</td>
          <td>¥{format_num(g['gmv'])}</td>
          <td><b>{format_num(g['roi'])}×</b></td>
          <td>¥{format_num(g['cpe'])}</td>
          <td>{format_num(g['store_rate'])}%</td>
        </tr>''')

    return f'''
<!-- ═══════ 内容标题方向效率分析 ═══════ -->
<div class="section tda-section">
  <h2 class="section-title">{title}</h2>
  <p class="section-sub">{subtitle}</p>
  <div class="tda-grid">
    {''.join(cards)}
  </div>
  <div class="tda-table-wrap">
    <table class="tda-table">
      <thead>
        <tr>
          <th>方向</th><th>篇数</th><th>消耗</th><th>阅读</th><th>互动</th><th>进店</th><th>搜索</th><th>{gmv_label}</th><th>{roi_label}</th><th>CPE</th><th>进店率</th>
        </tr>
      </thead>
      <tbody>
        {''.join(table_rows)}
      </tbody>
    </table>
  </div>
</div>'''

jinka_module = build_module(
    '金咖 72 篇 · 内容标题方向效率分析',
    '按标题关键词拆为横测/纵测/用户证言/价格促销/其他；纵测定义为「同产品线同代际对决」；GMV/ROI 按进店 UV 占比估算',
    j_groups, j_samples, '估算GMV', '估算ROI'
)

ruhan_module = build_module(
    '如涵 80 篇 · 内容标题方向效率分析',
    '按标题关键词拆为横测/纵测/用户证言/价格促销/其他；纵测定义为「同产品线同代际对决」；GMV/ROI 为真实成交',
    r_groups, r_samples, '真实GMV', '真实ROI'
)

CSS = '''
/* ── title direction analysis ── */
.tda-section { margin-top: 28px; }
.tda-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; margin: 18px 0; }
.tda-card { background: rgba(15,23,42,0.72); border: 1px solid rgba(148,163,184,0.12); border-radius: 12px; padding: 16px; border-top: 3px solid var(--tda-color); }
.tda-card-head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.tda-dot { width: 10px; height: 10px; border-radius: 50%; }
.tda-card-name { font-weight: 700; color: #e2e8f0; flex: 1; font-size: 14px; }
.tda-card-count { font-size: 12px; color: #94a3b8; background: rgba(148,163,184,0.12); padding: 2px 8px; border-radius: 999px; }
.tda-metric-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 12px; }
.tda-metric-row div { text-align: center; background: rgba(255,255,255,0.04); border-radius: 8px; padding: 8px 4px; }
.tda-metric-row b { display: block; color: var(--tda-color); font-size: 16px; }
.tda-metric-row span { font-size: 11px; color: #94a3b8; }
.tda-sample { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 10px; }
.tda-sample-label { font-size: 11px; color: #94a3b8; margin-bottom: 6px; }
.tda-sample-title { font-size: 12px; color: #cbd5e1; line-height: 1.5; padding: 4px 0; border-bottom: 1px dashed rgba(148,163,184,0.15); }
.tda-sample-title:last-child { border-bottom: none; }
.tda-table-wrap { overflow-x: auto; margin-top: 16px; }
.tda-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.tda-table th, .tda-table td { padding: 10px 8px; text-align: right; border-bottom: 1px solid rgba(148,163,184,0.12); white-space: nowrap; }
.tda-table th { color: #94a3b8; font-weight: 600; background: rgba(255,255,255,0.04); }
.tda-table td:first-child { text-align: left; }
.tda-dot-inline { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
'''

# ── inject ──
for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')
    # avoid double injection
    if 'tda-section' in h:
        print(f'already injected: {tgt}')
        continue

    # insert CSS before last </style>
    if CSS not in h:
        h = h.replace('</style>', CSS + '</style>', 1)

    # insert jinka module before panel-promo footer
    jinka_anchor = '<footer>618促单 · 小红书图文专项数据分析'
    assert h.count(jinka_anchor) == 1, f'{tgt}: jinka anchor count != 1'
    h = h.replace(jinka_anchor, jinka_module + '\n  ' + jinka_anchor)

    # insert ruhan module before ruhan footer
    ruhan_anchor = '<footer>千问 AI 眼镜 · KOC 周报 W1 · 如涵国补方向独立分析 · 数据截止 2026-06-29</footer>'
    assert h.count(ruhan_anchor) == 1, f'{tgt}: ruhan anchor count != 1'
    h = h.replace(ruhan_anchor, ruhan_module + '\n  ' + ruhan_anchor)

    tgt.write_text(h, encoding='utf-8')
    print(f'✓ {tgt.relative_to(ROOT)}: injected')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')

# Save computed data for reference
summary = {'jinka': j_groups, 'ruhan': r_groups, 'jinka_samples': j_samples, 'ruhan_samples': r_samples}
open('outputs/title_direction_summary.json', 'w', encoding='utf-8').write(json.dumps(summary, ensure_ascii=False, indent=1))
print('✓ saved outputs/title_direction_summary.json')
