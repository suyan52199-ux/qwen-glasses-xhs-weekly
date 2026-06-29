# -*- coding: utf-8 -*-
"""
R29: 把如涵国补方向独立报告作为第 7 个 tab 注入主入口
- topnav 加 button: 📦 如涵国补方向
- main 加 panel-ruhan div（id=panel-ruhan）
- CSS 全部加 .panel-ruhan 前缀避免污染其它 panel
- 同步注入 dark + light + outputs 2 份桌面版

数据保持 6.29 新版本，与独立 HTML 完全一致
"""
import re, os, shutil

CSS_RAW = open('/tmp/ruhan_css.txt').read()
BODY_RAW = open('/tmp/ruhan_body.txt').read()

# Add .panel-ruhan scope to every CSS rule
def scope_css(css, prefix='.panel-ruhan '):
    # naive but works: prefix every selector before {
    out_lines = []
    i = 0
    while i < len(css):
        # find next {
        brace = css.find('{', i)
        if brace == -1:
            out_lines.append(css[i:])
            break
        sel_block = css[i:brace]
        # skip @media etc.
        if '@media' in sel_block or '@keyframes' in sel_block or '@supports' in sel_block:
            # find matching closing brace for nested
            depth = 0; j = brace
            while j < len(css):
                if css[j] == '{': depth += 1
                elif css[j] == '}':
                    depth -= 1
                    if depth == 0: break
                j += 1
            inner = css[brace+1:j]
            inner_scoped = scope_css(inner, prefix)
            out_lines.append(sel_block + '{\n' + inner_scoped + '\n}')
            i = j + 1
            continue
        # split selectors by comma
        selectors = [s.strip() for s in sel_block.split(',')]
        scoped = []
        for s in selectors:
            if not s: continue
            # for html, body, * — replace with .panel-ruhan
            if s in ('html', 'body', '*') or s.startswith('html ') or s.startswith('body '):
                scoped.append(prefix.rstrip())
            elif s.startswith(prefix):
                scoped.append(s)
            else:
                scoped.append(prefix + s)
        # find matching close brace
        depth = 1; j = brace + 1
        while j < len(css) and depth > 0:
            if css[j] == '{': depth += 1
            elif css[j] == '}': depth -= 1
            j += 1
        rule_body = css[brace+1:j-1]
        out_lines.append(', '.join(scoped) + ' {' + rule_body + '}')
        i = j
    return '\n'.join(out_lines)

scoped_css = scope_css(CSS_RAW)

# Tab button HTML
TAB_BTN = '<button class="tab-btn" data-tab="ruhan"><span class="ic">📦</span><span class="nm">如涵国补方向</span></button>'

# Panel HTML
PANEL_HTML = f'''<div class="panel panel-ruhan" id="panel-ruhan" data-panel="ruhan">
<header><h1>如涵国补方向 · 80 篇内容数据分析</h1><p>S1 × 71 + G1 × 9 · 总预算 ¥10 万 · 数据源 如涵国补方向6.29数据汇总.xls · 截止 6.29</p></header>
<div class="ruhan-wrap">{BODY_RAW}</div>
</div>'''

