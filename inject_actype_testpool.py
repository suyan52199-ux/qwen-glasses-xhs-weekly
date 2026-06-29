#!/usr/bin/env python3
"""Inject KOC account-type analysis + enhanced test-pool section into HTML."""
import json, re
from pathlib import Path

PATH = 'docs/weeks/W1-2026-05-13_to_06-13/index.html'
with open(PATH, encoding='utf-8') as f:
    h = f.read()

stats = json.load(open('koc_account_type_v2.json'))
top = json.load(open('koc_account_type_top.json'))

def fmt_money(v):
    v = float(v or 0)
    if v >= 10000: return f"¥{v/10000:.1f}万"
    return f"¥{v:,.0f}"

# main types (>=10 notes)
main_types = sorted([s for s in stats if s['notes'] >= 10], key=lambda x: x['roi'], reverse=True)
small_types = sorted([s for s in stats if s['notes'] < 10], key=lambda x: x['notes'], reverse=True)

TOTAL_KOC_NOTES = 600
TOTAL_KOC_GMV = 3567123
TOTAL_KOC_COST = 436057

# build cards
cards_html = ''
for s in main_types:
    tier_class = 'tier-high' if s['roi'] >= 10 else ('tier-mid' if s['roi'] >= 5 else 'tier-low')
    tier_label = '⭐头部赛道' if s['roi'] >= 10 else ('正常' if s['roi'] >= 5 else '⚠️低效')
    bar_pct = min(100, s['roi'] / 15 * 100)
    cards_html += (
        f'<div class="actype-card {tier_class}">'
        f'<div class="actype-head"><div class="actype-name">{s["account_type"]}</div>'
        f'<div class="actype-tag">{tier_label}</div></div>'
        f'<div class="actype-roi"><span class="big">{s["roi"]:.2f}</span>'
        f'<span class="x">×</span><span class="lbl">ROI</span></div>'
        f'<div class="actype-bar"><div class="actype-bar-fill" style="width:{bar_pct:.0f}%"></div></div>'
        f'<div class="actype-stats">'
        f'<div><span class="k">篇数</span><span class="v">{s["notes"]}</span></div>'
        f'<div><span class="k">总GMV</span><span class="v">{fmt_money(s["gmv"])}</span></div>'
        f'<div><span class="k">总消耗</span><span class="v">{fmt_money(s["cost"])}</span></div>'
        f'<div><span class="k">篇均GMV</span><span class="v">{fmt_money(s["gmv_per_note"])}</span></div>'
        f'<div><span class="k">篇均互动</span><span class="v">{s["interact_per_note"]:.0f}</span></div>'
        f'<div><span class="k">进店转化</span><span class="v">{s["cvr_shop"]:.2f}%</span></div>'
        f'</div></div>'
    )

small_rows = ''
for s in small_types:
    small_rows += (
        f'<tr><td>{s["account_type"]}</td><td>{s["notes"]}</td>'
        f'<td>{fmt_money(s["cost"])}</td><td>{fmt_money(s["gmv"])}</td>'
        f'<td>{s["roi"]:.2f}×</td><td>{s["interact_per_note"]:.0f}</td></tr>'
    )

top_html = ''
for s in main_types:
    at = s['account_type']
    bloggers = top.get(at, [])[:5]
    rows = ''
    for b in bloggers:
        nick = b['达人昵称']
        roi = b.get('roi') or 0
        gmv = b.get('gmv') or 0
        rows += (
            f'<tr><td>{nick}</td><td>{b.get("内容方向","")}</td>'
            f'<td>{b.get("product","")}</td><td>{fmt_money(gmv)}</td>'
            f'<td>{(roi or 0):.1f}×</td></tr>'
        )
    top_html += (
        f'<div class="actype-top-block">'
        f'<h4>{at} · 篇均GMV {fmt_money(s["gmv_per_note"])} · Top 5</h4>'
        f'<table class="actype-top-tbl"><thead><tr>'
        f'<th>达人</th><th>方向</th><th>产品</th><th>GMV</th><th>ROI</th>'
        f'</tr></thead><tbody>{rows}</tbody></table></div>'
    )

