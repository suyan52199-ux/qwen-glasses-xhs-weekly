#!/usr/bin/env python3
"""
R37: 撤销独立的「S1/G1 产品内容流动分析」区块，把 S1/G1 拆分并入
panel-promo 原有的「内容分类 → 效果流向（桑基图）」，采用铺量板块
三阶桑基格式：产品 → 内容分类 → 互动/进店/转化效果。
TARGETS（硬规则）：docs dark + outputs/KOC铺量内容.html + 桌面同步
"""
import re, json, shutil
from pathlib import Path
import pandas as pd

ROOT = Path('/Users/xiemila/.qoderwork/workspace/mq6ecbjzd6kpfcgy')
TARGETS = [
    ROOT / 'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    ROOT / 'outputs/KOC铺量内容.html',
]
DESKTOP = Path('/Users/xiemila/Desktop/KOC铺量内容.html')

CATS = ['图文横测', '用户评论证言', '金字塔(避坑种草)', '大促攻略', '国补攻略', '功能卖点', '场景体验', '其他种草']

def classify_cat(title: str) -> str:
    t = title.lower()
    if '618' in t or '攻略' in t or '挑花眼' in t or '必入清单' in t:
        return '大促攻略'
    if '国补' in title or '补贴' in title or '抄底' in title or '捡漏' in title:
        return '国补攻略'
    if any(k in t for k in ['横测', '横评', '对比', 'vs', '怎么选', '多款', '几款', '闭眼选', '测评']):
        return '图文横测'
    if any(k in t for k in ['踩雷', '避坑', '别乱买', '红黑榜', '坑', '乱买', '别被骗']):
        return '金字塔(避坑种草)'
    if any(k in t for k in ['真实体验', '实测', '入手', '真香', '后悔', '开箱', '无广', '戴一周', '太绝了']):
        return '用户评论证言'
    if any(k in t for k in ['功能', '配置', '续航', '翻译', '参数', '硬核', '办公', '学习', '旅行', '拍照', '出差', '演讲', '汇报', '学生党']):
        return '功能卖点'
    if any(k in t for k in ['场景', '生活', '日常', '职场', '户外', '出行', '打工人', '创业', '治愈']):
        return '场景体验'
    return '其他种草'

def num(x):
    try:
        return float(x) if pd.notna(x) else 0.0
    except Exception:
        return 0.0

# ── load notes ──
jdf = pd.read_excel('/Users/xiemila/Downloads/金咖618节点KOC促单汇总.xlsx', sheet_name='蒲公英源表', header=2)
notes = []
for _, r in jdf.iterrows():
    title = str(r.iloc[5]).strip() if pd.notna(r.iloc[5]) else ''
    if not title or title == 'nan':
        continue
    coop = str(r.iloc[13]) if pd.notna(r.iloc[13]) else ''
    product = 'S1' if 'S1' in coop else ('G1' if 'G1' in coop else '?')
    notes.append({
        'title': title,
        'product': product,
        'category': classify_cat(title),
        'interact': num(r.iloc[28]),
        'store': num(r.iloc[123]),
    })

TOTAL_GMV = 320082.29
TOTAL_STORE = 9383.0
for n in notes:
    n['est_gmv'] = (n['store'] / TOTAL_STORE * TOTAL_GMV) if TOTAL_STORE > 0 else 0.0

# ── build product-split sankey: product → category → outcome ──
outcome_nodes = ['高互动(>80)', '中互动(30-80)', '低互动(<30)', '高进店(>10UV)', '有GMV转化', '无转化']
nodes = [{'name': 'S1'}, {'name': 'G1'}]
for prod in ['S1', 'G1']:
    for cat in CATS:
        nodes.append({'name': f'{prod} · {cat}'})
for o in outcome_nodes:
    nodes.append({'name': o})

links = []
# product → category
for prod in ['S1', 'G1']:
    for cat in CATS:
        cnt = sum(1 for n in notes if n['product'] == prod and n['category'] == cat)
        if cnt > 0:
            links.append({'source': prod, 'target': f'{prod} · {cat}', 'value': cnt})
# category → outcome
for n in notes:
    prod = n['product']
    cat = n['category']
    # interact tier
    if n['interact'] > 80:
        it = '高互动(>80)'
    elif n['interact'] >= 30:
        it = '中互动(30-80)'
    else:
        it = '低互动(<30)'
    links.append({'source': f'{prod} · {cat}', 'target': it, 'value': 1})
    if n['store'] > 10:
        links.append({'source': f'{prod} · {cat}', 'target': '高进店(>10UV)', 'value': 1})
    if n['est_gmv'] > 0:
        links.append({'source': f'{prod} · {cat}', 'target': '有GMV转化', 'value': 1})
    else:
        links.append({'source': f'{prod} · {cat}', 'target': '无转化', 'value': 1})
# aggregate duplicate links
link_map = {}
for lk in links:
    key = (lk['source'], lk['target'])
    link_map[key] = link_map.get(key, 0) + lk['value']
links = [{'source': s, 'target': t, 'value': v} for (s, t), v in link_map.items()]

new_sankey = {'nodes': nodes, 'links': links}