# Wrap CSS in style block — to be appended at last </style>
RUHAN_STYLE = f'''
/* === R29: 如涵国补方向 tab — 作用域 .panel-ruhan === */
.panel-ruhan {{ background:transparent; }}
.panel-ruhan .ruhan-wrap {{ max-width:1240px; margin:0 auto; padding:20px 4px; }}
.panel-ruhan header h1 {{ color:#fff; font-size:24px; margin-bottom:6px; }}
.panel-ruhan header p {{ color:#94a3b8; font-size:13px; }}
.panel-ruhan section {{ background:#0f1428; border:1px solid #1e2d5a; border-radius:14px; padding:22px 24px; margin-bottom:18px; }}
.panel-ruhan section > h2 {{ font-size:18px; color:#fff; margin-bottom:12px; padding-left:12px; border-left:4px solid #f59e0b; }}
.panel-ruhan section > p.sub {{ color:#94a3b8; font-size:13px; margin-bottom:14px; }}
.panel-ruhan h3 {{ color:#fff; font-size:16px; margin:18px 0 10px; }}
.panel-ruhan .banner {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:6px 0 18px; }}
.panel-ruhan .banner-card {{ background:linear-gradient(135deg,#1f2937 0%,#0f172a 100%); border:1px solid #334155; border-radius:12px; padding:16px; text-align:center; box-sizing:border-box; }}
.panel-ruhan .banner-card .v {{ display:block; font-size:28px; font-weight:900; line-height:1.1; }}
.panel-ruhan .banner-card .l {{ display:block; margin-top:4px; font-size:11.5px; color:#94a3b8; }}
.panel-ruhan .prodvs {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
.panel-ruhan .pcard {{ background:linear-gradient(135deg,#0f1b3d 0%,#1a2540 100%); border-radius:14px; padding:20px; border:1.5px solid #1e3a8a; box-sizing:border-box; }}
.panel-ruhan .pcard.g1 {{ border-color:#7c3aed; background:linear-gradient(135deg,#1a1432 0%,#2a1e4d 100%); }}
.panel-ruhan .pc-head {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; color:#fff; font-size:15px; }}
.panel-ruhan .pc-tag {{ font-size:11px; background:#3b82f6; color:#fff; padding:3px 8px; border-radius:10px; font-weight:600; }}
.panel-ruhan .pcard.g1 .pc-tag {{ background:#a78bfa; }}
.panel-ruhan .pc-roi {{ font-size:44px; font-weight:900; color:#60a5fa; line-height:1; margin:4px 0; }}
.panel-ruhan .pcard.g1 .pc-roi {{ color:#a78bfa; }}
.panel-ruhan .pc-roi .x {{ font-size:20px; margin-left:4px; }}
.panel-ruhan .pc-roi .desc {{ display:block; font-size:11px; color:#94a3b8; font-weight:500; letter-spacing:1.2px; margin-top:4px; }}
.panel-ruhan .pc-stats {{ display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:12px; }}
.panel-ruhan .pc-stats > div {{ background:#00000044; border-radius:8px; padding:8px 10px; }}
.panel-ruhan .pc-stats .v {{ font-size:14px; font-weight:700; color:#fff; display:block; line-height:1.2; }}
.panel-ruhan .pc-stats .l {{ font-size:10.5px; color:#94a3b8; margin-top:2px; }}
.panel-ruhan .pc-note {{ margin-top:10px; padding:9px 11px; background:#7f1d1d44; border-left:3px solid #ef4444; border-radius:6px; font-size:12px; color:#fca5a5; }}
.panel-ruhan .pcard.g1 .pc-note {{ background:#581c8744; border-left-color:#a78bfa; color:#c4b5fd; }}
.panel-ruhan table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
.panel-ruhan thead {{ background:#1e293b; }}
.panel-ruhan th {{ padding:9px 10px; text-align:left; color:#fbbf24; font-weight:700; font-size:11.5px; border-bottom:2px solid #334155; }}
.panel-ruhan td {{ padding:9px 10px; color:#e8ecf4; border-bottom:1px solid #1e293b; }}
.panel-ruhan tr.row-high td {{ background:#0a2515; }}
.panel-ruhan tr.row-mid td {{ background:#1e1810; }}
.panel-ruhan tr.row-low td {{ background:#2e0f0f; }}
.panel-ruhan td.rank {{ font-size:16px; font-weight:800; width:46px; }}
.panel-ruhan td.gmv {{ color:#22c55e; font-weight:800; }}
.panel-ruhan td.roi {{ color:#fbbf24; font-weight:800; }}
.panel-ruhan .tbl-wrap {{ overflow-x:auto; border-radius:10px; border:1px solid #1e2d5a; }}
.panel-ruhan .fans {{ display:flex; flex-direction:column; gap:10px; }}
.panel-ruhan .fbar {{ display:grid; grid-template-columns:90px 1fr 240px; gap:12px; align-items:center; font-size:12.5px; }}
.panel-ruhan .fbar-lbl {{ color:#fff; font-weight:600; }}
.panel-ruhan .fbar-track {{ height:26px; background:#1a2540; border-radius:13px; overflow:hidden; }}
.panel-ruhan .fbar-fill {{ height:100%; display:flex; align-items:center; padding-left:12px; color:#000; font-weight:700; font-size:11.5px; }}
.panel-ruhan .fbar-meta {{ color:#94a3b8; font-size:11.5px; }}
.panel-ruhan .finding {{ background:linear-gradient(135deg,#3d2a0a 0%,#1a1810 100%); border:1px solid #fbbf24; border-radius:14px; padding:20px 22px; }}
.panel-ruhan .finding h3 {{ color:#fbbf24; font-size:17px; margin:0 0 10px; }}
.panel-ruhan .finding ol {{ margin:0; padding-left:20px; color:#e8ecf4; line-height:1.85; }}
.panel-ruhan .finding ol li {{ margin-bottom:8px; }}
.panel-ruhan .action {{ background:linear-gradient(135deg,#0a2515 0%,#0a1428 100%); border:1px solid #22c55e; border-radius:14px; padding:20px 22px; }}
.panel-ruhan .action h3 {{ color:#22c55e; font-size:17px; margin:0 0 10px; }}
.panel-ruhan .action ul {{ margin:0; padding-left:20px; line-height:1.85; color:#cbd5e0; }}
.panel-ruhan .cpm-strip {{ margin:14px 0 6px; padding:14px 18px; background:#0d1530; border:1px solid #1e2d5a; border-radius:12px; }}
.panel-ruhan .cpm-strip h4 {{ margin:0 0 10px; color:#fff; font-size:13px; }}
.panel-ruhan .cpm-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
.panel-ruhan .cpm-card {{ padding:11px; border-radius:8px; border-left:3px solid #ef4444; background:#2e0f0f; box-sizing:border-box; }}
.panel-ruhan .cpm-card.win {{ border-left-color:#22c55e; background:#0a2515; }}
.panel-ruhan .cpm-card .label {{ color:#fca5a5; font-size:10.5px; }}
.panel-ruhan .cpm-card.win .label {{ color:#86efac; }}
.panel-ruhan .cpm-card .num {{ font-size:22px; font-weight:900; line-height:1.1; margin:4px 0; color:#ef4444; }}
.panel-ruhan .cpm-card.win .num {{ color:#22c55e; }}
.panel-ruhan .cpm-card .form {{ color:#94a3b8; font-size:10.5px; }}
.panel-ruhan .deposit-callout {{ margin:14px 0; padding:14px 18px; background:linear-gradient(135deg,#3d2a0a 0%,#1a1810 100%); border-left:4px solid #fbbf24; border-radius:10px; }}
.panel-ruhan .deposit-callout h4 {{ margin:0 0 6px; color:#fbbf24; font-size:14px; }}
.panel-ruhan .deposit-callout p {{ margin:0; color:#e8ecf4; font-size:13px; line-height:1.7; }}
.panel-ruhan footer {{ text-align:center; color:#64748b; font-size:11.5px; padding:18px 0 6px; }}
@media (max-width:900px) {{ .panel-ruhan .banner, .panel-ruhan .prodvs, .panel-ruhan .cpm-grid {{ grid-template-columns:1fr 1fr; }} .panel-ruhan .fbar {{ grid-template-columns:1fr; }} }}
@media (max-width:600px) {{ .panel-ruhan .banner, .panel-ruhan .prodvs, .panel-ruhan .cpm-grid {{ grid-template-columns:1fr; }} }}
'''

