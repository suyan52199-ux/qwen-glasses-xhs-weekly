# -*- coding: utf-8 -*-
"""
Apply 3 user feedbacks (round 28):
  ① Remove ruhan section + its style block from main index html (extract to standalone)
  ② Rename tab nav '618节点KOC促单' → '金咖618节点KOC促单'
  ③ Refresh CPM strip 如涵 data per new 6.29 xls:
     - 阅读量 68,893 → 71,700
     - 搜量UV成本 ¥71 (¥10万/1,402) → ¥56 (¥10万/1,782)
  ④ Fix chart width overflow (charts must stay within container)

Target files (dark + light):
  - docs/weeks/W1-2026-05-13_to_06-13/index.html
  - docs/weeks/W1-2026-05-13_to_06-13/index-light.html
  - outputs/KOC铺量内容.html
  - outputs/KOC铺量内容-白底版.html
"""
import re, shutil, os

TARGETS = [
    'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    'docs/weeks/W1-2026-05-13_to_06-13/index-light.html',
    'outputs/KOC铺量内容.html',
    'outputs/KOC铺量内容-白底版.html',
]

# Width-overflow fix CSS — appended at end of last <style> in each file
WIDTH_FIX_CSS = """
/* === Round-28: 防止图表 / 表格超出容器宽度 === */
.section, .panel, .container { box-sizing:border-box; }
.section, .panel-promo .section { overflow-x:hidden; max-width:100%; }
.section .chart-container, .panel-promo .chart-container,
.section .echart, .section [id^="chart-"], .section [id^="echart-"] {
  width:100% !important; max-width:100% !important; box-sizing:border-box;
}
.section table { table-layout:auto; max-width:100%; }
.section .tbl-wrap, .panel-promo .tbl-wrap { overflow-x:auto; max-width:100%; }
/* CPM strip / banners 不要超 */
.cpm-strip, .deposit-callout { max-width:100%; box-sizing:border-box; }
"""

for fp in TARGETS:
    if not os.path.exists(fp):
        print(f"⚠ skip (not found): {fp}")
        continue
    h = open(fp, encoding='utf-8').read()
    orig_size = len(h)
    is_light = 'light' in fp or '白底' in fp

    # ─── ① Remove ruhan section + its style block ───
    start_marker = '<!-- ═══════ 如涵 80 篇独立内容分析'
    start = h.find(start_marker)
    if start > 0:
        # Find the scoped style block that follows
        style_start = h.find('<style>\n.panel-promo .ruhan-section', start)
        if style_start > 0:
            style_end = h.find('</style>', style_start)
            if style_end > 0:
                block_end = style_end + len('</style>')
                h = h[:start] + h[block_end:]
                print(f"  ① removed ruhan block: {block_end-start:,}B")

    # ─── ② Rename tab nav ───
    h_before = h
    h = h.replace(
        '<span class="nm">618节点KOC促单</span>',
        '<span class="nm">金咖618节点KOC促单</span>'
    )
    if h != h_before:
        print("  ② tab name 618节点KOC促单 → 金咖618节点KOC促单")

    # ─── Also rename the panel header h1 if matches generic version ───
    h = re.sub(
        r'>618促单小红书图文专项数据分析<',
        r'>金咖 618 节点 KOC 促单 · 图文专项数据分析<',
        h
    )

    # ─── ③ Refresh CPM strip 如涵 numbers ───
    # 如涵 · CPM 卡 — 仅更新公式行 (¥1,631 保持)
    h_before = h
    h = h.replace(
        '¥10万 / 阅读量 68,893 × 1000 · 是金咖 2.5×',
        '¥10万 / 阅读量 71,700 × 1000 · 是金咖 2.5×'
    )
    # 如涵 · 搜量 UV 成本卡 — ¥71 → ¥56，公式更新
    h = re.sub(
        r'(<div style="color:#fca5a5;font-size:11px;">如涵 · 搜量 UV 成本</div>\s*<div style="[^"]*">)¥71</div>',
        r'\1¥56</div>',
        h
    )
    h = h.replace(
        '¥10万 / 搜索UV 1,402 · 是金咖 3.9×',
        '¥10万 / 搜索UV 1,782 · 是金咖 3.1× · 进店UV 4,260'
    )
    if h != h_before:
        print("  ③ CPM strip 如涵: 阅读量 68,893→71,700, ¥71→¥56, 搜索UV 1,402→1,782 + 进店UV 4,260")

    # ─── ④ Append width-fix CSS at last </style> ───
    if WIDTH_FIX_CSS.strip() not in h:
        last_style_close = h.rfind('</style>')
        if last_style_close > 0:
            h = h[:last_style_close] + WIDTH_FIX_CSS + h[last_style_close:]
            print(f"  ④ injected width-fix CSS @{last_style_close:,}")

    # Save
    delta = len(h) - orig_size
    open(fp, 'w', encoding='utf-8').write(h)
    print(f"  ✓ {fp}  ({orig_size:,} → {len(h):,}  Δ {delta:+,})")
    print()

# Sync desktop copies
for src, dst in [
    ('outputs/KOC铺量内容.html', '/Users/xiemila/Desktop/KOC铺量内容.html'),
    ('outputs/KOC铺量内容-白底版.html', '/Users/xiemila/Desktop/KOC铺量内容-白底版.html'),
    ('outputs/如涵国补方向数据分析.html', '/Users/xiemila/Desktop/如涵国补方向数据分析.html'),
]:
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"📋 desktop sync: {dst}")