# Get specific stats for insight box
def get(name):
    return next((s for s in main_types if s['account_type'] == name), None)
sci = get('🔬数码科技测评')
life = get('🌿生活分享')
generic = get('👤泛人格素人')
pet = get('🐱萌宠')

actype_data_for_chart = [
    {'name': s['account_type'], 'roi': s['roi'], 'gmv_per_note': s['gmv_per_note'], 'notes': s['notes']}
    for s in main_types
]

actype_section = (
    f'<div class="section actype-section">'
    f'<h2 class="section-title" style="border-left-color:#FFB800">KOC 账号类型效率拆解 '
    f'<span class="ribbon-new">NEW</span></h2>'
    f'<p class="section-sub">按昵称关键词把 600 篇 KOC 分成 9 类账号人设 · 同一品牌同一内容方向，不同账号类型 ROI 拉开 <b style="color:#FFB800">5 倍以上</b></p>'
    f'<div class="actype-headline">'
    f'<div class="hl-card hl-win"><div class="hl-tag">🏆 头部赛道</div>'
    f'<div class="hl-name">{sci["account_type"]}</div>'
    f'<div class="hl-val">{sci["roi"]:.2f}<span>×</span></div>'
    f'<div class="hl-desc">{sci["notes"]} 篇 · 篇均 GMV {fmt_money(sci["gmv_per_note"])} · '
    f'CPE 仅 ¥{sci["cpe"]:.0f} · 进店转化率 {sci["cvr_shop"]:.1f}% — '
    f'是 KOC 整体ROI(8.18×) 的 {sci["roi"]/8.18:.1f} 倍</div></div>'
    f'<div class="hl-card hl-bad"><div class="hl-tag">⚠️ 待优化</div>'
    f'<div class="hl-name">{generic["account_type"]}</div>'
    f'<div class="hl-val">{generic["roi"]:.2f}<span>×</span></div>'
    f'<div class="hl-desc">{generic["notes"]} 篇（占基本盘 {generic["notes"]/TOTAL_KOC_NOTES*100:.0f}%）· '
    f'篇均 GMV {fmt_money(generic["gmv_per_note"])} · '
    f'消耗 {fmt_money(generic["cost"])}（占 KOC 总投入 {generic["cost"]/TOTAL_KOC_COST*100:.0f}%）'
    f'但效率仅是科技测评的 1/{sci["roi"]/generic["roi"]:.0f}</div></div>'
    f'</div>'
    f'<div class="actype-cards">{cards_html}</div>'
    f'<div class="chart-container"><h3 style="color:#fff;font-size:16px;margin-bottom:16px;">'
    f'主流账号类型 ROI × 篇均GMV 双轴对比</h3>'
    f'<div id="actype-chart" class="chart-box short"></div></div>'
    f'<div class="actype-tops">{top_html}</div>'
    f'<details class="actype-small">'
    f'<summary>📌 小样本类型一览（&lt;10 篇 · 结论参考价值低）</summary>'
    f'<table class="actype-top-tbl"><thead><tr>'
    f'<th>账号类型</th><th>篇数</th><th>消耗</th><th>GMV</th><th>ROI</th><th>篇均互动</th>'
    f'</tr></thead><tbody>{small_rows}</tbody></table></details>'
    f'<div class="conclusion-box" style="border-left:4px solid #FFB800"><h4>🎯 账号类型效率结论</h4><ul>'
    f'<li><strong>🔬 数码科技测评类是真王者</strong>：仅 {sci["notes"]}/{TOTAL_KOC_NOTES} 篇 '
    f'({sci["notes"]/TOTAL_KOC_NOTES*100:.0f}%)，却贡献 {sci["gmv"]/TOTAL_KOC_GMV*100:.0f}% 的 GMV — '
    f'ROI <b>{sci["roi"]:.1f}×</b> 是泛人格素人({generic["roi"]:.1f}×)的 '
    f'<b>{sci["roi"]/generic["roi"]:.1f} 倍</b>。粉丝精准、买点听得懂、决策周期短</li>'
    f'<li><strong>🌿 生活分享类是隐藏 B 角</strong>：{life["notes"]} 篇 ROI {life["roi"]:.1f}× — '
    f'内容更软+场景化，是科技测评的辅助补充</li>'
    f'<li><strong>👤 泛人格素人占比过高拖累整体</strong>：{generic["notes"]} 篇消耗 {fmt_money(generic["cost"])}'
    f'（占 {generic["cost"]/TOTAL_KOC_COST*100:.0f}%）但 ROI 仅 {generic["roi"]:.1f}× — '
    f'多为无明确标签的「泛娱乐账号」（如"美成啥样了""一觉睡到小时候"），粉丝无明确购买意向</li>'
    f'<li><strong>🐱 萌宠/亲子/职场 ROI &lt;5×</strong>：跟科技品类调性不匹配，建议除非有强场景关联，否则停投</li>'
    f'<li><strong>核心动作</strong>：① 把数码科技测评类占比从 {sci["notes"]/TOTAL_KOC_NOTES*100:.0f}% 提升到 50%+ — '
    f'1:1 替换泛人格素人预算 ② 建立"数码科技测评账号白名单"，从现有 {sci["notes"]} 篇头部里筛 30-50 个复投 '
    f'③ 生活分享类作为破圈测试，控制在 20-30 篇/月</li>'
    f'</ul></div></div>'
)

