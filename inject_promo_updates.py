# -*- coding: utf-8 -*-
"""Update KOC HTML 4 files."""
import re, json, os

FILES = [
    'outputs/KOC铺量内容.html',
    'outputs/KOC铺量内容-白底版.html',
    'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    'docs/weeks/W1-2026-05-13_to_06-13/index-light.html',
]

d = json.load(open('outputs/ruhan_content_analysis.json'))
T = d['total']; S1 = d['S1']; G1 = d['G1']
acc_rows = d['account_types']
top_gmv = d['top_gmv']
fans = d['fans_buckets']
zero_by_type = d['zero_by_type']

# Build account type rows
acc_html = ''
for a in acc_rows:
    tier = 'high' if a['roi']>=3 else ('mid' if a['roi']>=2 else 'low')
    acc_html += f"""<tr class="ruhan-row-{tier}"><td><b>{a['账号类型']}</b></td><td>{a['notes']}</td><td>¥{a['spend']:,.0f}</td><td>¥{a['gmv']:,.0f}</td><td><b>{a['roi']}×</b></td><td>¥{a['gmv_per_note']:,.0f}</td><td>{a['hit_rate']}%</td></tr>"""

# Top GMV table
top_html = ''
for i, t in enumerate(top_gmv, 1):
    medal = '🥇' if i==1 else ('🥈' if i==2 else ('🥉' if i==3 else f'#{i}'))
    top_html += f"""<tr><td>{medal}</td><td><b>{t['nick']}</b></td><td>{t['actype']}</td><td>{t['product']}</td><td>{t['fans']:,}</td><td>¥{t['spend']:,}</td><td><b style="color:#22c55e">¥{t['gmv']:,}</b></td><td><b>{t['roi']}×</b></td><td>{t['visit']} / {t['search']}</td></tr>"""

# Fans bucket bars
fans_order = ['<2K','2-5K','5-10K','10-20K','>=20K']
fans_sorted = sorted(fans, key=lambda x: fans_order.index(x['fb']))
fans_max_roi = max(f['roi'] for f in fans_sorted) or 1
fans_html = ''
for f in fans_sorted:
    w = (f['roi']/fans_max_roi)*100
    color = '#22c55e' if f['roi']>=3 else ('#fbbf24' if f['roi']>=2 else '#ef4444')
    fans_html += f"""<div class="ruhan-fbar"><div class="ruhan-fbar-lbl"><b>{f['fb']}</b> 粉丝</div><div class="ruhan-fbar-track"><div class="ruhan-fbar-fill" style="width:{w}%;background:{color}"><span>ROI {f['roi']}×</span></div></div><div class="ruhan-fbar-meta">{f['n']} 篇 · 命中 {f['hit_rate']}% · ¥{int(f['gmv']):,}</div></div>"""

# Zero spend by type
zero_html = ''
zero_sorted = sorted(zero_by_type.items(), key=lambda x: -x[1]['spend'])
for k, v in zero_sorted:
    zero_html += f"""<tr><td><b>{k}</b></td><td>{v['n']}</td><td>¥{v['spend']:,}</td></tr>"""

total_zero_pct = round(d['total']['zero']/d['total']['notes']*100)
top_gmv_sum = sum(t['gmv'] for t in top_gmv)
avg_price = round(T['spend']/T['notes'])

# Build the section body — only f-string of small templates, then concatenate
parts = []
parts.append('<!-- ═══════ 如涵 80 篇独立内容分析（NEW） ═══════ -->\n')
parts.append('<div class="section ruhan-section">')
parts.append('<h2 class="section-title" style="border-left-color:#f59e0b">如涵供应商 · 80 篇内容独立分析 <span class="ribbon-new">NEW</span></h2>')
parts.append('<p class="section-sub">数据来源：<code style="background:#1a1f3d;color:#fbbf24;padding:2px 6px;border-radius:3px;">如涵618促销KOC图文数据汇总(1).xls</code> · S1×71 + G1×9 · 总预算 ¥10 万 · 数据截止 6.22</p>')

# 4 banner
parts.append('<div class="ruhan-banner">')
parts.append(f'<div class="ruhan-b"><span class="ruhan-bv" style="color:#22c55e">¥{T["gmv"]/10000:.1f}万</span><span class="ruhan-bl">星河 GMV</span></div>')
parts.append(f'<div class="ruhan-b"><span class="ruhan-bv" style="color:#fbbf24">{T["roi_budget"]}×</span><span class="ruhan-bl">ROI（¥10万预算口径）</span></div>')
parts.append(f'<div class="ruhan-b"><span class="ruhan-bv" style="color:#ef4444">{T["zero"]}</span><span class="ruhan-bl">零成交篇数 / 共 80</span></div>')
parts.append(f'<div class="ruhan-b"><span class="ruhan-bv" style="color:#60a5fa">¥{T["gmv_per_note"]:,}</span><span class="ruhan-bl">篇均 GMV</span></div>')
parts.append('</div>')

