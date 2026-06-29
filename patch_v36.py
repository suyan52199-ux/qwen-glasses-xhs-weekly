#!/usr/bin/env python3
"""
R36 微调：R34 金咖/如涵「内容标题方向效率分析」中，纵测方向若篇数为 0，
则不展示卡片和对应表格行。
TARGETS（硬规则）：docs dark + outputs/KOC铺量内容.html + 桌面同步
"""
import re, shutil
from pathlib import Path

ROOT = Path('/Users/xiemila/.qoderwork/workspace/mq6ecbjzd6kpfcgy')
TARGETS = [
    ROOT / 'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    ROOT / 'outputs/KOC铺量内容.html',
]
DESKTOP = Path('/Users/xiemila/Desktop/KOC铺量内容.html')

def remove_balanced_tag_blocks(html: str, start_tag: str, end_tag: str, predicate):
    """Remove every balanced block that starts with start_tag and ends with end_tag
    if predicate(block_text) returns True. Tags are assumed not to overlap."""
    out = []
    i = 0
    while i < len(html):
        idx = html.find(start_tag, i)
        if idx == -1:
            out.append(html[i:])
            break
        # find end of start_tag
        tag_end = idx + len(start_tag)
        # balance generic <...> vs </...>
        depth = 1
        j = tag_end
        while j < len(html) and depth > 0:
            # look for next tag start
            lt = html.find('<', j)
            if lt == -1:
                break
            # find tag end
            gt = html.find('>', lt)
            if gt == -1:
                break
            tag_content = html[lt+1:gt].strip()
            if tag_content.startswith('/'):
                close_name = tag_content[1:].split()[0]
                open_name = start_tag.split()[0][1:]
                # our start_tag may be '<div class="tda-card"' so open_name = 'div'
                if close_name == open_name:
                    depth -= 1
                    if depth == 0:
                        block_end = gt + 1
                        block = html[idx:block_end]
                        if predicate(block):
                            # skip this block; continue after it
                            i = block_end
                            # strip leading newline/spaces? keep as is
                            break
                        else:
                            out.append(html[i:block_end])
                            i = block_end
                            break
            else:
                open_name = tag_content.split()[0]
                if open_name == start_tag.split()[0][1:]:
                    depth += 1
            j = gt + 1
        else:
            # did not close, append rest
            out.append(html[i:])
            break
    return ''.join(out)

def remove_zero_zongce_cards(html: str) -> str:
    def is_zero_zongce(block: str) -> bool:
        return '<span class="tda-card-name">纵测' in block and '<span class="tda-card-count">0 篇</span>' in block
    return remove_balanced_tag_blocks(html, '<div class="tda-card"', '</div>', is_zero_zongce)

def remove_zero_zongce_table_rows(html: str) -> str:
    # table rows: <tr> ... </tr>
    def is_zero_zongce_row(block: str) -> bool:
        # block contains 纵测 in first td and a count cell 0
        return '<td><span class="tda-dot-inline"' in block and '纵测' in block and '>0</td>' in block
    return remove_balanced_tag_blocks(html, '<tr>', '</tr>', is_zero_zongce_row)

def update_subheading(html: str) -> str:
    # Replace the phrase mentioning 横测/纵测/... with "横测/用户证言/价格促销/其他（纵测方向本次样本为 0，未展示）"
    old = '按标题关键词拆为横测/纵测/用户证言/价格促销/其他'
    new = '按标题关键词拆为横测/用户证言/价格促销/其他（纵测方向本次样本为 0，已隐藏）'
    return html.replace(old, new)

for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')
    h = remove_zero_zongce_cards(h)
    h = remove_zero_zongce_table_rows(h)
    h = update_subheading(h)
    tgt.write_text(h, encoding='utf-8')
    print(f'✓ patched {tgt.relative_to(ROOT)}')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')
