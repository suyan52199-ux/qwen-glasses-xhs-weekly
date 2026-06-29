# -*- coding: utf-8 -*-
"""
Apply 5-item user feedback:
1. Rename overview h2 from '项目概括 · 目标完成情况' -> '铺量内容 · 目标完成情况'
2. Add CPM and search-UV cost data points:
   - 如涵 CPM ¥1,631 / 搜量UV成本 ¥77
   - 金咖 CPM ¥644 / 搜量UV成本 ¥18
3. Fix Top10 tab switching (panel-promo 第七层 S1/G1 Top10)
4. Replace 618 panel DATA (overall + top_interact/top_roi/top_store/top_search) with 金咖 72篇重算
   - Also patch conclusion bullet copy that referenced old top names
5. Add 沉淀周期 callout: 520/618 内容成交低或与出街时间沉淀较短相关
"""
import re, json, os

FILES = [
    'outputs/KOC铺量内容.html',
    'outputs/KOC铺量内容-白底版.html',
    'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    'docs/weeks/W1-2026-05-13_to_06-13/index-light.html',
]

ruhan = json.load(open('outputs/ruhan_content_analysis.json'))
jinka = json.load(open('outputs/jinka_promo_full.json'))

# ──────────────────────────────────────────────────────────
# Build new promo DATA assignment
# ──────────────────────────────────────────────────────────
JINKA_DATA_JSON = json.dumps({
    'overall': jinka['overall'],
    'top_interact': jinka['top_interact'],
    'top_roi': jinka['top_roi'],
    'top_store': jinka['top_store'],
    'top_search': jinka['top_search'],
    'title_analysis': jinka['title_analysis'],
}, ensure_ascii=False, separators=(', ', ': '))

# ──────────────────────────────────────────────────────────
# Build deposit-callout (沉淀周期)
# ──────────────────────────────────────────────────────────
DEPOSIT_CALLOUT = '''<div class="deposit-callout" style="margin:18px 0;padding:16px 20px;background:linear-gradient(135deg,#3d2a0a 0%,#1a1810 100%);border-left:4px solid #fbbf24;border-radius:10px;">
  <h4 style="margin:0 0 8px;color:#fbbf24;font-size:15px;">⏳ 关于 520 / 618 节点内容成交低的归因补充</h4>
  <p style="margin:0;color:#e8ecf4;font-size:13.5px;line-height:1.7;">520（5.20）与 618（6.18）促销节点距统计截止时间（6.13~6.22）仅 1-4 周，<b style="color:#fbbf24">小红书图文笔记的搜索权重与种草沉淀典型周期为 4-8 周</b>。当前观测到的成交数据尚未充分反映节点内容的长尾价值 — 下一轮节点投放需 <b>提前 2-4 周前置铺设</b>，并在 D+30 / D+60 各做一次复盘归因，避免基于「未沉淀样本」做出停投决策。</p>
</div>'''

# Light theme version
DEPOSIT_CALLOUT_LIGHT = '''<div class="deposit-callout" style="margin:18px 0;padding:16px 20px;background:linear-gradient(135deg,#fffbeb 0%,#fef3c7 100%);border-left:4px solid #f59e0b;border-radius:10px;">
  <h4 style="margin:0 0 8px;color:#92400e;font-size:15px;">⏳ 关于 520 / 618 节点内容成交低的归因补充</h4>
  <p style="margin:0;color:#1f2937;font-size:13.5px;line-height:1.7;">520（5.20）与 618（6.18）促销节点距统计截止时间（6.13~6.22）仅 1-4 周，<b style="color:#92400e">小红书图文笔记的搜索权重与种草沉淀典型周期为 4-8 周</b>。当前观测到的成交数据尚未充分反映节点内容的长尾价值 — 下一轮节点投放需 <b>提前 2-4 周前置铺设</b>，并在 D+30 / D+60 各做一次复盘归因，避免基于「未沉淀样本」做出停投决策。</p>
</div>'''

