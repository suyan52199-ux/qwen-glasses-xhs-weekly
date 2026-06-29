#!/usr/bin/env python3
"""
R33: 重写测试板块 KISS，不再强调金咖/如涵，改为促销 vs 国补回搜两个方向，
突出促销里用户证言、横测、价格促销类表现更好。
TARGETS（硬规则）：docs dark + outputs/KOC铺量内容.html
"""
import shutil
from pathlib import Path

ROOT = Path('/Users/xiemila/.qoderwork/workspace/mq6ecbjzd6kpfcgy')
TARGETS = [
    ROOT / 'docs/weeks/W1-2026-05-13_to_06-13/index.html',
    ROOT / 'outputs/KOC铺量内容.html',
]
DESKTOP = Path('/Users/xiemila/Desktop/KOC铺量内容.html')

OLD = '''<div class="section kiss-box kiss-test">
  <div class="kiss-head">
    <span class="kiss-emoji">🧪</span>
    <h2 class="kiss-title">新内容测试板块 · KISS 总结</h2>
    <span class="kiss-meta">152 篇 · ¥15 万 · 全 KOC · 无 KOL</span>
  </div>
  <div class="kiss-grid">
    <div class="kiss-card kiss-keep">
      <div class="kiss-k">✅ Keep（维持）</div>
      <div class="kiss-v">金咖效率优于如涵；KOC 模式验证成立</div>
      <div class="kiss-x">金咖 72 篇 ROI 6.40×、搜 UV 成本 ¥30，继续控量 60-80 篇做促销节点复跑</div>
    </div>
    <div class="kiss-card kiss-improve">
      <div class="kiss-k">⚡ Improve（优化）</div>
      <div class="kiss-v">测试池内 S1 占比偏低，G1 占比过高</div>
      <div class="kiss-x">测试池 S1:G1 配比从当前 ≈6:4 拉到 3:7，把预算向 S1 横测/读书日/纵测方向集中</div>
    </div>
    <div class="kiss-card kiss-stop">
      <div class="kiss-k">🛑 Stop（停掉）</div>
      <div class="kiss-v">如涵 S1 方向 71 篇 ROI 远低于同方向原始 KOC 16.01×</div>
      <div class="kiss-x">如涵 S1 内容暂停；如涵整体单价从 ¥1,250 砍到 ¥800/篇 之前不复投</div>
    </div>
    <div class="kiss-card kiss-start">
      <div class="kiss-k">🚀 Start（启动）</div>
      <div class="kiss-v">标题公式做 A/B，账号池收紧</div>
      <div class="kiss-x">S1 沿用情绪类标题并放大读书日白条，G1 主打耸人听闻否定句式；如涵/金咖统一只选数码+生活类素人账号</div>
    </div>
  </div>
  <div class="kiss-foot">一句话总结：<b>金咖控量复跑；如涵整体复盘+降价，S1 内容先停；测试池同样把 S1 配比拉到 7 成。</b></div>
</div>'''

NEW = '''<div class="section kiss-box kiss-test">
  <div class="kiss-head">
    <span class="kiss-emoji">🧪</span>
    <h2 class="kiss-title">新内容测试板块 · KISS 总结</h2>
    <span class="kiss-meta">152 篇 · ¥15 万 · 全 KOC · 无 KOL</span>
  </div>
  <div class="kiss-grid">
    <div class="kiss-card kiss-keep">
      <div class="kiss-k">✅ Keep（维持）</div>
      <div class="kiss-v">促销方向：用户证言、横测、价格促销类表现更好</div>
      <div class="kiss-x">把这三种内容形态做成 618/双11 促销节点标准模板，优先复刻到下一轮</div>
    </div>
    <div class="kiss-card kiss-improve">
      <div class="kiss-k">⚡ Improve（优化）</div>
      <div class="kiss-v">国补回搜方向：搜索承接不足，转化弱于促销方向</div>
      <div class="kiss-x">把促销验证过的用户证言+横测+价格促销结构迁移到国补场景，补搜索进店承接和 CTA 组件</div>
    </div>
    <div class="kiss-card kiss-stop">
      <div class="kiss-k">🛑 Stop（停掉）</div>
      <div class="kiss-v">低转化内容：纯场景种草、无 CTA 软广、曝光高但搜索进店为 0 的笔记</div>
      <div class="kiss-x">测试池不再买单纯曝光型内容，只保留带明确搜索/进店引导的笔记</div>
    </div>
    <div class="kiss-card kiss-start">
      <div class="kiss-k">🚀 Start（启动）</div>
      <div class="kiss-v">促销 + 国补双方向 A/B，标题公式固定</div>
      <div class="kiss-x">促销侧：放大「用户证言｜横测｜价格促销」；国补侧：主打「国补叠加+价格促销」钩子；统一账号只选数码+生活类素人</div>
    </div>
  </div>
  <div class="kiss-foot">一句话总结：<b>促销方向继续放大用户证言、横测、价格促销三类内容；国补方向复制同一结构并补强搜索承接；砍掉纯曝光型测试。</b></div>
</div>'''

for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')
    assert h.count(OLD) == 1, f'{tgt}: test KISS block count != 1'
    h2 = h.replace(OLD, NEW)
    tgt.write_text(h2, encoding='utf-8')
    print(f'✓ {tgt.relative_to(ROOT)}: {len(h)} → {len(h2)} ({len(h2)-len(h):+d}B)')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')
