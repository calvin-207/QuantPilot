# 上游 UI 首次导入门禁

第一个包含 FtShare_fincase UI 的提交必须已经展示 **QuantPilot** 品牌。
严禁导入未修改的上游页面并承诺之后再更换品牌。

1. 固定并记录上游源码的 commit。
2. 替换所有可见的页面标题、Logo、页头、导航、推广横幅和无障碍标签。
3. 移除原厂商的营销链接，但必须如实保留 FtShare 作为实际行情数据供应商的标识。
4. 使用 QuantPilot 本地的浏览器存储键名，并替换带厂商品牌的图标。
5. 复制 ECharts 发行版时保留独立的 ECharts Apache-2.0 NOTICE/LICENSE；对外分发 `etf/` 上游衍生代码时，须按 MIT 要求附上上游原始版权与许可声明。
6. 测试夹具必须清晰标注为模拟数据；不得分发私有的生产行情导出数据或 API Key。
7. 运行 python tools/check_brand.py、npm test、npm run build、pytest，并检查渲染后的 UI。
8. 所有门禁通过之前不得合入上游 UI。

ETF 浏览器 UI 现已导入 `etf/src/`，用户可见的 Logo 与推广入口在首次提交前已完成替换。本文档仍作为后续 UI 变更的验收清单。
