# 千问AI眼镜 · 小红书决策合集 · 周累计驾驶舱

每周累计千问AI眼镜（S1 / G1）在小红书的种草投放数据分析，按周次归档，支持历史回溯。

## 在线访问

> 启用 GitHub Pages 后访问：`https://<your-user>.github.io/<repo-name>/`

## 目录结构

```
docs/
  index.html                              # 主入口（顶部周次下拉 + iframe 加载本周报告）
  weeks.json                              # 周次元数据（必须维护）
  weeks/
    W1-2026-05-13_to_06-13/
      index.html                          # 该周完整 6 tab 合集（千问S1-G1细分 / 618促单 / 纵测Brief / G1模板 / S1对比 / 决策漏斗）
      raw_data/                           # 该周原始 JSON & CSV
```

## 已有周次

| 周次 | 周期 | 核心指标 | 笔记数 |
|---|---|---|---|
| W1 | 2026.05.13 - 06.13 | KOC ROI 8.18× / KOL ROI 2.75× / S1纵测 114.62× | 632 |

## 新增一期的步骤

1. 收集本周的蒲公英 + 星河 Excel
2. 复制最近一期目录：`cp -r docs/weeks/W1-... docs/weeks/W2-2026-06-14_to_06-20`
3. 重新跑 `build_unified_v2.py`（或后续的 `build_week.py`）输出新的 `index.html`
4. 在 `docs/weeks.json` 的 `weeks` 数组里追加一个新对象（label / period_start / period_end / headline_metrics / notes_count / path）
5. `git add docs/weeks/W2-... docs/weeks.json && git commit -m "feat(w2): add 2026-06-14 to 06-20 weekly report"`
6. `git push origin main` → GitHub Pages 自动更新

## 本地预览

```bash
cd docs && python3 -m http.server 8080
# 浏览器打开 http://localhost:8080
```

> 注意：必须用本地 HTTP server 打开，直接 `file://` 协议会导致 `fetch('weeks.json')` 被 CORS 拦截。
