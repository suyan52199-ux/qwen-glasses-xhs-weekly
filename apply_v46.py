#!/usr/bin/env python3
"""
R46: 全量 786 篇统一视图重构 + S1/G1/KOL/KOC 全量更新 + 移除测试板块
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

XLSX_MAIN = Path('/Users/xiemila/Desktop/4-6月koc、kol笔记效果(2).xlsx')
XLS_RUHAN = Path('/Users/xiemila/Desktop/【1】如涵国补方向6.29数据汇总.xls')
XLSX_JINKA = Path('/Users/xiemila/Downloads/金咖koc内容.xlsx')

BUDGET = 950000
ROLES = ['KOC', 'KOL']

# ── helpers ──
def safe_div(a, b): return a / b if b else 0

def fmt_num(n, d=0):
    if d:
        return f'{n:,.{d}f}'
    return f'{int(round(n)):,}'

def fmt_wan(n):
    if n >= 10000:
        return f'{n/10000:.1f}万'
    return f'{n:,.0f}'

def extract_note_id(url):
    if not isinstance(url, str): return ''
    for pat in [r'/explore/([0-9a-f]+)', r'/discovery/item/([0-9a-f]+)']:
        m = re.search(pat, url)
        if m: return m.group(1)
    return ''

# ── direction mapping ──
def map_main_direction(direction: str) -> tuple:
    d = str(direction)
    if 'S1vs' in d or 'S1 vs' in d or 'S1纵测' in d:
        return 'S1', 'S1纵测'
    if 'S1竞品多测' in d or ('S1' in d and '横测' in d):
        return 'S1', 'S1横测'
    if 'G1抠图横测' in d or ('G1' in d and '横测' in d):
        return 'G1', 'G1横测'
    if 'G1选购攻略' in d or '选购攻略' in d:
        return 'G1', 'G1选购攻略'
    if '520' in d:
        return 'S1', 'S1热点520'
    if '618' in d:
        return 'S1', 'S1热点618'
    if '场景对比' in d:
        return 'S1', 'S1热点场景对比'
    if '明星' in d:
        return 'S1', 'S1热点明星'
    if '读书日' in d:
        return 'S1', 'S1热点读书日'
    if d.startswith('S1'): return 'S1', 'S1横测'
    if d.startswith('G1'): return 'G1', 'G1横测'
    return 'G1', 'G1选购攻略'

# ── load main pool ──
koc_df = pd.read_excel(XLSX_MAIN, sheet_name='数据底表').fillna(0)
num_cols = ['总消耗','进店UV','阅读量','互动量','搜索进店uv','GMV','ROI']
for c in num_cols:
    koc_df[c] = pd.to_numeric(koc_df[c], errors='coerce').fillna(0)
link_dir = koc_df[koc_df['方向'] != 0].drop_duplicates('发布返链').set_index('发布返链')['方向'].to_dict()
koc_df['方向'] = koc_df.apply(lambda r: link_dir.get(r['发布返链'], r['方向']), axis=1)
koc_df = koc_df.loc[koc_df.groupby('发布返链')['GMV'].idxmax()].reset_index(drop=True)
koc_df = koc_df[(koc_df['方向'] != 0) & (koc_df['发布返链'].astype(str).str.startswith('http'))].reset_index(drop=True)

main_rows = []
for _, r in koc_df.iterrows():
    prod, dire = map_main_direction(str(r['方向']))
    url = str(r['发布返链']) if r['发布返链'] else ''
    main_rows.append({
        'product': prod, 'direction': dire, 'role': 'KOC',
        'name': str(r['昵称']) if r['昵称'] else '',
        'count': 1, 'cost': float(r['总消耗']), 'gmv': float(r['GMV']),
        'store': int(r['进店UV']), 'search': int(r['搜索进店uv']),
        'interact': int(r['互动量']), 'reads': int(r['阅读量']),
        'roi': float(r['ROI']), 'url': url, 'noteId': extract_note_id(url),
        'title': f"{dire} | {r['昵称']}",
        'source_pool': 'main',
    })

kol_df = pd.read_excel(XLSX_MAIN, sheet_name='kol（数据截止到6.28）').fillna(0)
num_cols_kol = ['总消耗','进店uv','阅读量','互动量','搜索uv','gmv','roi']
for c in num_cols_kol:
    kol_df[c] = pd.to_numeric(kol_df[c], errors='coerce').fillna(0)
for _, r in kol_df.iterrows():
    url = str(r['内容链接']) if r['内容链接'] else ''
    main_rows.append({
        'product': 'G1', 'direction': 'G1横测', 'role': 'KOL',
        'name': str(r['达人昵称']) if r['达人昵称'] else '',
        'count': 1, 'cost': float(r['总消耗']), 'gmv': float(r['gmv']),
        'store': int(r['进店uv']), 'search': int(r['搜索uv']),
        'interact': int(r['互动量']), 'reads': int(r['阅读量']),
        'roi': float(r['roi']), 'url': url, 'noteId': extract_note_id(url),
        'title': f"G1横测 | {r['达人昵称']}",
        'source_pool': 'main',
    })

main_df = pd.DataFrame(main_rows)

# ── load test pools ──
ruhan_df = pd.read_excel(XLS_RUHAN, header=0).fillna(0)
jinka_df = pd.read_excel(XLSX_JINKA, header=0).fillna(0)

def add_test_rows(df, source):
    out = []
    for _, r in df.iterrows():
        prod_raw = str(r.get('产品', '')).upper()
        prod = None
        if 'S1' in prod_raw: prod = 'S1'
        elif 'G1' in prod_raw: prod = 'G1'
        if prod is None: continue
        if source == 'ruhan':
            dire = f'{prod}国补攻略'
        else:
            dire = f'{prod}横测'
        cost = float(r.get('总消耗', 0) or 0)
        gmv = float(r.get('gmv', 0) or 0)
        out.append({
            'product': prod, 'direction': dire, 'role': 'KOC',
            'name': str(r.get('达人昵称', '')) if r.get('达人昵称') else '',
            'count': 1, 'cost': cost, 'gmv': gmv,
            'store': int(r.get('进店uv', 0) or 0),
            'search': int(r.get('搜索uv', 0) or 0),
            'interact': int(r.get('互动量', 0) or 0),
            'reads': int(r.get('阅读量', 0) or 0),
            'roi': safe_div(gmv, cost),
            'url': str(r.get('内容链接', '')) if r.get('内容链接') else '',
            'noteId': extract_note_id(str(r.get('内容链接', ''))),
            'title': f"{dire} | {r.get('达人昵称', '')}",
            'source_pool': source,
        })
    return out

test_rows = add_test_rows(ruhan_df, 'ruhan') + add_test_rows(jinka_df, 'jinka')
full_rows = main_rows + test_rows
full_df = pd.DataFrame(full_rows)

print('full shape', full_df.shape)
print('role', full_df['role'].value_counts().to_dict())
print('product', full_df['product'].value_counts().to_dict())

# ── summary helpers ──
def summary_from(s):
    count = int(s['count'].sum())
    return {
        'count': count,
        'total_cost': round(float(s['cost'].sum()), 3),
        'total_gmv': round(float(s['gmv'].sum()), 3),
        'total_store': int(s['store'].sum()),
        'total_interact': int(s['interact'].sum()),
        'total_search': int(s['search'].sum()),
        'total_reads': int(s['reads'].sum()),
        'roi': round(safe_div(s['gmv'].sum(), s['cost'].sum()), 2),
        'with_gmv': int((s['gmv'] > 0).sum()),
        'with_gmv_pct': round(100 * (s['gmv'] > 0).sum() / count, 1) if count else 0,
        'avg_cost': round(safe_div(s['cost'].sum(), count)),
        'avg_interact': round(safe_div(s['interact'].sum(), count)),
        'avg_store': round(safe_div(s['store'].sum(), count), 1),
        'avg_search': round(safe_div(s['search'].sum(), count), 1),
        'avg_gmv': round(safe_div(s['gmv'].sum(), count)),
        'avg_reads': round(safe_div(s['reads'].sum(), count)),
    }

def add_label(d, label):
    d['label'] = label
    return d

overall = {'s1': add_label(summary_from(full_df[full_df['product']=='S1']), 'S1'),
           'g1': add_label(summary_from(full_df[full_df['product']=='G1']), 'G1')}
koc = {'s1': add_label(summary_from(full_df[(full_df['role']=='KOC') & (full_df['product']=='S1')]), 'S1·KOC'),
       'g1': add_label(summary_from(full_df[(full_df['role']=='KOC') & (full_df['product']=='G1')]), 'G1·KOC')}
kol_s1 = None
kol_g1 = add_label(summary_from(full_df[(full_df['role']=='KOL') & (full_df['product']=='G1')]), 'G1·KOL')
kol = {'s1': kol_s1, 'g1': kol_g1}

kk_summary = {
    'koc_overall': add_label(summary_from(full_df[full_df['role']=='KOC']), 'KOC整体'),
    'kol_overall': add_label(summary_from(full_df[full_df['role']=='KOL']), 'KOL整体'),
    'koc_s1': add_label(summary_from(full_df[(full_df['role']=='KOC') & (full_df['product']=='S1')]), 'S1·KOC'),
    'koc_g1': add_label(summary_from(full_df[(full_df['role']=='KOC') & (full_df['product']=='G1')]), 'G1·KOC'),
    'kol_g1': add_label(summary_from(full_df[(full_df['role']=='KOL') & (full_df['product']=='G1')]), 'G1·KOL'),
}

# direction breakdowns
def build_dirs(product, role=None):
    if role:
        sub = full_df[(full_df['product']==product) & (full_df['role']==role)]
    else:
        sub = full_df[full_df['product']==product]
    agg = sub.groupby('direction').agg({'count':'sum','cost':'sum','gmv':'sum','store':'sum','interact':'sum','search':'sum','reads':'sum'}).reset_index()
    rows = []
    for _, r in agg.iterrows():
        count = int(r['count'])
        if count == 0: continue
        rows.append({
            '内容方向': r['direction'],
            '总消耗': round(float(r['cost']), 3),
            'gmv': round(float(r['gmv']), 3),
            '进店uv': int(r['store']),
            '互动量': int(r['interact']),
            '搜索uv': int(r['search']),
            '阅读量': int(r['reads']),
            'count': count,
            'roi': round(safe_div(r['gmv'], r['cost']), 2),
            'avg_interact': round(safe_div(r['interact'], count)),
            'avg_store': round(safe_div(r['store'], count), 1),
            'avg_search': round(safe_div(r['search'], count), 1),
            'avg_gmv': round(safe_div(r['gmv'], count)),
            'avg_cost': round(safe_div(r['cost'], count)),
        })
    rows = sorted(rows, key=lambda x: x['roi'], reverse=True)
    return rows

s1_dirs = build_dirs('S1', 'KOC')
g1_dirs = build_dirs('G1')

# top lists
def build_top(product, by, n=10):
    sub = full_df[full_df['product']==product].copy()
    sub = sub.sort_values(by, ascending=False).head(n)
    out = []
    for _, r in sub.iterrows():
        out.append({
            'name': r['name'], 'direction': r['direction'], 'product': r['product'], 'source': r['role'],
            'url': r['url'], 'noteId': r['noteId'], 'title': r['title'],
            'roi': round(float(r['roi']), 2), 'gmv': round(float(r['gmv']), 2),
            'cost': round(float(r['cost']), 3), 'interact': float(r['interact']), 'store': float(r['store']),
        })
    return out

s1_top_roi = build_top('S1', 'roi')
s1_top_gmv = build_top('S1', 'gmv')
s1_top_interact = build_top('S1', 'interact')
s1_top_store = build_top('S1', 'store')
g1_top_roi = build_top('G1', 'roi')
g1_top_gmv = build_top('G1', 'gmv')
g1_top_interact = build_top('G1', 'interact')
g1_top_store = build_top('G1', 'store')

# heatmap
direction_order = sorted(full_df['direction'].unique().tolist(), key=lambda d: (not d.startswith('S1'), d))
heatmap_roi = []
heatmap_gmv = []
for _, r in full_df.groupby(['role','direction']).agg({'count':'sum','cost':'sum','gmv':'sum'}).reset_index().iterrows():
    if r['direction'] not in direction_order: continue
    ri = ROLES.index(r['role'])
    di = direction_order.index(r['direction'])
    roi = round(safe_div(r['gmv'], r['cost']), 2)
    heatmap_roi.append([ri, di, roi, int(r['count'])])
    heatmap_gmv.append([ri, di, round(float(r['gmv']), 2), int(r['count'])])

# sankey
outcome_nodes = ['高ROI(≥10x)', '中ROI(3-10x)', '低ROI(<3x)']
sankey_nodes = [{'name':'KOC'},{'name':'KOL'},{'name':'S1'},{'name':'G1'}]
for d in direction_order:
    sankey_nodes.append({'name':d})
for o in outcome_nodes:
    sankey_nodes.append({'name':o})
sankey_links = []
for (role, prod), g in full_df.groupby(['role','product']):
    cnt = int(g['count'].sum())
    if cnt: sankey_links.append({'source':role,'target':prod,'value':cnt})
for (prod, dire), g in full_df.groupby(['product','direction']):
    cnt = int(g['count'].sum())
    if cnt: sankey_links.append({'source':prod,'target':dire,'value':cnt})
for dire, g in full_df.groupby('direction'):
    cnt = int(g['count'].sum())
    if cnt == 0: continue
    roi = safe_div(g['gmv'].sum(), g['cost'].sum())
    if roi >= 10: out = '高ROI(≥10x)'
    elif roi >= 3: out = '中ROI(3-10x)'
    else: out = '低ROI(<3x)'
    sankey_links.append({'source':dire,'target':out,'value':cnt})

# title_analysis
titles = []
for _, r in full_df.iterrows():
    titles.append({
        'name': r['name'], 'direction': r['direction'], 'product': r['product'], 'source': r['role'],
        'url': r['url'], 'noteId': r['noteId'], 'gmv': round(float(r['gmv']), 2), 'roi': round(float(r['roi']), 2),
        'cost': round(float(r['cost']), 3), 'interact': float(r['interact']), 'store': float(r['store']),
        'title': r['title'], 'images': [], 'cover': None, 'note_type': 'image',
        'elements': {k: False for k in ['否定/警告词','数字','竖线分隔','问句','品牌名','品类词','对比/横评','真实感','强情绪','推荐句式','emoji','痛点词','价格词','功效词','场景词']},
    })
top_s1_gmv = sorted([t for t in titles if t['product']=='S1'], key=lambda x: x['gmv'], reverse=True)[:5]
top_g1_gmv = sorted([t for t in titles if t['product']=='G1'], key=lambda x: x['gmv'], reverse=True)[:5]
title_analysis = {'titles': titles, 'top_titles_s1_gmv': top_s1_gmv, 'top_titles_g1_gmv': top_g1_gmv}

# preserve old element stats to keep lift charts rendering
try:
    cur_html = TARGETS[0].read_text(encoding='utf-8')
    m = re.search(r'function init_s1g1\(\)\{try\{const DATA = ', cur_html)
    if m:
        start = cur_html.find('{', m.end())
        depth = 1; j = start + 1
        while j < len(cur_html) and depth > 0:
            if cur_html[j] == '{': depth += 1
            elif cur_html[j] == '}': depth -= 1
            j += 1
        cur_data = json.loads(cur_html[start:j])
        for k in ['s1_element_stats', 'g1_element_stats', 'elements_list']:
            if k in cur_data.get('title_analysis', {}):
                title_analysis[k] = cur_data['title_analysis'][k]
except Exception as e:
    print('warn: could not preserve element stats:', e)

new_data = {
    'overall': overall,
    'koc': koc,
    'kol': kol,
    's1_dirs': s1_dirs,
    'g1_dirs': g1_dirs,
    's1_top_roi': s1_top_roi,
    's1_top_gmv': s1_top_gmv,
    's1_top_interact': s1_top_interact,
    's1_top_store': s1_top_store,
    'g1_top_roi': g1_top_roi,
    'g1_top_gmv': g1_top_gmv,
    'g1_top_interact': g1_top_interact,
    'g1_top_store': g1_top_store,
    'heatmap_directions': direction_order,
    'heatmap_roles': ROLES,
    'heatmap_roi': heatmap_roi,
    'heatmap_gmv': heatmap_gmv,
    'sankey_nodes': sankey_nodes,
    'sankey_links': sankey_links,
    'kk_summary': kk_summary,
    'title_analysis': title_analysis,
}

print('s1_dirs', [(d['内容方向'], d['count'], d['roi']) for d in s1_dirs])
print('g1_dirs', [(d['内容方向'], d['count'], d['roi']) for d in g1_dirs])

# ── account type analysis (full 752 KOC) ──
# manual overrides from historical top examples
manual_type = {}
for at_name, bloggers in json.load(open('koc_account_type_top.json')).items():
    for b in bloggers:
        manual_type[b['达人昵称']] = at_name

def classify_account(nick, ruhan_type=''):
    if nick in manual_type:
        return manual_type[nick]
    # ruhan explicit type mapping
    if ruhan_type:
        rt = str(ruhan_type)
        if rt in ['母婴']:
            return '👶家庭亲子'
        if rt in ['生活记录', '好物分享', '探店分享']:
            return '🌿生活分享'
        if rt in ['大字报']:
            return '👤泛人格素人'
    s = str(nick).lower()
    if any(k in s for k in ['数码','科技','测评','评测','3c','手机','硬件','电子','geek','数码控','型型数码','数码莓','柚子数码','搞机','极客']):
        return '🔬数码科技测评'
    if any(k in s for k in ['猫','狗','宠','金毛','喵','汪','铲屎官','喵星人','狗子','萌宠']):
        return '🐱萌宠'
    if any(k in s for k in ['奶茶','吃货','零食','咖啡','蛋糕','锅巴','猪脚饭','美食','吃喝','面包','甜点','糖水','烤肉','火锅','料理','厨房','干饭']):
        return '🍜美食吃货'
    if any(k in s for k in ['学姐','学长','学习','读书','备考','考研','英语','校园','study','大学生']):
        return '📚文艺学习'
    if any(k in s for k in ['妆','穿搭','护肤','造型','ootd','潮流','美妆','chic','fashion']):
        return '👗时尚颜值美妆'
    if any(k in s for k in ['妈','爸','娃','育儿','亲子','儿童','宝贝','母婴','宝宝','辣妈','奶爸']):
        return '👶家庭亲子'
    if any(k in s for k in ['大厂','职场','摸鱼','财经','打工','打工人','工资','搞钱','搬砖']):
        return '💼职场财经'
    if any(k in s for k in ['生活','家居','宅','研究所','旅行','日常','vlog','好物','分享']):
        return '🌿生活分享'
    return '👤泛人格素人'

koc_df_full = full_df[full_df['role']=='KOC'].copy()
koc_df_full['account_type'] = koc_df_full.apply(
    lambda r: classify_account(r['name'], r.get('账号类型', '') if '账号类型' in r else ''), axis=1)

actype_stats = []
actype_top = {}
for at_name, group in koc_df_full.groupby('account_type'):
    notes = int(group['count'].sum())
    cost = float(group['cost'].sum())
    gmv = float(group['gmv'].sum())
    interact = int(group['interact'].sum())
    reads = int(group['reads'].sum())
    store = int(group['store'].sum())
    search = int(group['search'].sum())
    roi = safe_div(gmv, cost)
    cpe = safe_div(cost, interact) if interact else 0
    cpm = safe_div(cost * 1000, reads) if reads else 0
    gmv_per_note = safe_div(gmv, notes)
    cost_per_note = safe_div(cost, notes)
    interact_per_note = safe_div(interact, notes)
    shop_per_note = safe_div(store, notes)
    cvr_shop = safe_div(store, reads) * 100 if reads else 0
    actype_stats.append({
        'account_type': at_name, 'notes': notes, 'cost': cost, 'gmv': gmv,
        'interaction': interact, 'read': reads, 'shop_uv': store, 'search_uv': search,
        'roi': round(roi, 2), 'cpe': round(cpe, 2), 'cpm': round(cpm, 2),
        'gmv_per_note': round(gmv_per_note), 'cost_per_note': round(cost_per_note),
        'interact_per_note': round(interact_per_note, 1), 'shop_per_note': round(shop_per_note, 1),
        'cvr_shop': round(cvr_shop, 2),
    })
    top5 = group.sort_values('gmv', ascending=False).head(5)
    actype_top[at_name] = []
    for _, r in top5.iterrows():
        actype_top[at_name].append({
            '达人昵称': r['name'], '内容方向': r['direction'], 'product': r['product'],
            'gmv': r['gmv'], 'roi': r['roi'],
        })

actype_stats = sorted(actype_stats, key=lambda x: x['roi'], reverse=True)
print('account types', [(s['account_type'], s['notes'], s['roi']) for s in actype_stats])

# total overview for panel-mega
total = summary_from(full_df)
total['budget'] = BUDGET
total['budget_roi'] = round(safe_div(total['total_gmv'], BUDGET), 2)

# data for mega direction charts
mega_dir_s1 = [{'方向': d['内容方向'], '篇数': d['count'], 'GMV': d['gmv'], 'ROI': d['roi']} for d in s1_dirs]
mega_dir_g1 = [{'方向': d['内容方向'], '篇数': d['count'], 'GMV': d['gmv'], 'ROI': d['roi']} for d in g1_dirs]

# mega heatmap: product x direction ROI
mega_heatmap_dirs = direction_order
mega_heatmap_data = []
for _, r in full_df.groupby(['product','direction']).agg({'count':'sum','cost':'sum','gmv':'sum'}).reset_index().iterrows():
    pi = 0 if r['product']=='S1' else 1
    di = mega_heatmap_dirs.index(r['direction'])
    mega_heatmap_data.append([pi, di, round(safe_div(r['gmv'], r['cost']), 2), int(r['count'])])

# helper for direction chart arrays
def dir_chart_data(rows):
    cats = [r['内容方向'] for r in rows]
    return {
        'categories': cats,
        'roi': [r['roi'] for r in rows],
        'gmv': [round(r['gmv']) for r in rows],
        'count': [r['count'] for r in rows],
    }

# ── HTML patching ──
for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')

    # 1) replace panel-s1g1 DATA block
    pat = r'(function init_s1g1\(\)\{try\{const DATA = )(\{.*?\})(;\s*function switchTopTab)'
    def data_repl(m):
        try:
            old = json.loads(m.group(2))
        except Exception as e:
            print('parse err', e); return m.group(0)
        old.update(new_data)
        return m.group(1) + json.dumps(old, ensure_ascii=False, separators=(',', ':')) + m.group(3)
    h2 = re.sub(pat, data_repl, h, count=1, flags=re.DOTALL)
    if h2 == h:
        print('WARN: panel-s1g1 DATA not replaced in', tgt)
    h = h2

    # 2) replace panel-s1g1 header
    h = re.sub(
        r'<header><h1>千问 S1 vs G1 KOC铺量效率分析</h1><p>.*?</p></header>',
        f'<header><h1>千问 S1 vs G1 全量效率分析</h1><p>4-6月 · 全量 786 篇（KOC {fmt_num(kk_summary["koc_overall"]["count"])} + KOL {fmt_num(kk_summary["kol_overall"]["count"])}） · S1 {fmt_num(overall["s1"]["count"])} 篇 · G1 {fmt_num(overall["g1"]["count"])} 篇 · 数据截止6.28</p></header>',
        h, count=1, flags=re.DOTALL)

    # helper values
    s1 = overall['s1']; g1 = overall['g1']
    koc_overall = kk_summary['koc_overall']; kol_overall = kk_summary['kol_overall']

    # 3) replace first section: 总览 S1 vs G1
    first_section = f'''<div class="section">
<h2 class="section-title">第一层：S1 vs G1 整体效率对比</h2>
<p class="section-sub">全量 786 篇口径 · 主池 634 篇 + 如涵 80 篇 + 金咖 72 篇已合并</p>
<div class="product-row">
  <div class="product-card s1">
    <h3>千问 S1 <span class="badge">带屏旗舰款 · {fmt_num(s1['count'])}篇</span></h3>
    <p class="sub">KOC {fmt_num(koc['s1']['count'])}篇 · 无 KOL · 整体 ROI {s1['roi']:.2f}</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(s1['total_cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(s1['total_gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{s1['roi']:.2f}x</div><div class="l">整体ROI</div></div>
      <div class="stat-item"><div class="v">{fmt_num(s1['total_store'])}</div><div class="l">进店UV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(s1['total_search'])}</div><div class="l">搜索UV</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(s1['avg_gmv'])}</div><div class="l">篇均GMV</div></div>
    </div>
  </div>
  <div class="product-card g1">
    <h3>千问 G1 <span class="badge">轻量音频款 · {fmt_num(g1['count'])}篇</span></h3>
    <p class="sub">KOC {fmt_num(koc['g1']['count'])}篇 + KOL {fmt_num(kol['g1']['count'])}篇 · 整体 ROI {g1['roi']:.2f}</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(g1['total_cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(g1['total_gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{g1['roi']:.2f}x</div><div class="l">整体ROI</div></div>
      <div class="stat-item"><div class="v">{fmt_num(g1['total_store'])}</div><div class="l">进店UV</div></div>
      <div class="stat-item"><div class="v">{fmt_num(g1['total_search'])}</div><div class="l">搜索UV</div></div>
      <div class="stat-item"><div class="v">¥{fmt_num(g1['avg_gmv'])}</div><div class="l">篇均GMV</div></div>
    </div>
  </div>
</div>
<div class="chart-container"><h3>S1 vs G1 核心指标对比</h3><div id="product-vs" class="chart-box short"></div></div>
<div class="conclusion-box success">
  <h4>第一层结论 · S1 vs G1（全量 786 篇口径）</h4>
  <ul>
    <li><strong>S1 是高客单效率款</strong>：{fmt_num(s1['count'])} 篇产出 {fmt_wan(s1['total_gmv'])} GMV，整体 ROI {s1['roi']:.2f}×，篇均 GMV ¥{fmt_num(s1['avg_gmv'])}，显著高于 G1</li>
    <li><strong>G1 是流量基本盘</strong>：{fmt_num(g1['count'])} 篇（含 KOL {fmt_num(kol['g1']['count'])} 篇）产出 {fmt_wan(g1['total_gmv'])}，整体 ROI {g1['roi']:.2f}×，覆盖面广但单篇产出低于 S1</li>
    <li><strong>KOC 效率高于 KOL</strong>：KOC {fmt_num(koc_overall['count'])} 篇 ROI {koc_overall['roi']:.2f}×，KOL {fmt_num(kol_overall['count'])} 篇 ROI {kol_overall['roi']:.2f}×</li>
    <li><strong>S1 无 KOL 投放</strong>：{fmt_num(s1['count'])} 篇 S1 全部由 KOC 执行，纵测/读书日/横测是高 ROI 主航道</li>
    <li><strong>G1 应控制 KOL 占比并复制 S1 高 ROI 方向</strong>：KOL 全部压在 G1 横测，可拓展到 S1 已验证的纵测/读书日/用户证言方向</li>
  </ul>
</div>
</div>'''
    h = re.sub(
        r'<!--\s*═══ 总览：S1 vs G1 ═══\s*--><div class="section">.*?(?=<!--\s*═══ S1 细分 ═══\s*-->)',
        f'<!-- ═══ 总览：S1 vs G1 ═══ -->{first_section}',
        h, count=1, flags=re.DOTALL)

    # 4) replace S1 direction section content (keep container id)
    s1_top3 = s1_dirs[:3]
    s1_low = [d for d in s1_dirs if d['roi'] < 3]
    s1_section = f'''<div class="section">
<h2 class="section-title s1">第二层：S1 内容方向细分</h2>
<p class="section-sub">S1 共 {len(s1_dirs)} 个内容方向，合并后如涵国补方向纳入统计</p>
<div class="chart-container"><h3>S1 内容方向 ROI / GMV / 篇数</h3><div id="s1-dir-chart" class="chart-box"></div></div>
<div class="conclusion-box">
  <h4>S1 方向效率结论（全量 786）</h4>
  <ul>
    <li><strong>S1纵测 = 王炸级方向</strong>：仅 {s1_dirs[0]['count']} 篇贡献 ¥{fmt_wan(s1_dirs[0]['gmv'])} GMV，ROI {s1_dirs[0]['roi']:.2f}× — 单一产品深度内容效率最高</li>
    <li><strong>S1横测 = 稳定主力</strong>：{s1_dirs[1]['count']} 篇贡献 ¥{fmt_wan(s1_dirs[1]['gmv'])} GMV，ROI {s1_dirs[1]['roi']:.2f}× — 标准化横测内容性价比稳定，可量铺</li>
    <li><strong>S1热点读书日 = 借势成功典范</strong>：{s1_dirs[2]['count']} 篇 ROI {s1_dirs[2]['roi']:.2f}×，4.23 读书日借势匹配 S1 阅读类卖点</li>
    <li><strong>S1国补攻略（如涵合并）效率偏低</strong>：{next((d['count'] for d in s1_dirs if d['内容方向']=='S1国补攻略'),0)} 篇 ROI {next((d['roi'] for d in s1_dirs if d['内容方向']=='S1国补攻略'),0):.2f}× — 促销/国补类内容需强化搜索承接与钩子结构</li>
    <li><strong>节点/明星类继续停投或前置</strong>：520/618/场景对比/明星 ROI 均低于 3，明星方向 ROI {next((d['roi'] for d in s1_dirs if d['内容方向']=='S1热点明星'),0):.2f}×，建议停投；节点类需提前 2-4 周铺设</li>
  </ul>
</div>
</div>'''
    h = re.sub(
        r'<!--\s*═══ S1 细分 ═══\s*--><div class="section">.*?(?=<!--\s*═══ G1 细分 ═══\s*-->)',
        f'<!-- ═══ S1 细分 ═══ -->{s1_section}',
        h, count=1, flags=re.DOTALL)

    # 5) replace G1 direction section content
    g1_section = f'''<div class="section">
<h2 class="section-title g1">第三层：G1 内容方向细分</h2>
<p class="section-sub">G1 共 {len(g1_dirs)} 个方向，横测占比近 7 成</p>
<div class="chart-container"><h3>G1 内容方向 ROI / GMV / 篇数</h3><div id="g1-dir-chart" class="chart-box short"></div></div>
<div class="conclusion-box">
  <h4>G1 方向效率结论（全量 786）</h4>
  <ul>
    <li><strong>G1横测是绝对主力</strong>：{g1_dirs[0]['count']} 篇贡献 ¥{fmt_wan(g1_dirs[0]['gmv'])} GMV，占 G1 总 GMV 的 {safe_div(g1_dirs[0]["gmv"], g1["total_gmv"])*100:.0f}%，ROI {g1_dirs[0]['roi']:.2f}×</li>
    <li><strong>G1选购攻略效率偏低</strong>：{g1_dirs[1]['count']} 篇 ROI {g1_dirs[1]['roi']:.2f}×，篇均 GMV ¥{fmt_num(g1_dirs[1]['avg_gmv'])} — 建议砍量或改为横测结构</li>
    <li><strong>G1国补攻略（如涵合并）待验证</strong>：{g1_dirs[2]['count']} 篇 ROI {g1_dirs[2]['roi']:.2f}×，样本小，需控制成本并复制 G1 横测标题公式</li>
    <li><strong>建议</strong>：G1 继续放大横测，加测 S1 已验证的「纵测/读书日/用户证言」方向，摆脱单一方向依赖</li>
  </ul>
</div>
</div>'''
    h = re.sub(
        r'<!--\s*═══ G1 细分 ═══\s*--><div class="section">.*?(?=<!--\s*═══ 标题元素分析 ═══\s*-->)',
        f'<!-- ═══ G1 细分 ═══ -->{g1_section}',
        h, count=1, flags=re.DOTALL)

    # 6) replace KOL vs KOC section
    koc_card = kk_summary['koc_overall']
    kol_card = kk_summary['kol_overall']
    kol_vs_koc = f'''<div class="section">
<h2 class="section-title">第八层：KOL vs KOC 身份维度核心结论</h2>
<p class="section-sub">全量 {fmt_num(koc_card['count'])} KOC + {fmt_num(kol_card['count'])} KOL · 身份效率结构差异巨大</p>
<div class="product-row">
  <div class="product-card" style="background: linear-gradient(135deg, #0a1f4d 0%, #1a56db22 100%); border: 1px solid #1a56db;">
    <h3 style="color:#5b9aff">KOC 中腰部铺量 <span class="badge">{fmt_num(koc_card['count'])}篇 · ROI {koc_card['roi']:.2f}</span></h3>
    <p class="sub">主力铺量 · 单篇成本¥{fmt_num(koc_card['avg_cost'])} · 篇均互动{fmt_num(koc_card['avg_interact'])} · {koc_card['with_gmv_pct']:.0f}%笔记有转化</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(koc_card['total_cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(koc_card['total_gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{koc_card['roi']:.2f}x</div><div class="l">整体ROI</div></div>
    </div>
  </div>
  <div class="product-card" style="background: linear-gradient(135deg, #4d0f1a 0%, #ff6b6b22 100%); border: 1px solid #ff6b6b;">
    <h3 style="color:#ff8a8a">KOL 头部声量 <span class="badge">{fmt_num(kol_card['count'])}篇 · ROI {kol_card['roi']:.2f}</span></h3>
    <p class="sub">单篇成本¥{fmt_num(kol_card['avg_cost'])} · 篇均互动{fmt_num(kol_card['avg_interact'])} · {kol_card['with_gmv_pct']:.0f}%笔记有转化</p>
    <div class="stats">
      <div class="stat-item"><div class="v">{fmt_wan(kol_card['total_cost'])}</div><div class="l">总消耗</div></div>
      <div class="stat-item"><div class="v">{fmt_wan(kol_card['total_gmv'])}</div><div class="l">总GMV</div></div>
      <div class="stat-item"><div class="v">{kol_card['roi']:.2f}x</div><div class="l">整体ROI</div></div>
    </div>
  </div>
</div>
<div class="chart-row" style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:24px 0;">
  <div class="chart-container"><h3>热力图：方向 × 身份 → ROI</h3><div id="heatmap-roi" class="chart-box" style="height:360px"></div></div>
  <div class="chart-container"><h3>桑基图：身份 → 产品 → 方向 → 转化结果</h3><div id="sankey-flow" class="chart-box" style="height:360px"></div></div>
</div>
<div class="conclusion-box">
  <h4>KOL vs KOC 核心结论（全量 786）</h4>
  <ul>
    <li><strong>KOC 仍是效率基本盘</strong>：{fmt_num(koc_card['count'])} 篇贡献 {fmt_wan(koc_card['total_gmv'])} GMV，整体 ROI {koc_card['roi']:.2f}×，单篇成本仅 ¥{fmt_num(koc_card['avg_cost'])}</li>
    <li><strong>KOL 单篇爆发但效率低于 KOC</strong>：{fmt_num(kol_card['count'])} 篇单篇互动 {fmt_num(kol_card['avg_interact'])}，但 ROI {kol_card['roi']:.2f}×，更适合品牌声量与搜索承接</li>
    <li><strong>身份与产品错配</strong>：S1 没有 KOL，G1 集中了全部 {fmt_num(kol_card['count'])} 篇 KOL；建议把 KOL 复制到 S1 纵测/读书日等高 ROI 方向验证</li>
    <li><strong>转化结果差异</strong>：KOC 覆盖 {len(direction_order)} 个方向，KOL 全部集中在 G1横测，结构单一，风险集中</li>
  </ul>
</div>
</div>'''
    h = re.sub(
        r'<!--\s*═══ KOL vs KOC 分类对比（新增） ═══\s*--><div class="section">.*?(?=<div class="section actype-section">)',
        f'<!-- ═══ KOL vs KOC 分类对比（新增） ═══ -->{kol_vs_koc}',
        h, count=1, flags=re.DOTALL)

    # 7) replace account type section
    def actype_card(s):
        tier = 'tier-high' if s['roi'] >= 10 else ('tier-mid' if s['roi'] >= 3 else 'tier-low')
        tag = '⭐头部赛道' if s['roi'] >= 10 else ('⏳腰部可用' if s['roi'] >= 3 else '⚠️ 低效/停投')
        max_roi = actype_stats[0]['roi'] if actype_stats else 1
        bar_w = min(100, int(100 * s['roi'] / max_roi))
        return f'''<div class="actype-card {tier}">
<div class="actype-head"><div class="actype-name">{s['account_type']}</div><div class="actype-tag">{tag}</div></div>
<div class="actype-roi"><span class="big">{s['roi']:.2f}</span><span class="x">×</span><span class="lbl">ROI</span></div>
<div class="actype-bar"><div class="actype-bar-fill" style="width:{bar_w}%"></div></div>
<div class="actype-stats">
  <div><span class="k">篇数</span><span class="v">{fmt_num(s['notes'])}</span></div>
  <div><span class="k">总GMV</span><span class="v">{fmt_wan(s['gmv'])}</span></div>
  <div><span class="k">总消耗</span><span class="v">{fmt_wan(s['cost'])}</span></div>
  <div><span class="k">篇均GMV</span><span class="v">¥{fmt_num(s['gmv_per_note'])}</span></div>
  <div><span class="k">篇均互动</span><span class="v">{fmt_num(s['interact_per_note'])}</span></div>
  <div><span class="k">进店转化</span><span class="v">{s['cvr_shop']:.1f}%</span></div>
</div>
</div>'''

    main_types = [s for s in actype_stats if s['notes'] >= 10]
    small_types = [s for s in actype_stats if s['notes'] < 10]
    top2 = actype_stats[:2]
    bottom2 = actype_stats[-2:]

    top_tables = ''
    for s in main_types:
        top_tables += f'<details class="actype-small"><summary>{s["account_type"]} · Top 5 爆文（按GMV）</summary><table><thead><tr><th>达人昵称</th><th>内容方向</th><th>产品</th><th>GMV</th><th>ROI</th></tr></thead><tbody>'
        for t in actype_top.get(s['account_type'], [])[:5]:
            top_tables += f'<tr><td>{t["达人昵称"]}</td><td>{t["内容方向"]}</td><td>{t["product"]}</td><td>¥{fmt_num(t["gmv"])}</td><td>{t["roi"]:.2f}x</td></tr>'
        top_tables += '</tbody></table></details>'

    actype_section = f'''<div class="section actype-section">
<h2 class="section-title" style="border-left-color:#FFB800">KOC 账号类型效率拆解 <span class="ribbon-new">NEW</span></h2>
<p class="section-sub">按昵称关键词把 {fmt_num(koc_card['count'])} 篇 KOC 分成 {len(actype_stats)} 类账号人设 · 同一品牌同一内容方向，不同账号类型 ROI 拉开 {safe_div(top2[0]['roi'], bottom2[0]['roi']):.1f} 倍以上</p>
<div class="actype-headline">
  <div class="hl-card hl-win">
    <div class="hl-tag">🏆 头部赛道</div>
    <div class="hl-name">{top2[0]['account_type']}</div>
    <div class="hl-val">{top2[0]['roi']:.2f}<span>×</span></div>
    <div class="hl-desc">{fmt_num(top2[0]['notes'])} 篇 · 篇均 GMV ¥{fmt_num(top2[0]['gmv_per_note'])} · CPE ¥{top2[0]['cpe']:.0f} · 进店转化率 {top2[0]['cvr_shop']:.1f}% — 是 KOC 整体 ROI({koc_card['roi']:.2f}×) 的 {safe_div(top2[0]['roi'], koc_card['roi']):.1f} 倍</div>
  </div>
  <div class="hl-card hl-bad">
    <div class="hl-tag">⚠️ 待优化</div>
    <div class="hl-name">{bottom2[-1]['account_type']}</div>
    <div class="hl-val">{bottom2[-1]['roi']:.2f}<span>×</span></div>
    <div class="hl-desc">{fmt_num(bottom2[-1]['notes'])} 篇 · 篇均 GMV ¥{fmt_num(bottom2[-1]['gmv_per_note'])} · 消耗 ¥{fmt_wan(bottom2[-1]['cost'])} — 建议停投或严格限制</div>
  </div>
</div>
<div class="actype-cards">
{''.join(actype_card(s) for s in main_types)}
</div>
<div class="chart-container"><h3>KOC 账号类型 ROI 对比</h3><div id="actype-chart" class="chart-box" style="height:420px"></div></div>
{top_tables}
<div class="conclusion-box">
  <h4>KOC 账号类型核心结论（全量 752 篇 KOC）</h4>
  <ul>
    <li><strong>科技测评 + 生活分享是高 ROI 双引擎</strong>：{top2[0]['account_type']} {fmt_num(top2[0]['notes'])} 篇 ROI {top2[0]['roi']:.2f}×，{top2[1]['account_type']} {fmt_num(top2[1]['notes'])} 篇 ROI {top2[1]['roi']:.2f}×，两类贡献 KOC 总 GMV 的 {safe_div(top2[0]['gmv']+top2[1]['gmv'], koc_card['total_gmv'])*100:.0f}%</li>
    <li><strong>泛人格素人是规模但非效率</strong>：{fmt_num(next((s['notes'] for s in actype_stats if '泛人格' in s['account_type']), 0))} 篇（占基本盘 {safe_div(next((s['notes'] for s in actype_stats if '泛人格' in s['account_type']), 0), koc_card['count'])*100:.0f}%）ROI {next((s['roi'] for s in actype_stats if '泛人格' in s['account_type']), 0):.2f}×，可作为低成本测试但不宜高价</li>
    <li><strong>时尚/美食/亲子/职场等 18 篇几乎零成交</strong>：这些类型与 AI 眼镜品类关联弱，建议停投；若坚持需改为科技/数码垂类账号共创</li>
    <li><strong>选号策略</strong>：主投「数码科技测评 + 生活分享」，辅投「萌宠/美食」做破圈，严控泛人格单价 ≤¥800/篇</li>
  </ul>
</div>
</div>'''
    h = re.sub(
        r'<div class="section actype-section">.*?(?=<div class="testpool-mega">)',
        actype_section,
        h, count=1, flags=re.DOTALL)

    # 8) remove test-pool section + test KISS
    h = re.sub(
        r'<div class="testpool-mega">.*?(?=<div class="section"><h2 class="section-title">综合行动建议</h2>)',
        '',
        h, count=1, flags=re.DOTALL)

    # 9) update actype chart data
    actype_chart_data = [
        {'name': s['account_type'], 'roi': s['roi'], 'gmv_per_note': s['gmv_per_note'], 'notes': s['notes']}
        for s in actype_stats
    ]
    h = re.sub(
        r'(function init_actype_chart\(\)\{[^}]*var data=)\[[^\]]*\];',
        r'\1' + json.dumps(actype_chart_data, ensure_ascii=False, separators=(',', ':')) + ';',
        h, count=1, flags=re.DOTALL)

    # 10) replace panel-mega with chart-centric view
    g1_overall = overall['g1']
    mega_panel = f'''<div class="panel panel-mega" id="panel-mega" data-panel="mega">
<header><h1>全量 786 篇统一视图</h1><p>总预算 ¥95万 · 786 条内容 · KOL {fmt_num(kol_overall['count'])} 条 · KOC {fmt_num(koc_overall['count'])} 条 · S1 {fmt_num(s1['count'])} 条 · G1 {fmt_num(g1_overall['count'])} 条</p></header>
<div class="container">
  <div class="section overview-section">
    <h2 class="section-title" style="border-left-color:#fbbf24">全量 786 篇 · 总览</h2>
    <p class="section-sub">总预算 ¥{fmt_num(BUDGET)} · {fmt_num(total['count'])} 条内容 · 数据截止6.28 · 测试池已并入主池统一口径</p>
    <div class="mega-metrics">
      <div class="mega-card"><div class="mega-label">累计GMV</div><div class="mega-value" style="color:#34d399">{fmt_wan(total['total_gmv'])}<span class="mega-unit">元</span></div></div>
      <div class="mega-card"><div class="mega-label">预算 ROI</div><div class="mega-value" style="color:#fbbf24">{total['budget_roi']:.2f}<span class="mega-unit">×</span></div></div>
      <div class="mega-card"><div class="mega-label">实际消耗</div><div class="mega-value" style="color:#f472b6">{fmt_wan(total['total_cost'])}<span class="mega-unit">元</span></div></div>
      <div class="mega-card"><div class="mega-label">预算执行率</div><div class="mega-value" style="color:#60a5fa">{safe_div(total['total_cost'], BUDGET)*100:.1f}<span class="mega-unit">%</span></div></div>
      <div class="mega-card"><div class="mega-label">累计引流UV</div><div class="mega-value" style="color:#22d3ee">{fmt_num(total['total_store'])}<span class="mega-unit"></span></div></div>
      <div class="mega-card"><div class="mega-label">累计搜索UV</div><div class="mega-value" style="color:#a78bfa">{fmt_num(total['total_search'])}<span class="mega-unit"></span></div></div>
      <div class="mega-card"><div class="mega-label">总互动量</div><div class="mega-value" style="color:#fb923c">{fmt_num(total['total_interact'])}<span class="mega-unit"></span></div></div>
      <div class="mega-card"><div class="mega-label">总阅读量</div><div class="mega-value" style="color:#38bdf8">{fmt_num(total['total_reads'])}<span class="mega-unit"></span></div></div>
    </div>
  </div>

  <div class="section">
    <h2 class="section-title">身份 × 产品双维效率</h2>
    <div class="mega-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:18px;">
      <div class="mega-card"><div class="mega-label">KOC 整体</div><div class="mega-value" style="color:#34d399">{koc_overall['roi']:.2f}<span class="mega-unit">×</span></div><div class="mega-desc">{fmt_num(koc_overall['count'])}篇 · ¥{fmt_num(koc_overall['avg_cost'])}/篇</div></div>
      <div class="mega-card"><div class="mega-label">KOL 整体</div><div class="mega-value" style="color:#fb7185">{kol_overall['roi']:.2f}<span class="mega-unit">×</span></div><div class="mega-desc">{fmt_num(kol_overall['count'])}篇 · ¥{fmt_num(kol_overall['avg_cost'])}/篇</div></div>
      <div class="mega-card"><div class="mega-label">S1 产品线</div><div class="mega-value" style="color:#38bdf8">{s1['roi']:.2f}<span class="mega-unit">×</span></div><div class="mega-desc">{fmt_num(s1['count'])}篇 · 篇均GMV ¥{fmt_num(s1['avg_gmv'])}</div></div>
      <div class="mega-card"><div class="mega-label">G1 产品线</div><div class="mega-value" style="color:#a78bfa">{g1_overall['roi']:.2f}<span class="mega-unit">×</span></div><div class="mega-desc">{fmt_num(g1_overall['count'])}篇 · 篇均GMV ¥{fmt_num(g1_overall['avg_gmv'])}</div></div>
    </div>
  </div>

  <div class="section">
    <h2 class="section-title">内容方向效率总表（按产品线拆分）</h2>
    <p class="section-sub">柱状图=篇数 · 折线=ROI · 气泡大小=GMV规模</p>
    <div class="chart-row" style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:18px 0;">
      <div class="chart-container"><h3>S1 内容方向 ROI & 篇数</h3><div id="mega-dir-s1" class="chart-box" style="height:380px"></div></div>
      <div class="chart-container"><h3>G1 内容方向 ROI & 篇数</h3><div id="mega-dir-g1" class="chart-box" style="height:380px"></div></div>
    </div>
    <div class="chart-container"><h3>方向 × 产品线 ROI 热力图</h3><div id="mega-heatmap" class="chart-box" style="height:420px"></div></div>
    <div class="conclusion-box">
      <h4>内容方向效率结论（全量 786 篇）</h4>
      <ul>
        <li><strong>S1 效率冠军是「纵测」</strong>：6 篇 ROI {s1_dirs[0]['roi']:.2f}×，证明深度对比内容在高客单产品上爆发力最强</li>
        <li><strong>S1 横测与读书日是可规模化的稳定方向</strong>：{s1_dirs[1]['count']} 篇 ROI {s1_dirs[1]['roi']:.2f}×、{s1_dirs[2]['count']} 篇 ROI {s1_dirs[2]['roi']:.2f}×，是 S1 铺量基本盘</li>
        <li><strong>G1 高度依赖横测</strong>：{g1_dirs[0]['count']} 篇横测占 G1 总量 {safe_div(g1_dirs[0]['count'], g1_overall['count'])*100:.0f}%，ROI {g1_dirs[0]['roi']:.2f}×；选购攻略、国补攻略效率偏低，需优化结构</li>
        <li><strong>国补/促销类内容并入后拉低均值</strong>：S1国补攻略 {next((d['count'] for d in s1_dirs if d['内容方向']=='S1国补攻略'),0)} 篇 ROI {next((d['roi'] for d in s1_dirs if d['内容方向']=='S1国补攻略'),0):.2f}×，G1国补攻略 {g1_dirs[2]['count']} 篇 ROI {g1_dirs[2]['roi']:.2f}×，建议统一使用「价格钩子+搜索承接」模板</li>
      </ul>
    </div>
  </div>

  <div class="section">
    <h2 class="section-title">全量 786 篇 KISS 结论</h2>
    <div class="kiss-grid">
      <div class="kiss-card kiss-keep">
        <div class="kiss-title">KEEP</div>
        <div class="kiss-v">KOC 仍是效率基本盘：统一后 {fmt_num(koc_overall['count'])} 篇，实际 ROI {koc_overall['roi']:.2f}×，远高于 KOL {kol_overall['roi']:.2f}×</div>
        <div class="kiss-v">S1 高客单模型成立：{fmt_num(s1['count'])} 篇 ROI {s1['roi']:.2f}×，篇均 GMV ¥{fmt_num(s1['avg_gmv'])}</div>
        <div class="kiss-v">S1纵测、S1读书日借势、G1横测继续规模化复制</div>
      </div>
      <div class="kiss-card kiss-improve">
        <div class="kiss-title">IMPROVE</div>
        <div class="kiss-v">KOL {fmt_num(kol_overall['count'])} 篇全部压在 G1 横测，应扩展到 S1 纵测/读书日等高 ROI 方向</div>
        <div class="kiss-v">节点类内容（520/618/场景对比）沉淀周期短，需提前 2-4 周前置铺设</div>
        <div class="kiss-v">国补/促销类内容统一使用高转化标题公式并强化搜索承接</div>
      </div>
      <div class="kiss-card kiss-stop">
        <div class="kiss-title">STOP</div>
        <div class="kiss-v">S1 明星热点方向继续停投（本次 ROI {next((d['roi'] for d in s1_dirs if d['内容方向']=='S1热点明星'),0):.2f}×）</div>
        <div class="kiss-v">低 ROI 账号类型（时尚颜值/职场财经/文艺学习/家庭亲子）建议停投或改为科技垂类共创</div>
      </div>
      <div class="kiss-card kiss-start">
        <div class="kiss-title">START</div>
        <div class="kiss-v">把高 ROI 方向（纵测/读书日）从 S1 复制到 G1，摆脱 G1 单一横测依赖</div>
        <div class="kiss-v">用 20% 预算做新方向小样本测试，验证后导入 80% KOC 铺量</div>
        <div class="kiss-v">建立「786 篇全量统一周报」口径，每周按预算 95w 更新</div>
      </div>
    </div>
  </div>
</div>
</div>'''
    h = re.sub(
        r'<div class="panel panel-mega" id="panel-mega" data-panel="mega">.*?(?=<div class="panel panel-s1g1")',
        mega_panel,
        h, count=1, flags=re.DOTALL)

    # 11) inject MEGA_DATA + init_mega before INIT
    mega_data_json = json.dumps({
        's1': dir_chart_data(s1_dirs),
        'g1': dir_chart_data(g1_dirs),
        'heatmap_dirs': mega_heatmap_dirs,
        'heatmap_data': mega_heatmap_data,
    }, ensure_ascii=False, separators=(',', ':'))
    init_mega_fn = f'''<script>
const MEGA_DATA = {mega_data_json};
function init_mega(){{
  try{{
    const common = {{backgroundColor:'transparent',tooltip:{{trigger:'axis',axisPointer:{{type:'cross'}}}},legend:{{textStyle:{{color:'#7b8bb2'}},top:0}},grid:{{left:60,right:60,top:40,bottom:80}},xAxis:{{type:'category',axisLabel:{{color:'#b8c5dc',rotate:35,fontSize:11}},axisLine:{{lineStyle:{{color:'#1e2d5a'}}}}}},yAxis:[{{type:'value',name:'篇数',position:'left',axisLabel:{{color:'#7b8bb2'}},splitLine:{{lineStyle:{{color:'#1e2d5a'}}}},nameTextStyle:{{color:'#7b8bb2'}}}},{{type:'value',name:'ROI(×)',position:'right',axisLabel:{{color:'#fbbf24'}},splitLine:{{show:false}},nameTextStyle:{{color:'#fbbf24'}}}}]}};
    function makeBarLine(id, rows, color){{
      const el = document.getElementById(id); if(!el) return;
      const chart = echarts.init(el);
      chart.setOption({{...common,
        xAxis:{{...common.xAxis,data:rows.categories}},
        series:[
          {{name:'篇数',type:'bar',data:rows.count,itemStyle:{{color:color,borderRadius:[4,4,0,0]}},barWidth:18}},
          {{name:'ROI',type:'line',yAxisIndex:1,data:rows.roi,smooth:true,lineStyle:{{color:'#fbbf24',width:3}},itemStyle:{{color:'#fbbf24'}},symbol:'circle',symbolSize:8,label:{{show:true,color:'#fbbf24',formatter:'{{c}}×'}}}}
        ]
      }});
      window.addEventListener('resize',()=>chart.resize());
    }}
    makeBarLine('mega-dir-s1', MEGA_DATA.s1, '#38bdf8');
    makeBarLine('mega-dir-g1', MEGA_DATA.g1, '#a78bfa');

    const hmEl = document.getElementById('mega-heatmap');
    if(hmEl){{
      const hm = echarts.init(hmEl);
      hm.setOption({{
        backgroundColor:'transparent',
        tooltip:{{position:'top',formatter:function(p){{return p.name+'<br/>ROI: '+p.value[2]+'×<br/>篇数: '+p.value[3];}}}},
        grid:{{left:80,right:40,top:20,bottom:120}},
        xAxis:{{type:'category',data:MEGA_DATA.heatmap_dirs,splitArea:{{show:true}},axisLabel:{{color:'#b8c5dc',rotate:35,fontSize:11}}}},
        yAxis:{{type:'category',data:['S1','G1'],splitArea:{{show:true}},axisLabel:{{color:'#b8c5dc',fontSize:13}}}},
        visualMap:{{min:0,max:15,calculable:true,orient:'horizontal',left:'center',bottom:10,inRange:{{color:['#0f172a','#1e3a8a','#0ea5e9','#fbbf24','#f472b6']}},textStyle:{{color:'#7b8bb2'}}}},
        series:[{{name:'ROI',type:'heatmap',data:MEGA_DATA.heatmap_data,label:{{show:true,formatter:function(p){{return p.value[2]+'×';}},color:'#fff',fontSize:11}},emphasis:{{itemStyle:{{shadowBlur:10,shadowColor:'rgba(0,0,0,0.5)'}}}}}}]
      }});
      window.addEventListener('resize',()=>hm.resize());
    }}
  }}catch(e){{console.error('init mega',e);}}
}}
</script>'''
    h = h.replace('</main>', f'{init_mega_fn}</main>')

    # 12) update INIT to include mega, drop promo
    h = re.sub(
        r"const INIT=\{'s1g1':typeof init_s1g1==='function'\?init_s1g1:null,'promo':typeof init_promo==='function'\?init_promo:null,(.*?)\};",
        r"const INIT={'mega':typeof init_mega==='function'?init_mega:null,'s1g1':typeof init_s1g1==='function'?init_s1g1:null,\1};",
        h, count=1)

    # 13) remove nav tabs promo/ruhan
    h = re.sub(r'<button class="tab-btn" data-tab="promo">.*?</button>\s*', '', h, count=1, flags=re.DOTALL)
    h = re.sub(r'<button class="tab-btn" data-tab="ruhan">.*?</button>\s*', '', h, count=1, flags=re.DOTALL)

    # 14) remove panel-promo block by index
    pp_start = h.find('<div class="panel panel-promo" id="panel-promo" data-panel="promo">')
    if pp_start != -1:
        depth = 1; j = pp_start + len('<div class="panel panel-promo" id="panel-promo" data-panel="promo">')
        while j < len(h) and depth > 0:
            if h[j:j+4] == '<div': depth += 1; j += 4; continue
            if h[j:j+6] == '</div>': depth -= 1; j += 6; continue
            j += 1
        h = h[:pp_start] + h[j:].lstrip()

    tgt.write_text(h, encoding='utf-8')
    print(f'✓ panel-mega + init + nav cleanup {tgt.relative_to(ROOT)}')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')