TARGETS = [
    'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    'docs/weeks/W1-2026-05-13_to_06-13/index-light.html',
    'outputs/KOC铺量内容.html',
    'outputs/KOC铺量内容-白底版.html',
]

for fp in TARGETS:
    h = open(fp, encoding='utf-8').read()
    if 'data-tab="ruhan"' in h:
        print(f"⚠ already injected: {fp}")
        continue
    orig = len(h)
    # 1) Add tab btn after funnel button
    funnel_btn_close = '<span class="nm">KOC决策漏斗×ROI</span></button>'
    h = h.replace(funnel_btn_close, funnel_btn_close + TAB_BTN)
    # 2) Add panel before closing main — find </main>
    if '</main>' in h:
        h = h.replace('</main>', PANEL_HTML + '</main>', 1)
    else:
        # fallback: insert before script
        pass
    # 3) Add CSS to last </style>
    last_close = h.rfind('</style>')
    h = h[:last_close] + RUHAN_STYLE + h[last_close:]

    open(fp, 'w', encoding='utf-8').write(h)
    print(f"✓ {fp}  {orig:,} → {len(h):,}  Δ {len(h)-orig:+,}")

# desktop sync
shutil.copy('outputs/KOC铺量内容.html', '/Users/xiemila/Desktop/KOC铺量内容.html')
shutil.copy('outputs/KOC铺量内容-白底版.html', '/Users/xiemila/Desktop/KOC铺量内容-白底版.html')
print('📋 desktop sync done')
