#!/usr/bin/env python3
"""
R45: 修复 panel-s1g1 桑基图/热力图空白。
根因：R44 重建 title_analysis 时丢失了 s1_element_stats / g1_element_stats，
buildLiftChart 报错导致后续 heatmap/sankey 初始化被中断。
修复：从上一版 commit 拷回元素统计数组，保留新标题列表。
"""
import re, json, shutil
from pathlib import Path
import subprocess

ROOT = Path('/Users/xiemila/.qoderwork/workspace/mq6ecbjzd6kpfcgy')
TARGETS = [
    ROOT / 'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    ROOT / 'outputs/KOC铺量内容.html',
]
DESKTOP = Path('/Users/xiemila/Desktop/KOC铺量内容.html')

# get previous title_analysis element stats
prev_html = subprocess.check_output(
    ['git', '-C', str(ROOT), 'show', 'b926ac7^:docs/weeks/W1-2026-05-13_to_06-13/index.html']
).decode('utf-8')
m = re.search(r'function init_s1g1\(\)\{try\{const DATA = ', prev_html)
start = prev_html.find('{', m.end())
depth = 1; j = start + 1
while j < len(prev_html) and depth > 0:
    if prev_html[j] == '{': depth += 1
    elif prev_html[j] == '}': depth -= 1
    j += 1
prev_data = json.loads(prev_html[start:j])
old_element_stats = {
    's1_element_stats': prev_data['title_analysis'].get('s1_element_stats', []),
    'g1_element_stats': prev_data['title_analysis'].get('g1_element_stats', []),
}

for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')
    pat = r'(function init_s1g1\(\)\{try\{const DATA = )(\{.*?\})(;\s*function switchTopTab)'
    def repl(m):
        d = json.loads(m.group(2))
        d['title_analysis'].update(old_element_stats)
        return m.group(1) + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + m.group(3)
    h2 = re.sub(pat, repl, h, count=1, flags=re.DOTALL)
    if h2 == h:
        print('WARN: no replacement in', tgt)
    else:
        h = h2
    tgt.write_text(h, encoding='utf-8')
    print('✓ patched', tgt.relative_to(ROOT))

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')
