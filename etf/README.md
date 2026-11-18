# QuantPilot · ETF 资金观察子系统

本目录是从 [FtShare_fincase](https://github.com/FTShare-Lab/FtShare_fincase) 迁移而来的 ETF 资金与成交观察模块。原作者 MIT 版权及许可文本保留在本目录 [LICENSE](LICENSE)；ECharts 的 Apache-2.0 授权见 [third_party/echarts](third_party/echarts)。

**品牌**：页面标题、Logo、推广入口已替换为 QuantPilot。实际行情供应商若为 FtShare，数据来源说明应真实显示 FtShare，不属于产品品牌推广。

## 功能

- ETF 成交异动雷达（20/60 日同进度成交比较）
- 核心 ETF、宽基类别行情与资金净申赎估算
- 分钟成交、历史资金、自动采集及缓存
- 演示模式使用程序生成的模拟数据；真实模式需合法 API 凭证与历史快照

## 本地运行

要求 Node.js 24+。

```bash
cd etf
npm ci
npm run build
npm test
npm start
```

访问 http://127.0.0.1:8080 。启用演示异动雷达时设置 `ENABLE_RADAR=1` 后重新运行构建。

**注意**：首次迁移仍需以自动测试、构建产物及真实浏览器视图确认，不应将未核验的行情数据视为真实市场结果。

相关文档见 `docs/data.md`、`docs/deployment.md` 及仓库根目录 `docs/UPSTREAM.md`。
