#!/usr/bin/env python3
"""
R31 fix: restore init_promo local DATA's 8 missing chart fields by recycling
73e31a3's version, then patch `overall` scalars to 6.29 values, and inject a
"数据更新时间 2026-06-29" label above the promo panel.

Hard rule: TARGETS = ONLY
  - docs/weeks/W1-2026-05-13_to_06-13/index.html (dark, online)
  - outputs/KOC铺量内容.html (desktop sync source)
"""
import re, json, subprocess, shutil
from pathlib import Path

ROOT = Path('/Users/xiemila/.qoderwork/workspace/mq6ecbjzd6kpfcgy')
TARGETS = [
    ROOT / 'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    ROOT / 'outputs/KOC铺量内容.html',
]
DESKTOP = Path('/Users/xiemila/Desktop/KOC铺量内容.html')

# 1) Get the 73e31a3 local DATA (14 keys) — reuse historical chart data
old_html = subprocess.check_output(
    ['git', '-C', str(ROOT), 'show', '73e31a3:docs/weeks/W1-2026-05-13_to_06-13/index.html']
).decode('utf-8', 'ignore')
m = re.search(r'function\s+init_promo\s*\(', old_html)
i = old_html.index('const DATA = {', m.end())
j = i
while old_html[j] != '{':
    j += 1
start, depth, j = j, 1, j + 1
while j < len(old_html) and depth > 0:
    if old_html[j] == '{': depth += 1
    elif old_html[j] == '}': depth -= 1
    j += 1
recycled = json.loads(old_html[start:j])

# 2) Patch `overall` block to the 6.29 jinka-xlsx numbers
recycled['overall'] = {
    'total_notes': 72,
    'total_interact': 3646,
    'total_store': 9383,
    'total_search': 1694,
    'total_gmv': 320082.29,
    'total_cost': 50000,
    'overall_roi': 6.40,
    'cpm': 644,
    'cost_per_search_uv': 30,
    'data_updated_at': '2026-06-29',
    'data_source': '金咖618节点KOC促单汇总.xlsx',
}
new_local_data = json.dumps(recycled, ensure_ascii=False, separators=(',', ':'))

# 3) For each target, replace the local DATA inside init_promo
def find_local_data_span(html: str):
    m = re.search(r'function\s+init_promo\s*\(', html)
    if not m: raise RuntimeError('init_promo not found')
    i = html.index('const DATA = {', m.end())
    j = i
    while html[j] != '{': j += 1
    start, depth, j = j, 1, j + 1
    while j < len(html) and depth > 0:
        if html[j] == '{': depth += 1
        elif html[j] == '}': depth -= 1
        j += 1
    return start, j  # j is one past final }

UPDATE_BANNER = (
    '<div class="promo-data-stamp" style="background:linear-gradient(90deg,'
    'rgba(34,211,238,.10),rgba(168,85,247,.06));border:1px solid '
    'rgba(34,211,238,.25);border-radius:8px;padding:10px 14px;margin:0 0 14px;'
    'font-size:12px;color:#94a3b8;display:flex;gap:14px;flex-wrap:wrap;align-items:center;">'
    '<span style="color:#22d3ee;font-weight:600;">📅 数据更新时间 2026-06-29</span>'
    '<span>· 数据源：金咖618节点KOC促单汇总.xlsx（蒲公英源表 72 篇 + 淘宝星河 30 天归因）</span>'
    '<span style="color:#fbbf24;">· 图表数据沿用历史口径，KPI 标量已按 6.29 新表更新</span>'
    '</div>'
)

for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')
    s, e = find_local_data_span(h)
    before, after = h[:s], h[e:]
    h2 = before + new_local_data + after

    # Insert the data-update banner once at the top of panel-promo (after its opening div)
    if 'promo-data-stamp' not in h2:
        # find the panel-promo container opening
        anchor = re.search(r'<div\s+id="panel-promo"[^>]*>', h2)
        if anchor:
            ins = anchor.end()
            h2 = h2[:ins] + UPDATE_BANNER + h2[ins:]
        else:
            # fallback: insert before the first 标题吸引度分析 comment
            mark = '<!-- ═══════ 标题吸引度分析'
            idx = h2.find(mark)
            if idx > 0:
                h2 = h2[:idx] + UPDATE_BANNER + h2[idx:]

    tgt.write_text(h2, encoding='utf-8')
    print(f'✓ {tgt.relative_to(ROOT)}: {len(h)} → {len(h2)} ({len(h2)-len(h):+d}B)')

# 4) Sync to desktop
shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')