# ── patch functions ──
def remove_balanced_div_block(html: str, start_idx: int) -> str:
    """Return html with the <div>...</div> block starting at start_idx removed."""
    j = html.find('<div', start_idx)
    if j == -1:
        return html
    depth = 0
    k = j
    while k < len(html):
        # find next tag
        lt = html.find('<', k)
        if lt == -1:
            break
        gt = html.find('>', lt)
        if gt == -1:
            break
        tag = html[lt+1:gt].strip()
        if tag.startswith('/'):
            name = tag[1:].split()[0]
            if name == 'div':
                depth -= 1
                if depth == 0:
                    return html[:j] + html[gt+1:]
        else:
            name = tag.split()[0]
            if name == 'div':
                depth += 1
        k = gt + 1
    return html

for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')

    # 1) remove pps-section HTML
    pps_start = h.find('<!-- ═══════ S1/G1 产品内容流动分析')
    if pps_start != -1:
        # find start of next section comment after it
        next_sec = h.find('<!-- ═══════', pps_start + 10)
        if next_sec == -1:
            next_sec = len(h)
        h = h[:pps_start] + h[next_sec:]

    # 2) remove pps CSS
    css_start = h.find('/* ── product split promo analysis ── */')
    if css_start != -1:
        css_end = h.find('}', css_start)
        # remove until after closing brace
        h = h[:css_start] + h[css_end+1:]

    # 3) remove pps JS block
    js_marker = 'window.init_promo_product_split = function()'
    js_start = h.find('<script>\n(function(){')
    # find the specific script that contains init_promo_product_split
    while js_start != -1:
        js_end = h.find('</script>', js_start)
        block = h[js_start:js_end]
        if js_marker in block:
            h = h[:js_start] + h[js_end+9:]
            break
        js_start = h.find('<script>\n(function(){', js_end)

    # 4) revert INIT wrapper to original
    old_init = "const INIT={'s1g1':typeof init_s1g1==='function'?init_s1g1:null,'promo':(typeof init_promo==='function'?function(){init_promo();if(typeof init_promo_product_split==='function')init_promo_product_split();}:null),"
    new_init = "const INIT={'s1g1':typeof init_s1g1==='function'?init_s1g1:null,'promo':typeof init_promo==='function'?init_promo:null,"
    if old_init in h:
        h = h.replace(old_init, new_init)

    # 5) replace local DATA.sankey inside init_promo
    m = re.search(r'function\s+init_promo\s*\(', h)
    if m:
        data_start = h.index('const DATA = {', m.end())
        # find the DATA block (balanced braces)
        brace = h.find('{', data_start)
        depth = 1
        j = brace + 1
        while j < len(h) and depth > 0:
            if h[j] == '{':
                depth += 1
            elif h[j] == '}':
                depth -= 1
            j += 1
        data_block = h[brace:j]
        d = json.loads(data_block)
        d['sankey'] = new_sankey
        new_data_block = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
        h = h[:brace] + new_data_block + h[j:]

    # 6) update桑基图 conclusion to product-aware
    # Replace the existing conclusion text within the桑基图 section
    old_conclusion = '''<div class="conclusion-box"><h4>桑基图结论</h4><ul><li><strong>金字塔(避坑) → 高互动 最粗管道</strong>：14篇中7篇达到高互动(>80)，是最稳定的互动收割类型</li><li><strong>"有GMV转化"的笔记仅占总量28%</strong>：72篇中仅约20篇产生了实际GMV，多数笔记停留在种草层</li><li><strong>其他种草 → 无转化 流量最大</strong>：24篇中多数进店和GMV为0 — 非标准化内容难以驱动转化</li><li><strong>图文横测+证言 → 有GMV转化 贡献最稳定</strong>：两类合计9篇产生GMV，远超其他类型</li></ul></div></div><!-- ═══════ 气泡图 ═══════ -->'''
    new_conclusion = '''<div class="conclusion-box"><h4>桑基图结论</h4><ul><li><strong>产品结构：S1 与 G1 流向差异明显</strong>：S1 大促攻略/图文横测两条管道较粗，G1 用户评论证言/图文横测/other 种草是主力，两类产品的高转化内容类型不同</li><li><strong>G1 的「有GMV转化」占比更高</strong>：G1 价格门槛低，用户评论证言和图文横测均产生较多 GMV；S1 则更依赖攻略/横测类决策型内容</li><li><strong>「无转化」仍是最大出口</strong>：两大产品的「其他种草」和「场景体验」多数流向无转化，说明非标准化场景内容难以直接收割</li><li><strong>高互动 ≠ 高转化</strong>：金字塔(避坑种草)在 S1/G1 均有不少高互动笔记，但转化为 GMV 的比例偏低，需要追加 CTA 或挂车优化</li></ul></div></div><!-- ═══════ 气泡图 ═══════ -->'''
    if old_conclusion in h:
        h = h.replace(old_conclusion, new_conclusion)
    else:
        print(f'  ⚠ {tgt.relative_to(ROOT)}: old桑基 conclusion not found, skipping conclusion update')

    tgt.write_text(h, encoding='utf-8')
    print(f'✓ patched {tgt.relative_to(ROOT)}')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')