# CSS additions
css_additions = '''
.panel-s1g1 .ribbon-new{display:inline-block;background:#FFB800;color:#000;font-size:11px;font-weight:800;padding:3px 10px;border-radius:10px;margin-left:8px;vertical-align:middle;animation:pulse-new 1.6s ease-in-out infinite}
@keyframes pulse-new{0%,100%{box-shadow:0 0 0 0 #FFB800AA}50%{box-shadow:0 0 0 6px #FFB80000}}
.panel-s1g1 .actype-headline{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:18px 0 24px}
.panel-s1g1 .hl-card{padding:22px 26px;border-radius:14px;border:1px solid;position:relative;overflow:hidden}
.panel-s1g1 .hl-win{background:linear-gradient(135deg,#0a1a14 0%,#00C9A722 70%,#FFB80022 100%);border-color:#00C9A7}
.panel-s1g1 .hl-bad{background:linear-gradient(135deg,#1a0a14 0%,#FF6B6B22 100%);border-color:#FF6B6B66}
.panel-s1g1 .hl-tag{font-size:12px;opacity:.7;margin-bottom:6px;color:#fff}
.panel-s1g1 .hl-name{font-size:19px;font-weight:700;margin-bottom:8px;color:#fff}
.panel-s1g1 .hl-val{font-size:44px;font-weight:900;line-height:1;margin-bottom:10px}
.panel-s1g1 .hl-win .hl-val{color:#00C9A7}
.panel-s1g1 .hl-bad .hl-val{color:#FF6B6B}
.panel-s1g1 .hl-val span{font-size:22px;margin-left:4px}
.panel-s1g1 .hl-desc{font-size:13px;color:#cbd5e0;line-height:1.7}
.panel-s1g1 .actype-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-bottom:20px}
.panel-s1g1 .actype-card{background:#161e2e;border:1px solid #2a3650;border-radius:12px;padding:16px;transition:transform .2s}
.panel-s1g1 .actype-card:hover{transform:translateY(-3px)}
.panel-s1g1 .actype-card.tier-high{border-color:#00C9A7;box-shadow:0 0 0 1px #00C9A744,0 4px 16px #00C9A722}
.panel-s1g1 .actype-card.tier-mid{border-color:#FFB80055}
.panel-s1g1 .actype-card.tier-low{opacity:.75}
.panel-s1g1 .actype-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.panel-s1g1 .actype-name{font-weight:700;color:#fff;font-size:15px}
.panel-s1g1 .actype-tag{font-size:11px;padding:3px 9px;border-radius:8px;background:#243450;color:#cbd5e0}
.panel-s1g1 .tier-high .actype-tag{background:#00C9A7;color:#000;font-weight:700}
.panel-s1g1 .tier-low .actype-tag{background:#FF6B6B33;color:#FF6B6B}
.panel-s1g1 .actype-roi{display:flex;align-items:baseline;gap:6px;margin:6px 0}
.panel-s1g1 .actype-roi .big{font-size:32px;font-weight:800;color:#FFB800;line-height:1}
.panel-s1g1 .actype-roi .x{font-size:18px;color:#FFB800}
.panel-s1g1 .actype-roi .lbl{font-size:11px;color:#888;margin-left:auto}
.panel-s1g1 .actype-bar{height:4px;background:#243450;border-radius:2px;overflow:hidden;margin:8px 0 12px}
.panel-s1g1 .actype-bar-fill{height:100%;background:linear-gradient(90deg,#FFB800,#00C9A7);border-radius:2px}
.panel-s1g1 .actype-stats{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;font-size:12px}
.panel-s1g1 .actype-stats>div{display:flex;justify-content:space-between;color:#999}
.panel-s1g1 .actype-stats .v{color:#fff;font-weight:600}
.panel-s1g1 .actype-tops{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-top:16px}
.panel-s1g1 .actype-top-block{background:#0f1626;border:1px solid #1f2942;border-radius:10px;padding:12px}
.panel-s1g1 .actype-top-block h4{font-size:13px;color:#FFB800;margin:0 0 8px;padding:0;border:none}
.panel-s1g1 .actype-top-tbl{width:100%;border-collapse:collapse;font-size:12px}
.panel-s1g1 .actype-top-tbl th{text-align:left;padding:5px 6px;color:#888;font-weight:500;border-bottom:1px solid #243450}
.panel-s1g1 .actype-top-tbl td{padding:5px 6px;color:#ccc;border-bottom:1px solid #1a2238}
.panel-s1g1 .actype-small{margin-top:18px;background:#0f1626;border:1px solid #1f2942;border-radius:10px;padding:10px 14px}
.panel-s1g1 .actype-small summary{cursor:pointer;color:#FFB800;font-weight:600;font-size:13px}
.panel-s1g1 .actype-small table{margin-top:10px}

/* === Test-pool MEGA enhancement === */
.panel-s1g1 .testpool-mega{position:relative;background:radial-gradient(ellipse at top left,#0a2235 0%,#0a1428 60%,#1a0f35 100%);border:2px solid transparent;border-radius:22px;padding:34px 28px 28px;margin:36px 0 28px;background-clip:padding-box;overflow:hidden}
.panel-s1g1 .testpool-mega::before{content:"";position:absolute;inset:0;background:linear-gradient(135deg,#00C9A744,#FFB80044,#FF6B6B44);border-radius:22px;padding:2px;-webkit-mask:linear-gradient(#fff 0 0) content-box,linear-gradient(#fff 0 0);-webkit-mask-composite:xor;mask-composite:exclude;pointer-events:none;z-index:0}
.panel-s1g1 .testpool-mega>*{position:relative;z-index:1}
.panel-s1g1 .testpool-badge{position:absolute;top:-1px;left:24px;background:linear-gradient(90deg,#FFB800,#00C9A7,#0099ff);color:#000;font-weight:900;font-size:11px;letter-spacing:3px;padding:6px 18px;border-radius:0 0 10px 10px;box-shadow:0 4px 14px #00C9A766;z-index:2}
.panel-s1g1 .testpool-mega .testpool-h2{font-size:26px;font-weight:800;color:#fff;margin:8px 0 4px;padding:0;display:flex;align-items:center;gap:10px}
.panel-s1g1 .testpool-mega .testpool-h2 .emoji{font-size:30px}
.panel-s1g1 .testpool-mega .testpool-sub{color:#aabacf;font-size:13px;margin-bottom:22px}
.panel-s1g1 .testpool-vs{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}
.panel-s1g1 .testpool-card{position:relative;padding:24px;border-radius:14px;transition:transform .2s}
.panel-s1g1 .testpool-card:hover{transform:translateY(-3px)}
.panel-s1g1 .testpool-good{background:linear-gradient(135deg,#0a2f1a 0%,#00C9A733 100%);border:1.5px solid #00C9A7;box-shadow:0 8px 30px #00C9A733}
.panel-s1g1 .testpool-meh{background:linear-gradient(135deg,#2f1a0a 0%,#FFB80022 100%);border:1.5px solid #FFB800;box-shadow:0 8px 30px #FFB80022}
.panel-s1g1 .testpool-card .badge-corner{position:absolute;top:14px;right:14px;font-size:11px;font-weight:800;padding:4px 12px;border-radius:8px;letter-spacing:1px}
.panel-s1g1 .testpool-good .badge-corner{background:#00C9A7;color:#000}
.panel-s1g1 .testpool-meh .badge-corner{background:#FFB800;color:#000}
.panel-s1g1 .testpool-card h3{margin:0 0 4px;padding:0;border:none;font-size:19px;color:#fff;font-weight:700}
.panel-s1g1 .testpool-card .sub{font-size:12px;color:#bbb;margin-bottom:14px;line-height:1.6}
.panel-s1g1 .testpool-roi-big{font-size:62px;font-weight:900;line-height:1;margin:10px 0 4px}
.panel-s1g1 .testpool-good .testpool-roi-big{color:#00C9A7;text-shadow:0 0 24px #00C9A744}
.panel-s1g1 .testpool-meh .testpool-roi-big{color:#FFB800;text-shadow:0 0 24px #FFB80044}
.panel-s1g1 .testpool-roi-big .x{font-size:28px;margin-left:4px}
.panel-s1g1 .testpool-roi-big .vs{display:block;font-size:11px;color:#999;font-weight:500;margin-top:4px;letter-spacing:1.5px}
.panel-s1g1 .testpool-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:16px}
.panel-s1g1 .testpool-stats>div{background:#00000044;border-radius:10px;padding:10px}
.panel-s1g1 .testpool-stats .v{font-size:17px;font-weight:700;color:#fff;display:block;line-height:1.2}
.panel-s1g1 .testpool-stats .l{font-size:11px;color:#999;margin-top:4px}
.panel-s1g1 .testpool-compare{background:#0a1428cc;border:1px solid #1a2540;border-radius:14px;padding:18px 20px;margin-top:16px;backdrop-filter:blur(8px)}
.panel-s1g1 .testpool-compare h4{font-size:14px;color:#FFB800;margin:0 0 14px;padding:0;border:none;font-weight:700}
.panel-s1g1 .testpool-cbar{display:grid;grid-template-columns:90px 1fr 90px;gap:12px;align-items:center;margin-bottom:10px;font-size:12px}
.panel-s1g1 .testpool-cbar .lbl{color:#cbd5e0;font-weight:600}
.panel-s1g1 .testpool-cbar .bar{height:22px;background:#1a2540;border-radius:11px;overflow:hidden;position:relative}
.panel-s1g1 .testpool-cbar .bar-fill{height:100%;border-radius:11px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;color:#000;font-weight:700;font-size:11px;transition:width .6s ease-out}
.panel-s1g1 .testpool-cbar .bar-fill.main{background:linear-gradient(90deg,#0099ff,#00C9A7)}
.panel-s1g1 .testpool-cbar .bar-fill.jinka{background:linear-gradient(90deg,#FFB800,#00C9A7)}
.panel-s1g1 .testpool-cbar .bar-fill.ruhan{background:linear-gradient(90deg,#FF6B6B,#FFB800)}
.panel-s1g1 .testpool-cbar .val{text-align:right;color:#fff;font-weight:700;font-size:14px}
.panel-s1g1 .testpool-conclusion{background:linear-gradient(135deg,#1a2f1a 0%,#0a1a14 100%);border-left:4px solid #00C9A7;border-radius:10px;padding:16px 20px;margin-top:14px}
.panel-s1g1 .testpool-conclusion h4{font-size:14px;color:#00C9A7;margin:0 0 8px;padding:0;border:none}
.panel-s1g1 .testpool-conclusion ul{margin:0;padding-left:18px}
.panel-s1g1 .testpool-conclusion li{font-size:13px;color:#cbd5e0;line-height:1.8;margin-bottom:4px}
.panel-s1g1 .testpool-conclusion li strong{color:#fff}
@media(max-width:760px){.panel-s1g1 .actype-headline,.panel-s1g1 .testpool-vs{grid-template-columns:1fr}}
'''

