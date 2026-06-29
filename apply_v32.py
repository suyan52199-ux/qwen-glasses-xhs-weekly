#!/usr/bin/env python3
"""
R32: 把 KISS 总结改成直接结论，去掉 agency/泛化表述。
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

MAIN_OLD = '''<div class="section kiss-box kiss-main">
  <div class="kiss-head">
    <span class="kiss-emoji">🎯</span>
    <h2 class="kiss-title">铺量板块 · KISS 总结</h2>
    <span class="kiss-meta">634 篇 · ¥80 万 · 4-6 月</span>
  </div>
  <div class="kiss-grid">
    <div class="kiss-card kiss-keep">
      <div class="kiss-k">✅ Keep（维持）</div>
      <div class="kiss-v">KOC 600 篇 ROI 9.60× · 引流超额 134%</div>
      <div class="kiss-x">是基本盘，下期预算占比从 72% 提到 78-80%</div>
    </div>
    <div class="kiss-card kiss-improve">
      <div class="kiss-k">⚡ Improve（优化）</div>
      <div class="kiss-v">KOL 引流仅 46% · 搜索 UV 成本 ¥69 超上限</div>
      <div class="kiss-x">扩域：从只投 G1 横测 → 拓 S1 纵测 / 读书日</div>
    </div>
    <div class="kiss-card kiss-stop">
      <div class="kiss-k">🛑 Stop（停掉）</div>
      <div class="kiss-v">G1 选购攻略 127 篇 ROI 1.19 · S1 热点明星 0×</div>
      <div class="kiss-x">立即砍量 50%，预算转移到横测+读书日</div>
    </div>
    <div class="kiss-card kiss-start">
      <div class="kiss-k">🚀 Start（启动）</div>
      <div class="kiss-v">数码科技测评 166 篇 ROI 14.9× · 占比 28%</div>
      <div class="kiss-x">建账号白名单，1:1 替换泛人格素人预算到 50%+</div>
    </div>
  </div>
  <div class="kiss-foot">一句话总结：<b>KOC 全面爆发，下期继续放大基本盘；KOL 必须扩域，否则单一方向触顶。</b></div>
</div>'''

MAIN_NEW = '''<div class="section kiss-box kiss-main">
  <div class="kiss-head">
    <span class="kiss-emoji">🎯</span>
    <h2 class="kiss-title">铺量板块 · KISS 总结</h2>
    <span class="kiss-meta">634 篇 · ¥80 万 · 4-6 月</span>
  </div>
  <div class="kiss-grid">
    <div class="kiss-card kiss-keep">
      <div class="kiss-k">✅ Keep（维持）</div>
      <div class="kiss-v">KOC 效率高于 KOL；S1 投产比远高于 G1</div>
      <div class="kiss-x">S1 读书日场景、横测/纵测、用户证言内容继续规模化复制；账号筛选倾向数码和生活类素人</div>
    </div>
    <div class="kiss-card kiss-improve">
      <div class="kiss-k">⚡ Improve（优化）</div>
      <div class="kiss-v">提升 S1 内容占比；G1 投放结构调优</div>
      <div class="kiss-x">千问 S1 与 G1 的预算配比从 G1:S1≈6:4 调整为 3:7，把更多预算集中到 S1 高效方向</div>
    </div>
    <div class="kiss-card kiss-stop">
      <div class="kiss-k">🛑 Stop（停掉）</div>
      <div class="kiss-v">G1 选购攻略 127 篇 ROI 1.19 · S1 热点明星 0×</div>
      <div class="kiss-x">G1 选购攻略立即砍量 50% 以上，S1 明星/泛娱乐场景直接停投</div>
    </div>
    <div class="kiss-card kiss-start">
      <div class="kiss-k">🚀 Start（启动）</div>
      <div class="kiss-v">付费投流占比从 5:5 提到 3:7；标题公式迭代</div>
      <div class="kiss-x">自然内容 vs 付费投流从 5:5 调整为 3:7 加大投流；S1 延续读书日情绪标题，G1 主打耸人听闻否定句式并加测 S1 高效情感场景</div>
    </div>
  </div>
  <div class="kiss-foot">一句话总结：<b>下期把预算和投流向 S1 倾斜，KOC 基本盘继续放大；砍掉 G1 选购攻略和 S1 泛娱乐场景。</b></div>
</div>'''

TEST_OLD = '''<div class="section kiss-box kiss-test">
  <div class="kiss-head">
    <span class="kiss-emoji">🧪</span>
    <h2 class="kiss-title">新内容测试板块 · KISS 总结</h2>
    <span class="kiss-meta">152 篇 · ¥15 万 · 全 KOC · 无 KOL</span>
  </div>
  <div class="kiss-grid">
    <div class="kiss-card kiss-keep">
      <div class="kiss-k">✅ Keep（维持）</div>
      <div class="kiss-v">金咖 72 篇 ROI 6.40× · 搜 UV 成本 ¥30 优于基线</div>
      <div class="kiss-x">下一轮控量 60-80 篇做促销节点（618/双11）复跑</div>
    </div>
    <div class="kiss-card kiss-improve">
      <div class="kiss-k">⚡ Improve（优化）</div>
      <div class="kiss-v">如涵 80 篇 ROI 3.02× · 引流仅 26% · 搜 UV ¥56 超上限 12%</div>
      <div class="kiss-x">复盘选题/达人/挂车 + 单价从 ¥1,250 砍到 ¥800/篇</div>
    </div>
    <div class="kiss-card kiss-stop">
      <div class="kiss-k">🛑 Stop（停掉）</div>
      <div class="kiss-v">如涵 S1 方向 71 篇 ROI 远低于同方向原始 KOC 16.01×</div>
      <div class="kiss-x">如涵下轮限定 G1 横测一个方向，S1 暂停</div>
    </div>
    <div class="kiss-card kiss-start">
      <div class="kiss-k">🚀 Start（启动）</div>
      <div class="kiss-v">CPM 维度未按供应商拆分</div>
      <div class="kiss-x">下期接入聚光后台数据，CPM/CTR/CPE 按供应商拆开核算</div>
    </div>
  </div>
  <div class="kiss-foot">一句话总结：<b>金咖可放行控量复跑；如涵需做内容复盘 + 单价砍半，否则不复投。</b></div>
</div>'''

TEST_NEW = '''<div class="section kiss-box kiss-test">
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

for tgt in TARGETS:
    h = tgt.read_text(encoding='utf-8')
    assert h.count(MAIN_OLD) == 1, f'{tgt}: main KISS block count != 1'
    assert h.count(TEST_OLD) == 1, f'{tgt}: test KISS block count != 1'
    h2 = h.replace(MAIN_OLD, MAIN_NEW).replace(TEST_OLD, TEST_NEW)
    tgt.write_text(h2, encoding='utf-8')
    print(f'✓ {tgt.relative_to(ROOT)}: {len(h)} → {len(h2)} ({len(h2)-len(h):+d}B)')

shutil.copyfile(TARGETS[1], DESKTOP)
print(f'✓ desktop sync: {DESKTOP} ({DESKTOP.stat().st_size}B)')
