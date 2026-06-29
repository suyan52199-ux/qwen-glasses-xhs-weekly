#!/usr/bin/env python3
"""
R35: 金咖 618 促单分析按 S1 / G1 产品拆分：
- 内容分类 → 效果流向（桑基图）分产品
- 内容分类效率热力图 分产品
- 分类 ROI 与效率对比 分产品
TARGETS（硬规则）：docs dark + outputs/KOC铺量内容.html
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

# ── load jinka 72 notes ──
jdf = pd.read_excel('/Users/xiemila/Downloads/金咖618节点KOC促单汇总.xlsx', sheet_name='蒲公英源表', header=2)
notes = []
for _, r in jdf.iterrows():
    title = str(r.iloc[5]).strip() if pd.notna(r.iloc[5]) else ''
    if not title or title == 'nan':
        continue
    coop = str(r.iloc[13]) if pd.notna(r.iloc[13]) else ''
    product = 'S1' if 'S1' in coop else ('G1' if 'G1' in coop else '?')
    cost = num(r.iloc[16]) + num(r.iloc[17])
    reads = num(r.iloc[21])
    interact = num(r.iloc[28])
    store = num(r.iloc[123])
    search = num(r.iloc[125])
    notes.append({
        'title': title,
        'product': product,
        'category': classify_cat(title),
        'cost': cost,
        'reads': reads,
        'interact': interact,
        'store': store,
        'search': search,
    })

TOTAL_GMV = 320082.29
TOTAL_STORE = 9383.0
for n in notes:
    n['est_gmv'] = (n['store'] / TOTAL_STORE * TOTAL_GMV) if TOTAL_STORE > 0 else 0.0

def build_product_data(prod):
    arr = [n for n in notes if n['product'] == prod]
    stats = {}
    for cat in CATS:
        subset = [n for n in arr if n['category'] == cat]
        if not subset:
            stats[cat] = {'count': 0, 'cost': 0, 'reads': 0, 'interact': 0, 'store': 0, 'search': 0, 'gmv': 0,
                          'roi': 0, 'cpe': 0, 'cpm': 0, 'avg_interact': 0, 'avg_store': 0, 'avg_search': 0, 'store_rate': 0}
            continue
        count = len(subset)
        cost = sum(x['cost'] for x in subset)
        reads = sum(x['reads'] for x in subset)
        interact = sum(x['interact'] for x in subset)
        store = sum(x['store'] for x in subset)
        search = sum(x['search'] for x in subset)
        gmv = sum(x['est_gmv'] for x in subset)
        stats[cat] = {
            'count': count,
            'cost': round(cost, 2),
            'reads': round(reads, 2),
            'interact': round(interact, 2),
            'store': round(store, 2),
            'search': round(search, 2),
            'gmv': round(gmv, 2),
            'roi': round(gmv / cost, 2) if cost > 0 else 0,
            'cpe': round(cost / interact, 2) if interact > 0 else 0,
            'cpm': round(cost / reads * 1000, 2) if reads > 0 else 0,
            'avg_interact': round(interact / count, 2),
            'avg_store': round(store / count, 2),
            'avg_search': round(search / count, 2),
            'store_rate': round(store / reads * 100, 2) if reads > 0 else 0,
        }
    # sankey nodes & links
    target_nodes = ['高互动(>80)', '中互动(30-80)', '低互动(<30)', '高进店(>10UV)', '有GMV转化', '无转化']
    nodes = [{'name': cat} for cat in CATS] + [{'name': t} for t in target_nodes]
    links = []
    for n in arr:
        cat = n['category']
        # interact tier
        if n['interact'] > 80:
            it = '高互动(>80)'
        elif n['interact'] >= 30:
            it = '中互动(30-80)'
        else:
            it = '低互动(<30)'
        links.append({'source': cat, 'target': it, 'value': 1})
        if n['store'] > 10:
            links.append({'source': cat, 'target': '高进店(>10UV)', 'value': 1})
        if n['est_gmv'] > 0:
            links.append({'source': cat, 'target': '有GMV转化', 'value': 1})
        else:
            links.append({'source': cat, 'target': '无转化', 'value': 1})
    # aggregate duplicate links
    link_map = {}
    for lk in links:
        key = (lk['source'], lk['target'])
        link_map[key] = link_map.get(key, 0) + lk['value']
    links = [{'source': s, 'target': t, 'value': v} for (s, t), v in link_map.items()]

    # heatmap data: rows=categories, cols=metrics [count, avg_interact, avg_store, avg_search, roi]
    metrics = ['篇数', '篇均互动', '篇均进店', '篇均搜索', 'ROI']
    heatmap_data = []
    for i, cat in enumerate(CATS):
        s = stats[cat]
        vals = [s['count'], s['avg_interact'], s['avg_store'], s['avg_search'], s['roi']]
        for j, v in enumerate(vals):
            heatmap_data.append([j, i, v])
    return {
        'stats': stats,
        'sankey': {'nodes': nodes, 'links': links},
        'heatmap': {'cats': CATS, 'metrics': metrics, 'data': heatmap_data},
    }

PROMO_DATA = {'S1': build_product_data('S1'), 'G1': build_product_data('G1')}

# ── HTML / CSS ──
SECTION_HTML = '''
<!-- ═══════ S1/G1 产品内容流动分析 ═══════ -->
<div class="section pps-section">
  <h2 class="section-title">S1 / G1 产品内容流动分析</h2>
  <p class="section-sub">把 72 篇金咖促单笔记按产品拆为 S1(36篇) 与 G1(36篇)，分别看内容分类 → 互动/进店/转化的流向、效率热力图与 ROI 对比</p>

  <div class="pps-tabs">
    <button class="pps-tab active" data-pps="s1">千问 S1</button>
    <button class="pps-tab" data-pps="g1">千问 G1</button>
  </div>

  <div id="pps-s1" class="pps-panel active">
    <div class="pps-row">
      <div class="pps-chart"><h3>内容分类 → 效果流向</h3><div id="pps-s1-sankey" class="pps-container"></div></div>
    </div>
    <div class="pps-row">
      <div class="pps-chart"><h3>内容分类效率热力图</h3><div id="pps-s1-heatmap" class="pps-container"></div></div>
      <div class="pps-chart"><h3>分类 ROI 与效率对比</h3><div id="pps-s1-bar" class="pps-container"></div></div>
    </div>
  </div>

  <div id="pps-g1" class="pps-panel">
    <div class="pps-row">
      <div class="pps-chart"><h3>内容分类 → 效果流向</h3><div id="pps-g1-sankey" class="pps-container"></div></div>
    </div>
    <div class="pps-row">
      <div class="pps-chart"><h3>内容分类效率热力图</h3><div id="pps-g1-heatmap" class="pps-container"></div></div>
      <div class="pps-chart"><h3>分类 ROI 与效率对比</h3><div id="pps-g1-bar" class="pps-container"></div></div>
    </div>
  </div>
</div>
'''

CSS = '''
/* ── product split promo analysis ── */
.pps-section { margin-top: 28px; }
.pps-tabs { display: flex; gap: 10px; margin: 16px 0; }
.pps-tab { background: rgba(255,255,255,0.06); border: 1px solid rgba(148,163,184,0.2); color: #94a3b8; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-size: 14px; }
.pps-tab.active { background: linear-gradient(90deg,#22d3ee,#3b82f6); color: #0f172a; border-color: transparent; font-weight: 700; }
.pps-panel { display: none; }
.pps-panel.active { display: block; }
.pps-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.pps-row:first-child { grid-template-columns: 1fr; }
.pps-chart { background: rgba(15,23,42,0.6); border: 1px solid rgba(148,163,184,0.12); border-radius: 12px; padding: 14px; }
.pps-chart h3 { margin: 0 0 10px; font-size: 14px; color: #e2e8f0; }
.pps-container { width: 100%; height: 360px; }
@media (max-width: 900px) { .pps-row { grid-template-columns: 1fr !important; } }
'''

# ── JS ──
js_data = json.dumps(PROMO_DATA, ensure_ascii=False, separators=(',', ':'))
JS = f'''
<script>
(function(){{
  const PROMO_PRODUCT_SPLIT = {js_data};
  const colorMap = {{'图文横测':'#3b82f6','用户评论证言':'#10b981','金字塔(避坑种草)':'#ef4444','大促攻略':'#f59e0b','国补攻略':'#f97316','功能卖点':'#8b5cf6','场景体验':'#06b6d4','其他种草':'#64748b'}};

  function renderSankey(prod, id){{
    const d = PROMO_PRODUCT_SPLIT[prod].sankey;
    const chart = echarts.init(document.getElementById(id));
    const option = {{
      tooltip: {{ trigger: 'item', triggerOn: 'mousemove' }},
      series: [{{
        type: 'sankey', layout: 'none', emphasis: {{ focus: 'adjacency' }},
        data: d.nodes,
        links: d.links,
        top: 20, bottom: 20, left: 20, right: 120,
        lineStyle: {{ color: 'gradient', curveness: 0.5, opacity: 0.4 }},
        itemStyle: {{ borderWidth: 0 }},
        label: {{ color: '#cbd5e1', fontSize: 11 }}
      }}]
    }};
    chart.setOption(option);
    return chart;
  }}

  function renderHeatmap(prod, id){{
    const d = PROMO_PRODUCT_SPLIT[prod].heatmap;
    const chart = echarts.init(document.getElementById(id));
    const option = {{
      tooltip: {{ position: 'top', formatter: p => p.name + '<br/>' + d.metrics[p.value[0]] + ': ' + p.value[2] }},
      grid: {{ left: 100, right: 30, top: 10, bottom: 40 }},
      xAxis: {{ type: 'category', data: d.metrics, splitArea: {{ show: true }}, axisLabel: {{ color: '#94a3b8', fontSize: 11 }} }},
      yAxis: {{ type: 'category', data: d.cats, splitArea: {{ show: true }}, axisLabel: {{ color: '#cbd5e1', fontSize: 11 }} }},
      visualMap: {{ min: 0, max: 50, calculable: true, orient: 'horizontal', left: 'center', bottom: 0, inRange: {{ color: ['#1e293b','#22d3ee','#f59e0b'] }}, textStyle: {{ color: '#94a3b8' }} }},
      series: [{{ name: '效率', type: 'heatmap', data: d.data, label: {{ show: true, color: '#fff', fontSize: 10, formatter: p => p.value[2] >= 10000 ? (p.value[2]/10000).toFixed(1)+'w' : p.value[2] }}, itemStyle: {{ borderColor: '#0f172a', borderWidth: 1 }} }}]
    }};
    chart.setOption(option);
    return chart;
  }}

  function renderBar(prod, id){{
    const stats = PROMO_PRODUCT_SPLIT[prod].stats;
    const cats = Object.keys(stats);
    const rois = cats.map(c => stats[c].roi);
    const cpes = cats.map(c => stats[c].cpe);
    const counts = cats.map(c => stats[c].count);
    const chart = echarts.init(document.getElementById(id));
    const option = {{
      tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
      legend: {{ data: ['ROI','CPE','篇数'], textStyle: {{ color: '#94a3b8' }} }},
      grid: {{ left: 60, right: 60, top: 40, bottom: 80 }},
      xAxis: {{ type: 'category', data: cats, axisLabel: {{ color: '#cbd5e1', rotate: 30, fontSize: 10 }} }},
      yAxis: [{{ type: 'value', name: 'ROI', axisLabel: {{ color: '#94a3b8' }}, splitLine: {{ lineStyle: {{ color: '#1e293b' }} }} }},
              {{ type: 'value', name: 'CPE', axisLabel: {{ color: '#94a3b8' }}, splitLine: {{ show: false }} }}],
      series: [
        {{ name: 'ROI', type: 'bar', data: rois, itemStyle: {{ color: '#22d3ee', borderRadius: [4,4,0,0] }} }},
        {{ name: 'CPE', type: 'line', yAxisIndex: 1, data: cpes, lineStyle: {{ color: '#f59e0b', width: 2 }}, itemStyle: {{ color: '#f59e0b' }} }},
        {{ name: '篇数', type: 'scatter', data: counts, symbolSize: p => Math.max(6, p*2), itemStyle: {{ color: '#ef4444' }} }}
      ]
    }};
    chart.setOption(option);
    return chart;
  }}

  window.init_promo_product_split = function(){{
    ['s1','g1'].forEach(prod => {{
      renderSankey(prod, 'pps-'+prod+'-sankey');
      renderHeatmap(prod, 'pps-'+prod+'-heatmap');
      renderBar(prod, 'pps-'+prod+'-bar');
    }});
  }};

  document.querySelectorAll('.pps-tab').forEach(btn => {{
    btn.addEventListener('click', () => {{
      document.querySelectorAll('.pps-tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.pps-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const prod = btn.dataset.pps;
      document.getElementById('pps-'+prod).classList.add('active');
      setTimeout(() => {{ echarts.getInstanceByDom(document.getElementById('pps-'+prod+'-sankey')).resize(); echarts.getInstanceByDom(document.getElementById('pps-'+prod+'-heatmap')).resize(); echarts.getInstanceByDom(document.getElementById('pps-'+prod+'-bar')).resize(); }}, 50);
    }});
  }};
}})();
</script>
'''

for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')
    if 'pps-section' in h:
        print(f'already injected: {tgt}')
        continue

    # insert CSS before last </style>
    h = h.replace('</style>', CSS + '</style>', 1)

    # insert HTML section before panel-promo footer
    anchor = '<footer>618促单 · 小红书图文专项数据分析'
    assert h.count(anchor) == 1, f'{tgt}: promo footer anchor count != 1'
    h = h.replace(anchor, SECTION_HTML + '\n  ' + anchor)

    # insert JS before global final </script></body></html>
    # place right before </body>
    h = h.replace('</body>', JS + '\n</body>')

    # wrap INIT['promo'] to also call product split
    init_line = "const INIT={'s1g1':typeof init_s1g1==='function'?init_s1g1:null,'promo':typeof init_promo==='function'?init_promo:null,"
    if init_line in h:
        new_init = "const INIT={'s1g1':typeof init_s1g1==='function'?init_s1g1:null,'promo':(typeof init_promo==='function'?function(){init_promo();if(typeof init_promo_product_split==='function')init_promo_product_split();}:null),"
        h = h.replace(init_line, new_init)
    else:
        print(f'  ⚠ INIT line not found in {tgt}, skipping wrapper')

    tgt.write_text(h, encoding='utf-8')
    print(f'✓ {tgt.relative_to(ROOT)}: injected')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')

# save summary
summary = {prod: PROMO_DATA[prod]['stats'] for prod in PROMO_DATA}
open('outputs/promo_product_split_summary.json', 'w', encoding='utf-8').write(json.dumps(summary, ensure_ascii=False, indent=1))
print('✓ saved outputs/promo_product_split_summary.json')