# new test-pool section (strong visual)
new_test_section = (
    '<div class="testpool-mega">'
    '<div class="testpool-badge">🧪 NEW TEST POOL · 新内容供应商试投</div>'
    '<h2 class="testpool-h2"><span class="emoji">🆕</span>新内容类型测试 · 如涵 + 金咖（152篇）</h2>'
    '<p class="testpool-sub">独立于主力铺量(KOC600+KOL34=634篇) · 测试不同供应商与内容组合的投产效率 · 数据截止 6.22</p>'
    '<div class="testpool-vs">'
    # Jinka — winner
    '<div class="testpool-card testpool-good">'
    '<span class="badge-corner">✅ 高效</span>'
    '<h3>金咖 · 聚光+星河 KOC</h3>'
    '<div class="sub">S1 + G1 混合 · 聚光投流 + 蒲公英笔记 · 星河归因截止 6.23</div>'
    '<div class="testpool-roi-big">10.65<span class="x">×</span><span class="vs">ROI · 超过主力均值 9.60×</span></div>'
    '<div class="testpool-stats">'
    '<div><span class="v">72</span><span class="l">投放笔记</span></div>'
    '<div><span class="v">¥3.0万</span><span class="l">聚光消耗</span></div>'
    '<div><span class="v">¥32.0万</span><span class="l">星河GMV</span></div>'
    '<div><span class="v">¥4,439</span><span class="l">篇均GMV</span></div>'
    '<div><span class="v">9,224</span><span class="l">累计进店</span></div>'
    '<div><span class="v">1,653</span><span class="l">搜索UV</span></div>'
    '</div></div>'
    # Ruhan — lose
    '<div class="testpool-card testpool-meh">'
    '<span class="badge-corner">⚠️ 待优化</span>'
    '<h3>如涵 · 618促销 KOC</h3>'
    '<div class="sub">S1×71 篇 + G1×9 篇 · 618 节点促单内容 · 数据截止 6.22</div>'
    '<div class="testpool-roi-big">2.65<span class="x">×</span><span class="vs">ROI · 不到主力均值 1/3</span></div>'
    '<div class="testpool-stats">'
    '<div><span class="v">80</span><span class="l">投放笔记</span></div>'
    '<div><span class="v">¥10.7万</span><span class="l">总消耗</span></div>'
    '<div><span class="v">¥28.5万</span><span class="l">总GMV</span></div>'
    '<div><span class="v">¥3,566</span><span class="l">篇均GMV</span></div>'
    '<div><span class="v">4,564</span><span class="l">总互动</span></div>'
    '<div><span class="v">3,226</span><span class="l">总进店</span></div>'
    '</div></div>'
    '</div>'
    # comparison bar
    '<div class="testpool-compare">'
    '<h4>📊 ROI 三方对比：主力铺量 vs 金咖 vs 如涵</h4>'
    '<div class="testpool-cbar"><div class="lbl">🏆 金咖</div><div class="bar"><div class="bar-fill jinka" style="width:100%">10.65×</div></div><div class="val">¥4,439 篇均</div></div>'
    '<div class="testpool-cbar"><div class="lbl">📋 主力铺量</div><div class="bar"><div class="bar-fill main" style="width:90%">9.60×</div></div><div class="val">¥9,236 篇均</div></div>'
    '<div class="testpool-cbar"><div class="lbl">⚠️ 如涵</div><div class="bar"><div class="bar-fill ruhan" style="width:25%">2.65×</div></div><div class="val">¥3,566 篇均</div></div>'
    '</div>'
    '<div class="testpool-conclusion"><h4>🎯 测试结论与行动指令</h4><ul>'
    '<li><strong>金咖模式立即追加预算</strong>：聚光精准投流 + 蒲公英低消耗笔记的组合拳跑通了，下个月预算从 ¥3 万追加到 ¥10 万验证规模化效果</li>'
    '<li><strong>如涵需要做内容质量复盘</strong>：80 篇消耗 ¥10.7 万但只产 ¥28.5 万 GMV — S1 方向 71 篇但转化力远低于同方向原始 KOC（同方向 ROI 16.01×），优先排查达人匹配/选题/挂车环节</li>'
    '<li><strong>如涵下一轮限定方向</strong>：只投 G1 横测方向（主力已验证 ROI 12.07×），暂停 S1 方向；同时单价从¥1300 砍到 ¥800/篇验证软成本是否能拉回 ROI</li>'
    '<li><strong>差距 4 倍背后</strong>：金咖单篇效率(¥4,439)接近主力均值，如涵(¥3,566)偏低 — 关键差异在「聚光投流的精准搜索流量入口」 vs 「618 促单纯软文」</li>'
    '</ul></div>'
    '</div>'
)