# S1 vs G1 dual cards
parts.append('<div class="ruhan-prodvs">')
parts.append(f'<div class="ruhan-pcard ruhan-pc-s1"><div class="ruhan-pc-head"><b>S1 方向 · 71 篇</b><span class="ruhan-pc-tag">主力 89%</span></div><div class="ruhan-pc-roi">{S1["roi"]}<span class="x">×</span><span class="vs">ROI 实算</span></div>')
parts.append(f'<div class="ruhan-pc-stats"><div><span class="v">¥{S1["spend"]/10000:.1f}万</span><span class="l">总消耗</span></div><div><span class="v">¥{S1["gmv"]/10000:.1f}万</span><span class="l">总GMV</span></div><div><span class="v">{S1["visit"]:,}</span><span class="l">进店UV</span></div><div><span class="v">{S1["search"]:,}</span><span class="l">搜索UV</span></div><div><span class="v">{S1["cengjiao"]}/71</span><span class="l">成交篇数</span></div><div><span class="v">¥{S1["gmv_per_note"]:,}</span><span class="l">篇均GMV</span></div></div>')
parts.append(f'<div class="ruhan-pc-note">⚠️ 同方向主力 KOC ROI 16.01× · 如涵 S1 仅 {S1["roi"]}× — <b>效率仅主力 1/5.7</b></div></div>')

parts.append(f'<div class="ruhan-pcard ruhan-pc-g1"><div class="ruhan-pc-head"><b>G1 方向 · 9 篇</b><span class="ruhan-pc-tag" style="background:#a78bfa">补充 11%</span></div><div class="ruhan-pc-roi" style="color:#a78bfa">{G1["roi"]}<span class="x">×</span><span class="vs">ROI 实算</span></div>')
parts.append(f'<div class="ruhan-pc-stats"><div><span class="v">¥{G1["spend"]/10000:.1f}万</span><span class="l">总消耗</span></div><div><span class="v">¥{G1["gmv"]/10000:.1f}万</span><span class="l">总GMV</span></div><div><span class="v">{G1["visit"]:,}</span><span class="l">进店UV</span></div><div><span class="v">{G1["search"]:,}</span><span class="l">搜索UV</span></div><div><span class="v">{G1["cengjiao"]}/9</span><span class="l">成交篇数</span></div><div><span class="v">¥{G1["gmv_per_note"]:,}</span><span class="l">篇均GMV</span></div></div>')
parts.append(f'<div class="ruhan-pc-note">⚠️ 同方向主力 KOC ROI 12.07× · 如涵 G1 仅 {G1["roi"]}× — <b>效率仅主力 1/7</b></div></div>')
parts.append('</div>')

# Account type table
parts.append('<h3 style="color:#fff;font-size:18px;margin:32px 0 12px;padding:0;">① 账号类型效率对比（5 类）</h3>')
parts.append('<p class="section-sub" style="margin-bottom:14px;">如涵 80 篇账号类型分布与原 KOC 9 类不同 — <b style="color:#fbbf24">缺乏数码科技测评（原主力 ROI 14.9×）</b>，全部偏生活/好物/大字报 3 类</p>')
parts.append('<div class="ruhan-tbl-wrap"><table class="ruhan-tbl"><thead><tr><th>账号类型</th><th>篇数</th><th>总消耗</th><th>总 GMV</th><th>ROI</th><th>篇均 GMV</th><th>成交命中率</th></tr></thead><tbody>')
parts.append(acc_html)
parts.append('</tbody></table></div>')

# Fans buckets
parts.append('<h3 style="color:#fff;font-size:18px;margin:28px 0 12px;padding:0;">② 粉丝量段 × ROI <span style="color:#fbbf24">— 反相关现象</span></h3>')
parts.append('<p class="section-sub" style="margin-bottom:14px;"><b style="color:#22c55e">&lt; 2K 微粉</b> 21 篇 ROI <b>4.43×</b> 反而是 ROI 最高段 — 越垂直的小博主带货效率越好；<b>10-20K 中腰部</b>预算占比 50% 但 ROI 仅 2.46×</p>')
parts.append('<div class="ruhan-fans">')
parts.append(fans_html)
parts.append('</div>')