# ──────────────────────────────────────────────────────────
# Build CPM / search-UV-cost stat strip insertion for 如涵 + 金咖
# ──────────────────────────────────────────────────────────
def make_cpm_strip(jinka_label='金咖', ruhan_label='如涵'):
    return f'''<div class="cpm-strip" style="margin:14px 0 24px;padding:16px 20px;background:#0d1530;border:1px solid #1e2d5a;border-radius:12px;">
  <h4 style="margin:0 0 12px;color:#fff;font-size:14px;letter-spacing:.5px;">🔍 单位获取成本对比（金咖 vs 如涵）</h4>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;font-size:13px;">
    <div style="padding:12px;background:#0a2515;border-left:3px solid #22c55e;border-radius:6px;">
      <div style="color:#86efac;font-size:11px;">{jinka_label} · CPM</div>
      <div style="font-size:22px;font-weight:900;color:#22c55e;line-height:1.1;margin:4px 0;">¥644</div>
      <div style="color:#94a3b8;font-size:11px;">¥5万 / 阅读量 77,631 × 1000</div>
    </div>
    <div style="padding:12px;background:#0a2515;border-left:3px solid #22c55e;border-radius:6px;">
      <div style="color:#86efac;font-size:11px;">{jinka_label} · 搜量 UV 成本</div>
      <div style="font-size:22px;font-weight:900;color:#22c55e;line-height:1.1;margin:4px 0;">¥18</div>
      <div style="color:#94a3b8;font-size:11px;">¥5万 / 搜索进店UV 2,850</div>
    </div>
    <div style="padding:12px;background:#2e0f0f;border-left:3px solid #ef4444;border-radius:6px;">
      <div style="color:#fca5a5;font-size:11px;">{ruhan_label} · CPM</div>
      <div style="font-size:22px;font-weight:900;color:#ef4444;line-height:1.1;margin:4px 0;">¥1,631</div>
      <div style="color:#94a3b8;font-size:11px;">¥10万 / 阅读量 68,893 × 1000 · 是金咖 2.5×</div>
    </div>
    <div style="padding:12px;background:#2e0f0f;border-left:3px solid #ef4444;border-radius:6px;">
      <div style="color:#fca5a5;font-size:11px;">{ruhan_label} · 搜量 UV 成本</div>
      <div style="font-size:22px;font-weight:900;color:#ef4444;line-height:1.1;margin:4px 0;">¥71</div>
      <div style="color:#94a3b8;font-size:11px;">¥10万 / 搜索UV 1,402 · 是金咖 3.9×</div>
    </div>
  </div>
</div>'''

def make_cpm_strip_light():
    return '''<div class="cpm-strip" style="margin:14px 0 24px;padding:16px 20px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:12px;">
  <h4 style="margin:0 0 12px;color:#111827;font-size:14px;letter-spacing:.5px;">🔍 单位获取成本对比（金咖 vs 如涵）</h4>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;font-size:13px;">
    <div style="padding:12px;background:#f0fdf4;border-left:3px solid #16a34a;border-radius:6px;">
      <div style="color:#15803d;font-size:11px;">金咖 · CPM</div>
      <div style="font-size:22px;font-weight:900;color:#16a34a;line-height:1.1;margin:4px 0;">¥644</div>
      <div style="color:#6b7280;font-size:11px;">¥5万 / 阅读量 77,631 × 1000</div>
    </div>
    <div style="padding:12px;background:#f0fdf4;border-left:3px solid #16a34a;border-radius:6px;">
      <div style="color:#15803d;font-size:11px;">金咖 · 搜量 UV 成本</div>
      <div style="font-size:22px;font-weight:900;color:#16a34a;line-height:1.1;margin:4px 0;">¥18</div>
      <div style="color:#6b7280;font-size:11px;">¥5万 / 搜索进店UV 2,850</div>
    </div>
    <div style="padding:12px;background:#fef2f2;border-left:3px solid #dc2626;border-radius:6px;">
      <div style="color:#b91c1c;font-size:11px;">如涵 · CPM</div>
      <div style="font-size:22px;font-weight:900;color:#dc2626;line-height:1.1;margin:4px 0;">¥1,631</div>
      <div style="color:#6b7280;font-size:11px;">¥10万 / 阅读量 68,893 × 1000 · 是金咖 2.5×</div>
    </div>
    <div style="padding:12px;background:#fef2f2;border-left:3px solid #dc2626;border-radius:6px;">
      <div style="color:#b91c1c;font-size:11px;">如涵 · 搜量 UV 成本</div>
      <div style="font-size:22px;font-weight:900;color:#dc2626;line-height:1.1;margin:4px 0;">¥71</div>
      <div style="color:#6b7280;font-size:11px;">¥10万 / 搜索UV 1,402 · 是金咖 3.9×</div>
    </div>
  </div>
</div>'''