# Replace old test section
start_marker = '<div class="section"><h2 class="section-title" style="border-left-color:#00C9A7">新内容类型测试'
end_marker = '<div class="section"><h2 class="section-title">综合行动建议</h2>'
i_s = h.find(start_marker)
i_e = h.find(end_marker, i_s)
assert i_s > 0 and i_e > i_s, f"markers not found: s={i_s},e={i_e}"

# Insert: actype_section + new_test_section, replacing the old section
new_block = actype_section + new_test_section
h2 = h[:i_s] + new_block + h[i_e:]
print(f"Old len: {len(h)}, new len: {len(h2)}, delta: {len(h2)-len(h)}")

# Inject CSS at end of <style> block (we'll find the last </style> in head area)
# Find first </style> after <head>
i_style_end = h2.find('</style>')
assert i_style_end > 0
h2 = h2[:i_style_end] + css_additions + h2[i_style_end:]
print(f"After CSS: {len(h2)}")

# Inject ECharts init for actype-chart. Find the init script for panel-s1g1.
# We use a small JS that hooks into the existing tab activation system.
# Find the function that initializes s1g1 charts: look for `function init_s1g1` or similar
m_init = re.search(r'function (init_s1g1|s1g1_init)\([^)]*\)\s*\{', h2)
if m_init:
    print(f"found init func: {m_init.group(1)} at {m_init.start()}")