# Top10
parts.append('<h3 style="color:#fff;font-size:18px;margin:28px 0 12px;padding:0;">③ 成交 Top 10 真实笔记</h3>')
parts.append(f'<p class="section-sub" style="margin-bottom:14px;">33 篇有成交 · Top10 贡献 ¥{top_gmv_sum/10000:.1f}万 GMV（占总 GMV 的 {round(top_gmv_sum/T["gmv"]*100)}%）· <b style="color:#fbbf24">9/10 是 S1 方向</b></p>')
parts.append('<div class="ruhan-tbl-wrap"><table class="ruhan-tbl"><thead><tr><th>排名</th><th>达人</th><th>类型</th><th>产品</th><th>粉丝</th><th>消耗</th><th>GMV</th><th>ROI</th><th>进店/搜索 UV</th></tr></thead><tbody>')
parts.append(top_html)
parts.append('</tbody></table></div>')

# Zero
parts.append(f'<h3 style="color:#fff;font-size:18px;margin:28px 0 12px;padding:0;">④ 零成交 47 篇 · ¥{d["zero_total_spend"]/10000:.1f}万预算（{total_zero_pct}% 篇数 / {round(d["zero_total_spend"]/T["spend"]*100)}% 预算）</h3>')
parts.append('<p class="section-sub" style="margin-bottom:14px;">47 篇零成交集中在 <b style="color:#ef4444">好物分享 17 篇 + 生活记录 17 篇</b> — 即使做了内容铺量也未能产生订单，结合上面 Top10 看 — 同样是「好物分享/生活记录/大字报」3 类，差距在<b style="color:#fbbf24">选品力 + 钩子文案 + 挂车位置</b></p>')
parts.append('<div class="ruhan-zero-wrap"><table class="ruhan-tbl" style="max-width:520px"><thead><tr><th>账号类型</th><th>零成交篇数</th><th>沉没预算</th></tr></thead><tbody>')
parts.append(zero_html)
parts.append('</tbody></table></div>')

# Findings
parts.append('<div class="ruhan-finding"><h3 style="margin-top:0;color:#fbbf24;font-size:20px;padding:0;border:none;">📋 如涵 80 篇 · 4 条核心规律</h3><ol>')
parts.append('<li><b>S1 是基本盘但效率仅主力 1/6</b>：71/80 篇都做 S1（占 89%），但 ROI 仅 2.81× 是原 KOC S1 ROI 8.53× 的 1/3 — 不是「产品方向选错」，是<b>「同方向内容质量塌方」</b></li>')
parts.append('<li><b>账号类型结构失衡</b>：3 类账号（生活记录+好物分享+大字报）= 95% 笔记 — 完全没有<b style="color:#22c55e">数码科技测评</b>（原 KOC 主力 166 篇 ROI 14.9×）这种高效账号 — 下一轮必须强制混入数码测评类</li>')
parts.append('<li><b>微粉 ROI &gt; 中腰部 ROI</b>：&lt;2K 粉 21 篇 ROI 4.43× &gt;&gt; 10-20K 粉 32 篇 ROI 2.46× — 如涵给的中腰部包没有跑赢小红书自然铺量逻辑，建议下一轮要求按 70% 微粉 + 30% 1-2 万粉的结构投放</li>')
parts.append('<li><b>零成交 47 篇 ¥3.7 万沉没</b>：占预算 34% 但零产出 — 比对 Top10 大字报/好物分享类成交大的样本（如 饱饱吃不饱 ROI 23.7× / 馋嘴小牛 21×），需要做「内容样本要素拆解」喂给如涵下一轮选号</li>')
parts.append('</ol></div>')

# Action
parts.append('<div class="ruhan-action"><h3 style="margin-top:0;color:#22c55e;font-size:18px;padding:0;border:none;">🎯 如涵下一轮分流建议</h3>')
parts.append('<ul style="margin:0;padding-left:20px;line-height:1.9;color:#cbd5e0">')
parts.append(f'<li><b>方向限定</b>：暂停 G1（9 篇 ROI 1.72×），全量投 S1 但单价从 ¥{avg_price:,} 砍到 ¥800 以下控量到 60 篇</li>')
parts.append('<li><b>结构调整</b>：要求 30 篇 = <span style="color:#22c55e">数码科技测评类（必须）</span> + 20 篇 = 大字报短决策类 + 10 篇 = 微粉好物分享</li>')
parts.append('<li><b>选号机制</b>：把 Top10 笔记给如涵作为「标杆样本」，选号 ROI 复投率 ≥ 30% 才算达标</li>')
parts.append('<li><b>挂车诊断</b>：47 篇零成交全部跑「挂车 SKU 配对 + 落地承接」分析，找出选品/页面问题</li>')
parts.append('</ul></div>')