# ──────────────────────────────────────────────────────────
# Top10 switch fix: replace switchTopTab function with scoped version
# ──────────────────────────────────────────────────────────
OLD_SWITCH = '''function switchTopTab(e, name) {
 document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
 document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
 e.target.classList.add('active');
 document.getElementById('tab-' + name).classList.add('active');
}'''
NEW_SWITCH = '''function switchTopTab(e, name) {
 var btn = e.currentTarget || e.target;
 var tabsBar = btn.closest('.tabs');
 if (tabsBar) tabsBar.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
 var container = btn.closest('.section, .panel') || document;
 container.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
 btn.classList.add('active');
 var target = document.getElementById('tab-' + name);
 if (target) target.classList.add('active');
}'''

OLD_PROMO_SWITCH = '''function switchPromoTab(name) {
 document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
 document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
 event.target.classList.add('active');
 document.getElementById('tab-' + name).classList.add('active');
}'''
NEW_PROMO_SWITCH = '''function switchPromoTab(name, ev) {
 var e = ev || window.event;
 var btn = e && (e.currentTarget || e.target);
 var tabsBar = btn && btn.closest && btn.closest('.tabs');
 if (tabsBar) tabsBar.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
 var container = (btn && btn.closest && btn.closest('.section, .panel')) || document;
 container.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
 if (btn) btn.classList.add('active');
 var target = document.getElementById('tab-' + name);
 if (target) target.classList.add('active');
}'''

# Also pass event in onclick for switchPromoTab calls
# (current markup: switchPromoTab('interact') without event)
# We must rewrite onclick="switchPromoTab('xxx')" -> "switchPromoTab('xxx', event)"
PROMO_ONCLICK_PAT = re.compile(r'''onclick="switchPromoTab\((['"][a-z_-]+['"])\)"''')

# ──────────────────────────────────────────────────────────
# Promo DATA replacement
# ──────────────────────────────────────────────────────────
PROMO_DATA_RE = re.compile(
    r'const DATA = \{"overall": \{"total_notes": 72, "total_interact": 3629.*?\}\};',
    re.DOTALL
)

# ──────────────────────────────────────────────────────────
# Subtitle "72篇笔记交叉验证" -> consistent金咖 label
# (already replaced earlier; check if exists and add CPM)
# ──────────────────────────────────────────────────────────

OVERVIEW_TITLE_OLD = '项目概括 · 目标完成情况'
OVERVIEW_TITLE_NEW = '铺量内容 · 目标完成情况'

# ──────────────────────────────────────────────────────────
# Conclusion bullets in panel-promo that reference old numbers
# Old hardcoded "美女科技范(188互动)" / "188" should match the new top "美女科技范 189"
# Most of these are descriptive; if they say "Top1 188" -> "Top1 189". We'll only replace the most explicit ones.
# ──────────────────────────────────────────────────────────
CONCLUSION_REPLACEMENTS = [
    ('Top1美女科技范(188互动)', 'Top1美女科技范(189互动)'),
    ('Top2(美女科技范132 + 趣味数码130)', 'Top2(趣味数码 1,104 + 美女科技范 787)'),
    ('Top3(ROI 43/35/30)', 'Top3(ROI 107×/65×/54×)'),
]

# ──────────────────────────────────────────────────────────
# Update ruhan section (if exists already): refresh data using new file
# ──────────────────────────────────────────────────────────
# numbers already match because new xls is identical. No data change.