else:
    # Try search for echarts.init with id matching s1g1 charts
    print("init_s1g1 not found, searching for echarts.init in s1g1 area...")
    for m in re.finditer(r"echarts\.init\(document\.getElementById\('([^']+)'\)", h2):
        if 'dir-chart' in m.group(1) or 'product-vs' in m.group(1):
            print(f"  echarts.init for {m.group(1)} at {m.start()}")
            print(h2[max(0,m.start()-200):m.start()+100])
            print('---')
            break

# Build ECharts script for actype-chart
chart_data_js = json.dumps(actype_data_for_chart, ensure_ascii=False)
actype_chart_js = '''
function init_actype_chart(){
  var el=document.getElementById('actype-chart');
  if(!el||el.dataset.inited)return;el.dataset.inited='1';
  var data=''' + chart_data_js + ''';
  data.sort(function(a,b){return b.roi-a.roi});
  var names=data.map(function(d){return d.name});
  var rois=data.map(function(d){return +d.roi.toFixed(2)});
  var gpns=data.map(function(d){return +d.gmv_per_note.toFixed(0)});
  var notes=data.map(function(d){return d.notes});
  var chart=echarts.init(el);
  chart.setOption({
    backgroundColor:'transparent',
    tooltip:{trigger:'axis',axisPointer:{type:'shadow'},
      formatter:function(p){var r='<b>'+p[0].name+'</b><br/>';
        p.forEach(function(it){r+=it.marker+it.seriesName+': '+it.value+(it.seriesName==='ROI(×)'?'×':(it.seriesName==='篇均GMV(¥)'?'':''))+'<br/>'});
        var idx=p[0].dataIndex;r+='<br/>📊 篇数: '+notes[idx];return r}},
    legend:{data:['ROI(×)','篇均GMV(¥)'],textStyle:{color:'#cbd5e0'},top:6},
    grid:{left:60,right:60,top:50,bottom:30},
    xAxis:{type:'category',data:names,axisLabel:{color:'#cbd5e0',rotate:0,interval:0,fontSize:11}},
    yAxis:[
      {type:'value',name:'ROI(×)',position:'left',axisLabel:{color:'#00C9A7',formatter:'{value}×'},nameTextStyle:{color:'#00C9A7'},splitLine:{lineStyle:{color:'#243450'}}},
      {type:'value',name:'篇均GMV(¥)',position:'right',axisLabel:{color:'#FFB800',formatter:'{value}'},nameTextStyle:{color:'#FFB800'},splitLine:{show:false}}
    ],
    series:[
      {name:'ROI(×)',type:'bar',data:rois,itemStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'#00C9A7'},{offset:1,color:'#0099ff'}]),borderRadius:[6,6,0,0]},label:{show:true,position:'top',color:'#00C9A7',formatter:'{c}×',fontWeight:700}},
      {name:'篇均GMV(¥)',type:'line',yAxisIndex:1,data:gpns,smooth:true,lineStyle:{color:'#FFB800',width:3},itemStyle:{color:'#FFB800'},symbol:'circle',symbolSize:8,label:{show:true,color:'#FFB800',formatter:function(p){return p.value>=10000?(p.value/10000).toFixed(1)+'w':p.value}}}
    ]
  });
  window.addEventListener('resize',function(){chart.resize()});
}
'''

# Hook into existing init_s1g1 function: add the call at the end
m_init = re.search(r'function init_s1g1\([^)]*\)\s*\{', h2)
if m_init:
    # find matching close brace
    start = m_init.end()
    depth = 1
    i = start
    while i < len(h2) and depth > 0:
        c = h2[i]
        if c == '{': depth += 1
        elif c == '}': depth -= 1
        i += 1
    func_end = i - 1  # position of closing brace
    # insert call before closing brace
    insertion = "\ntry{init_actype_chart()}catch(e){console.error(e)}\n"
    h2 = h2[:func_end] + insertion + h2[func_end:]
    print(f"Hooked into init_s1g1 at {func_end}")
else:
    print("WARN: init_s1g1 not found - will append as immediate IIFE")

# Append the function definition before </body>
i_body_end = h2.rfind('</body>')
assert i_body_end > 0
script_block = '<script>' + actype_chart_js + '</script>'
h2 = h2[:i_body_end] + script_block + h2[i_body_end:]

with open(PATH, 'w', encoding='utf-8') as f:
    f.write(h2)
print(f"\n✅ Written {len(h2)} bytes to {PATH}")