parts.append('</div>')

RUHAN_STYLE = """
<style>
.panel-promo .ruhan-section .section-title { color:#fbbf24; }
.panel-promo .ruhan-banner { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:18px 0 24px; }
.panel-promo .ruhan-b { background:linear-gradient(135deg,#1f2937 0%,#0f172a 100%); border:1px solid #334155; border-radius:12px; padding:18px 20px; text-align:center; }
.panel-promo .ruhan-bv { display:block; font-size:32px; font-weight:900; line-height:1.1; }
.panel-promo .ruhan-bl { display:block; margin-top:6px; font-size:12px; color:#94a3b8; }
.panel-promo .ruhan-prodvs { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin:18px 0; }
.panel-promo .ruhan-pcard { background:linear-gradient(135deg,#0f1b3d 0%,#1a2540 100%); border-radius:14px; padding:20px 22px; border:1.5px solid #1e3a8a; }
.panel-promo .ruhan-pc-g1 { border-color:#7c3aed; background:linear-gradient(135deg,#1a1432 0%,#2a1e4d 100%); }
.panel-promo .ruhan-pc-head { display:flex; justify-content:space-between; align-items:center; font-size:16px; color:#fff; margin-bottom:8px; }
.panel-promo .ruhan-pc-tag { font-size:11px; background:#3b82f6; color:#fff; padding:2px 10px; border-radius:10px; font-weight:600; }
.panel-promo .ruhan-pc-roi { font-size:50px; font-weight:900; color:#60a5fa; line-height:1; margin:8px 0 4px; }
.panel-promo .ruhan-pc-roi .x { font-size:22px; margin-left:4px; }
.panel-promo .ruhan-pc-roi .vs { display:block; font-size:11px; color:#94a3b8; font-weight:500; letter-spacing:1.5px; margin-top:4px; }
.panel-promo .ruhan-pc-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:14px; }
.panel-promo .ruhan-pc-stats > div { background:#00000044; border-radius:8px; padding:8px 10px; }
.panel-promo .ruhan-pc-stats .v { font-size:15px; font-weight:700; color:#fff; display:block; line-height:1.2; }
.panel-promo .ruhan-pc-stats .l { font-size:11px; color:#94a3b8; margin-top:2px; }
.panel-promo .ruhan-pc-note { margin-top:12px; padding:10px 12px; background:#7f1d1d44; border-left:3px solid #ef4444; border-radius:6px; font-size:12.5px; color:#fca5a5; }
.panel-promo .ruhan-pc-g1 .ruhan-pc-note { background:#581c8744; border-left-color:#a78bfa; color:#c4b5fd; }
.panel-promo .ruhan-tbl-wrap { overflow-x:auto; margin:8px 0; }
.panel-promo .ruhan-tbl { width:100%; border-collapse:collapse; font-size:13px; }
.panel-promo .ruhan-tbl thead { background:#1e293b; }
.panel-promo .ruhan-tbl th { padding:10px 12px; text-align:left; color:#fbbf24; font-weight:700; font-size:12px; border-bottom:2px solid #334155; }
.panel-promo .ruhan-tbl td { padding:10px 12px; color:#e8ecf4; border-bottom:1px solid #1e293b; }
.panel-promo .ruhan-tbl tr.ruhan-row-high td { background:#0a2515; }
.panel-promo .ruhan-tbl tr.ruhan-row-mid td { background:#1e1810; }
.panel-promo .ruhan-tbl tr.ruhan-row-low td { background:#2e0f0f; }
.panel-promo .ruhan-fans { display:flex; flex-direction:column; gap:10px; margin:14px 0 24px; }
.panel-promo .ruhan-fbar { display:grid; grid-template-columns:90px 1fr 220px; gap:14px; align-items:center; font-size:13px; }
.panel-promo .ruhan-fbar-lbl { color:#fff; font-weight:600; }
.panel-promo .ruhan-fbar-track { height:26px; background:#1a2540; border-radius:13px; overflow:hidden; }
.panel-promo .ruhan-fbar-fill { height:100%; display:flex; align-items:center; padding-left:10px; color:#000; font-weight:700; font-size:12px; transition:width .6s; }
.panel-promo .ruhan-fbar-meta { color:#94a3b8; font-size:12px; }
.panel-promo .ruhan-zero-wrap { margin:8px 0 24px; }
.panel-promo .ruhan-finding { background:linear-gradient(135deg,#3d2a0a 0%,#1a1810 100%); border:1px solid #fbbf24; border-radius:14px; padding:20px 24px; margin:24px 0; }
.panel-promo .ruhan-finding ol { margin:8px 0 0; padding-left:22px; color:#e8ecf4; line-height:1.9; }
.panel-promo .ruhan-finding ol li { margin-bottom:10px; }
.panel-promo .ruhan-action { background:linear-gradient(135deg,#0a2515 0%,#0a1428 100%); border:1px solid #22c55e; border-radius:14px; padding:20px 24px; margin:18px 0 12px; }
@media (max-width:760px) { .panel-promo .ruhan-banner, .panel-promo .ruhan-prodvs { grid-template-columns:1fr 1fr; } .panel-promo .ruhan-fbar { grid-template-columns:1fr; } }
</style>
"""

