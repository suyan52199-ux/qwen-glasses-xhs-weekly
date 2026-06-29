# -*- coding: utf-8 -*-
"""
R30: 用新金咖文件 (/Users/xiemila/Downloads/金咖618节点KOC促单汇总.xlsx) 更新数据
仅 dark 主版：docs/.../index.html + outputs/KOC铺量内容.html + 桌面同步
不动 -light.html / 不动 outputs/如涵*.html / 不动 -白底版.html

数据更新（基于新表 每日消耗 sheet 累计末日值 + 蒲公英源表 全样本）：
- 累计阅读量：77,631 (unchanged，蒲公英)
- 累计互动量：3,646 (unchanged，蒲公英)
- 累计进店 UV：3,539 → 9,383（新 daily 累计末日 9,383）
- 累计搜索 UV：2,850 → 1,694（新 daily 累计末日 1,694）
- 累计 GMV：¥319,642 → ¥320,082.29
- ROI：6.40× → 6.40× (320,082/50,000)
- 搜量 UV 成本：¥18 → ¥30（50,000 / 1,694）
- 如涵相对金咖：3.1× → 1.9×（¥56 / ¥30）
"""
import re, shutil, os

TARGETS = [
    'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    'outputs/KOC铺量内容.html',
]

for fp in TARGETS:
    h = open(fp, encoding='utf-8').read()
    orig = len(h)
    panel_start = h.find('id="panel-promo"')
    panel_end = h.find('id="panel-ruhan"')

    # ─── ① metric-card 进店 UV 9,224 → 9,383 ───
    h = h.replace(
        '<div class="metric-card green"><div class="value">9,224</div>',
        '<div class="metric-card green"><div class="value">9,383</div>'
    )

    # ─── ② cpm-strip 金咖搜量UV成本 ¥18 → ¥30 + 公式更新 ───
    h = h.replace(
        '''<div style="font-size:22px;font-weight:900;color:#22c55e;line-height:1.1;margin:4px 0;">¥18</div>
      <div style="color:#94a3b8;font-size:11px;">¥5万 / 搜索进店UV 2,850</div>''',
        '''<div style="font-size:22px;font-weight:900;color:#22c55e;line-height:1.1;margin:4px 0;">¥30</div>
      <div style="color:#94a3b8;font-size:11px;">¥5万 / 搜索进店UV 1,694</div>'''
    )

    # ─── ③ 如涵相对金咖：3.1× → 1.9× ───
    h = h.replace(
        '¥10万 / 搜索UV 1,782 · 是金咖 3.1× · 进店UV 4,260',
        '¥10万 / 搜索UV 1,782 · 是金咖 1.9× · 进店UV 4,260'
    )

    # ─── ④ panel-promo DATA：surgical replace 指定值 (only the second const DATA = ...) ───
    # Locate "total_interact": 3646 anchor — the jinka DATA block lives ~332934
    seg_start = h.find('"total_interact": 3646')
    if seg_start > 0:
        # 范围替换 ±200B 内的 total_store/total_search/total_gmv
        seg_end = seg_start + 400
        seg = h[seg_start:seg_end]
        seg2 = seg
        seg2 = seg2.replace('"total_store": 3539', '"total_store": 9383')
        seg2 = seg2.replace('"total_search": 2850', '"total_search": 1694')
        seg2 = seg2.replace('"total_gmv": 319642.24', '"total_gmv": 320082.29')
        h = h[:seg_start] + seg2 + h[seg_end:]
        print(f"  ④ DATA jinka block updated @{seg_start:,}")

    # ─── ⑤ panel header subtitle ───
    h = h.replace(
        '总预算 ¥5万 · 星河 GMV ¥32万 · ROI 6.40×',
        '总预算 ¥5万 · 星河 GMV ¥32.0万 · ROI 6.40× · 数据截止 2026-06-27'
    )

    # ─── ⑥ Update source footer in panel-ruhan card 同步金咖对比文字 ───
    # 如涵 panel CPM 卡 (panel-ruhan) - "是金咖 ¥18 的 3.1×" → "¥30 的 1.9×"
    h = h.replace(
        '搜量UV成本 ¥56（金咖 ¥18 的 3.1×）',
        '搜量UV成本 ¥56（金咖 ¥30 的 1.9×）'
    )
    h = h.replace(
        '进店UV成本 ¥23（金咖 ¥18 的 1.3×）',
        '进店UV成本 ¥23（金咖 ¥5 的 4.6×）'  # 金咖 进店成本 = 50000/9383 ≈ ¥5.3
    )

    if len(h) != orig or True:
        open(fp, 'w', encoding='utf-8').write(h)
        delta = len(h) - orig
        print(f"  ✓ {fp}  {orig:,} → {len(h):,}  Δ {delta:+,}")

# Desktop sync (dark only)
shutil.copy('outputs/KOC铺量内容.html', '/Users/xiemila/Desktop/KOC铺量内容.html')
print('📋 desktop sync done (dark only)')