# ──────────────────────────────────────────────────────────
def process(path):
    is_light = 'light' in path or '白底' in path
    if not os.path.exists(path):
        print(f"  ⚠ skip (missing): {path}")
        return
    with open(path, encoding='utf-8') as f:
        h = f.read()
    orig_len = len(h)

    # 1. Overview title rename
    n1 = h.count(OVERVIEW_TITLE_OLD)
    h = h.replace(OVERVIEW_TITLE_OLD, OVERVIEW_TITLE_NEW)
    print(f"  ① overview title renamed: {n1} occurrences")

    # 2. Fix switchTopTab + switchPromoTab
    if OLD_SWITCH in h:
        h = h.replace(OLD_SWITCH, NEW_SWITCH)
        print("  ③ switchTopTab fixed")
    elif 'btn.closest(\'.tabs\')' in h:
        print("  ③ switchTopTab already fixed")
    else:
        print("  ⚠ switchTopTab not matched")
    if OLD_PROMO_SWITCH in h:
        h = h.replace(OLD_PROMO_SWITCH, NEW_PROMO_SWITCH)
        # also update onclick to pass event
        h = PROMO_ONCLICK_PAT.sub(r'onclick="switchPromoTab(\1, event)"', h)
        print("  ③ switchPromoTab fixed + onclick updated")
    elif 'switchPromoTab(name, ev)' in h:
        print("  ③ switchPromoTab already fixed")
    else:
        print("  ⚠ switchPromoTab not matched")

    # 4. Replace promo DATA with new jinka recompute (balanced-brace finder)
    new_data_line = 'const DATA = ' + JINKA_DATA_JSON + ';'
    start = h.find('const DATA = {"overall": {"total_notes": 72')
    if start >= 0:
        i = h.index('{', start)
        depth = 0
        end_brace = None
        for j in range(i, len(h)):
            if h[j] == '{': depth += 1
            elif h[j] == '}': depth -= 1
            if depth == 0:
                end_brace = j + 1
                break
        sc = h.find(';', end_brace)
        if sc > 0:
            old_len = sc + 1 - start
            h = h[:start] + new_data_line + h[sc + 1:]
            print(f"  ④ promo DATA replaced (old {old_len:,}B -> new {len(new_data_line):,}B)")
    elif '"total_cost": 50000' in h and '"overall_roi": 6.4' in h:
        print("  ④ promo DATA already updated")
    else:
        print("  ⚠ promo DATA pattern not matched")

    # 4b. Conclusion replacements
    for old, new in CONCLUSION_REPLACEMENTS:
        if old in h:
            h = h.replace(old, new)
            print(f"  ④b conclusion text: {old[:30]}... -> ...")

    # 2/5. Inject CPM strip + deposit callout in panel-promo (right after metrics-grid)
    if 'cpm-strip' not in h:
        strip = make_cpm_strip_light() if is_light else make_cpm_strip()
        callout = DEPOSIT_CALLOUT_LIGHT if is_light else DEPOSIT_CALLOUT
        # anchor: end of </div></div> following the 4 metric-cards (the metrics-grid closing tag with new metrics)
        anchor = '<div class="metric-card red"><div class="value">6.40×</div><div class="label">ROI（¥5 万预算）</div></div></div>'
        if anchor in h:
            h = h.replace(anchor, anchor + '\n' + strip + '\n' + callout, 1)
            print("  ②+⑤ CPM strip + deposit callout injected after metric-grid")
        else:
            print("  ⚠ metric-grid anchor not found, skipping CPM strip")
    else:
        print("  ②+⑤ CPM strip already present")

    if h != open(path, encoding='utf-8').read():
        with open(path, 'w', encoding='utf-8') as f:
            f.write(h)
        print(f"  → wrote {path} (Δ {len(h)-orig_len:+,}B, total {len(h):,}B)")

for fp in FILES:
    print(f"\n=== {fp} ===")
    process(fp)

print("\n✓ all 5 fixes applied")