ruhan_section = ''.join(parts) + RUHAN_STYLE

# ── 618 panel hero replacements ──
OLD_SUBTITLE = '<p>数据来源：蒲公英 × 星河 | 时间范围：2026.05.13 - 06.13 | 72篇笔记交叉验证</p>'
NEW_SUBTITLE = '<p>数据来源：蒲公英 × 星河（金咖供应商 KOC 全样本）· 2026.05.13 - 06.13 · 72 篇笔记交叉验证（S1×36 + G1×36）· 总预算 ¥5万 · 星河 GMV ¥32万 · ROI 6.40×</p>'

OLD_METRICS = '<div class="metrics-grid"><div class="metric-card blue"><div class="value">3,629</div><div class="label">总互动量</div></div><div class="metric-card green"><div class="value">669</div><div class="label">总进店UV</div></div><div class="metric-card gold"><div class="value">¥9.1万</div><div class="label">总GMV</div></div><div class="metric-card red"><div class="value">4.52</div><div class="label">整体ROI</div></div></div>'
NEW_METRICS = '<div class="metrics-grid"><div class="metric-card blue"><div class="value">3,646</div><div class="label">总互动量</div></div><div class="metric-card green"><div class="value">9,224</div><div class="label">累计进店 UV</div></div><div class="metric-card gold"><div class="value">¥32.0万</div><div class="label">星河 GMV</div></div><div class="metric-card red"><div class="value">6.40×</div><div class="label">ROI（¥5 万预算）</div></div></div>'

FOOTER_ANCHOR = '<footer>618促单 · 小红书图文专项数据分析'

def process(path):
    if not os.path.exists(path):
        print(f"  ⚠ skip (missing): {path}")
        return
    with open(path, encoding='utf-8') as f:
        h = f.read()
    orig = h
    n_sub = h.count(OLD_SUBTITLE)
    if n_sub == 1:
        h = h.replace(OLD_SUBTITLE, NEW_SUBTITLE)
        print(f"  ✓ subtitle replaced")
    elif n_sub == 0 and NEW_SUBTITLE in h:
        print(f"  · subtitle already new")
    else:
        print(f"  ⚠ subtitle count={n_sub}")

    n_m = h.count(OLD_METRICS)
    if n_m == 1:
        h = h.replace(OLD_METRICS, NEW_METRICS)
        print(f"  ✓ metrics replaced")
    elif NEW_METRICS in h:
        print(f"  · metrics already new")
    else:
        print(f"  ⚠ metrics count={n_m}")

    if 'ruhan-section' in h:
        print(f"  · ruhan-section already exists, skipping inject")
    else:
        idx = h.find(FOOTER_ANCHOR)
        if idx < 0:
            print(f"  ⚠ FOOTER_ANCHOR not found")
        else:
            fopen = h.rfind('<footer', 0, idx)
            if fopen < 0:
                print(f"  ⚠ <footer cannot be located")
            else:
                h = h[:fopen] + ruhan_section + '\n' + h[fopen:]
                print(f"  ✓ ruhan-section injected (+{len(ruhan_section):,}B)")

    if h != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(h)
        print(f"  → wrote {path} (Δ {len(h)-len(orig):+,}B)")
    else:
        print(f"  · no changes for {path}")

for fp in FILES:
    print(f"\n=== {fp} ===")
    process(fp)

print("\n✓ all done")
